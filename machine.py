import grpc
from concurrent import futures
import multiprocessing
import random
import time
import system_pb2
from concurrent.futures import ThreadPoolExecutor
import system_pb2_grpc
import logging
from queue import Queue
import queue
import threading
import os
from google.protobuf import empty_pb2
import sys

class Machine(system_pb2_grpc.PeerServiceServicer):
    def __init__(self, machine_id, port, clock_rate, peers, peers_id, log_path=None):
        """Initialize the machine."""
        # Initialize the logical clock
        self.logical_clock = 0
        self.clock_rate = clock_rate
        self.cycle_time = 1 / clock_rate
        
        # Initialize the machine ID, peer addresses, and message queue
        self.machine_id = machine_id
        self.peers = peers # list of peer addresses
        self.peers_id = peers_id
        self.port = port
        self._channels = [] # list of channels to peers
        self._stubs = [] # list of stubs to peers
        self._receive_threads = [] # list of threads for receiving from peers
        self.message_queue = Queue()
        self._stop_event = threading.Event()
        
        self.running = False
        self.last_sent_message = None

        # Initialize the logger
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        self.logger = logging.getLogger(f"{log_path}/machine_{machine_id}")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(f"{log_path}/machine_{machine_id}.log", mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        self.logger.addHandler(handler)   
        # Write first log message
        self.logger.info(f"[INIT] with clock rate {self.clock_rate} and peers {self.peers}, {self.peers_id}") 

    def SendMessage(self, request, context):
        """Receive a message (unary) from a peer and enqueue it."""
        self.message_queue.put(request)
        return empty_pb2.Empty()
    
    def ReceiveMessages(self, request, context):
        """Stream messages to a peer from this machine's queue."""
        while not self._stop_event.is_set():
            try:
                if self.last_sent_message is not None:
                    msg = self.last_sent_message
                    self.last_sent_message = None
                    yield msg
            except queue.Empty:
                pass

    def _start_server(self):
        """Start the gRPC server in a separate thread"""
        self.server = grpc.server(ThreadPoolExecutor(max_workers=10))
        system_pb2_grpc.add_PeerServiceServicer_to_server(self, self.server)
        self.server.add_insecure_port(f"[::]:{self.port}")
        self.server.start()

        # Connect to peers & start streaming from them
        for p in self.peers:
            channel = grpc.insecure_channel(f'{p}')
            stub = system_pb2_grpc.PeerServiceStub(channel)
            self._channels.append(channel)
            self._stubs.append(stub)

            t = threading.Thread(target=self._receive_from_peer, args=(stub,))
            t.start()
            self._receive_threads.append(t)
        
        # Give time for all machines to start up
        time.sleep(2)

        self.running = True

    def run(self, p_a, p_b, p_c):
        """Main loop for processing messages and events
        p_a: probability threshold for sending msg to machine A
        p_b: probability threshold for sending msg to machine B
        p_c: probability threshold for sending msg to both machines
        above t3: internal event
        """

        self._start_server()

        while self.running:
            # Bookkeeping
            start = time.time()

            # Check for incoming messages
            if not self.message_queue.empty():
                message = self.message_queue.get() 

                # Update clock according to Lamport
                self.logical_clock = max(self.logical_clock, message.logical_clock) + 1

                # Get queue length
                queue_length = self.message_queue.qsize()

                # Log the message
                self.logger.info(f"[RECEIVED] from Machine {message.sender_id}, Logical clock: {self.logical_clock}, Queue length: {queue_length}")
            # Generate random action
            else:
                # TODO: modify for >3 peers, change threshold names
                action = random.randint(1, 10)
                if action < p_a:
                    self._send_message(0)
                    self.logical_clock += 1
                elif action < p_b:
                    self._send_message(1)
                    self.logical_clock += 1
                elif action < p_c: 
                    for i in range(len(self.peers)):
                        self._send_message(i)
                    self.logical_clock += 1
                # Trigger an internal event
                else:
                    self.logical_clock += 1
                    self.logger.info(f"[INTERNAL], Logical clock: {self.logical_clock}")

            # Bookkeeping
            end = time.time()
            time.sleep(max(0,self.cycle_time - (end - start)))

    def _send_message(self, target):
        """Send a message to peer via unary calls."""
        try:
            stub = self._stubs[target]
            msg = system_pb2.Message(sender_id=self.machine_id, logical_clock=self.logical_clock)
            stub.SendMessage(msg)
            self.logger.info(f"[SENT] to Machine {self.peers_id[target]}, Logical clock: {self.logical_clock}")
            self.last_sent_message = msg
        except grpc.RpcError as e:
            self.logger.error(f"{e}")

    def _receive_from_peer(self, stub):
        """Keep reading messages from a peer's stream and enqueue them."""
        try:
            for msg in stub.ReceiveMessages(empty_pb2.Empty()):
                self.message_queue.put(msg)
                if self._stop_event.is_set():
                    break
        except grpc.RpcError:
            pass  # Peer might be down or closed
        
    def stop(self):
        """Signal stop, close channels, and end run loop."""
        self.running = False
        self._stop_event.set()
        for ch in self._channels:
            ch.close()

