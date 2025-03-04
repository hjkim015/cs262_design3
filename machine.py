import grpc
from concurrent import futures
import multiprocessing
import random
import time
import system_pb2
import system_pb2_grpc
import logging
from queue import Queue
import os
import sys

class Machine(system_pb2_grpc.PeerServiceServicer):
    def __init__(self, machine_id, clock_rate, peers, log_path=None):
        """Initialize the machine."""
        # Initialize the logical clock
        self.logical_clock = 0
        self.clock_rate = clock_rate
        self.cycle_time = 1 / clock_rate
        
        # Initialize the machine ID, peer addresses, and message queue
        self.machine_id = machine_id
        self.peers = peers # list of peer addresses
        self.message_queue = Queue()

        # Initialize the logger
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        self.logger = logging.getLogger(f"machine_{machine_id}")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(self.logger, mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        self.logger.addHandler(handler)   
        # Write first log message
        self.logger.info(f"[INIT] with clock rate {self.clock_rate} and peers {self.peers}")    

    def _receive_message(self, request, context):
        """Listen for incoming messages"""
        # self.logical_clock = max(self.logical_clock, request.logical_clock) + 1

        # with open(self.log_file, "a") as f:
        #     f.write(f"[RECEIVED] Clock: {self.logical_clock} | From: {request.sender_id} | Global Time: {now} | Queue Length: {len(self.queue)}\n")
        return system_pb2.Response(success=True)

    def start_server(self, port):
        """Start the gRPC server."""
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        system_pb2_grpc.add_PeerServiceServicer_to_server(self, server)
        server.add_insecure_port(f"[::]:{port}")
        server.start()
        server.wait_for_termination()

    def run(self, port, t1, t2, t3):
        """Main loop for processing messages and events
        t1: probability threshold for sending msg to machine A
        t2: probability threshold for sending msg to machine B
        t3: probability threshold for sending msg to both machines
        above t3: internal event
        """
        process = multiprocessing.Process(target=self.start_server, args=(port,))
        process.start()

        while True:
            # Bookkeeping
            start = time.time()

            # Check for incoming messages
            message = 0
            # message = self.queue.get()            
            if message:
                
                # Update clock according to Lamport
                self.logical_clock = max(self.logical_clock, message.logical_clock) + 1

                # Get queue length
                queue_length = self.message_queue.qsize()

                # Log the message
                self.logger.info(f"[RECEIVED] from Machine {message.sender_id}, Logical clock: {message.logical_clock}, Queue length: {queue_length}")
            # Generate random action
            else:
                # TODO: modify for >3 peers, change threshold names
                action = random.randint(1, 10)
                if action < t1:
                    self._send_message(self.peers[0])
                    self.logical_clock += 1
                elif action < t2:
                    self._send_message(self.peers[1])
                    self.logical_clock += 1
                elif action < t3: 
                    for i in self.peers:
                        self._send_message(i)
                    self.logical_clock += 1
                # Trigger an internal event
                else:
                    self.logical_clock += 1
                    self.logger.info(f"[INTERNAL], Logical clock: {message.logical_clock}")

            # Bookkeeping
            end = time.time()
            time.sleep(self.cycle_time - (end - start))

    def send_message(self, target):
        """Send a message to another machine."""
        with grpc.insecure_channel(target) as channel:
            stub = system_pb2_grpc.PeerServiceStub(channel)
            stub.receive_message(system_pb2.Message(logical_clock=self.logical_clock, sender_id=str(self.machine_id)))

            self.logger.info(f"[SENT] to Machine {target}, Logical clock: {self.logical_clock}")

