import grpc
import random
import time
import system_pb2
from concurrent.futures import ThreadPoolExecutor
import system_pb2_grpc
import logging
from queue import Queue
import queue
import threading
import socket
import os
from google.protobuf import empty_pb2
from multiprocessing import Queue
import multiprocessing
import json

class Message:
    """Class to represent a message sent between machines."""
    def __init__(self, sender_id, logical_clock):
        self.sender_id = sender_id
        self.logical_clock = logical_clock

    def to_json(self):
        # Convert the message to a JSON string
        return json.dumps(self.__dict__)

    @staticmethod
    def from_json(json_string):
        # Create a message object from a JSON string
        data = json.loads(json_string)
        return Message(data["sender_id"], data["logical_clock"])

class Machine(system_pb2_grpc.PeerServiceServicer):
    def __init__(self, machine_id: int, host: str, port: int, clock_rate: int, peers: list, peers_id: list, log_path=None):
        """Initialize the machine."""

        # Initialize the logical clock
        self.logical_clock = 0
        self.clock_rate = clock_rate
        self.cycle_time = 1 / clock_rate
        
        # Initialize the sockets and message queue
        self.machine_id = machine_id
        self.peers = peers # list of peer addresses: [50051, 50052]
        self.peers_id = peers_id # list of peer ids: [0, 1]
        self.host = host
        self.port = port
        # Necessary to avoid Unix .qsize bug
        m = multiprocessing.Manager()
        self.message_queue = m.Queue()
        
        # Flag to indicate if the machine is running
        self.running = multiprocessing.Value('b', False)

        self.log_path = log_path
        
        # Set up server to listen for messages
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.server.listen()

    def _start_server(self):
        """Start the server in a separate thread"""
        
        # Start listener thread for incoming connections
        listener_thread = threading.Thread(target=self._receive_messages, daemon=True)
        listener_thread.start()
        
        # Give time for all machines to start up
        time.sleep(2)

        # Set the running flag
        self.running = True

        # Initialize the logger
        log_path = self.log_path
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        self.logger = logging.getLogger(f"{log_path}/machine_{self.machine_id}")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(f"{log_path}/machine_{self.machine_id}.log", mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        self.logger.addHandler(handler)   
        # Write first log message
        self.logger.info(f"[INIT] with clock rate {self.clock_rate} and peers {self.peers}, {self.peers_id}") 


    def run(self, p_a, p_b, p_c):
        """Main loop for processing messages and events
        p_a: probability threshold for sending msg to machine A
        p_b: probability threshold for sending msg to machine B
        p_c: probability threshold for sending msg to both machines
        above p_c: internal event
        """

        # Start the server and connect to peers
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
                # TODO: modify for >3 peers
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
            
    def _receive_messages(self):
        """Listen for incoming connections from other machines"""
        while self.running:
            try:
                peer, _ = self.server.accept()
                listening_thread = threading.Thread(target=self._service_socket, args=(peer,), daemon=True)
                listening_thread.start()
            except Exception as e:
                self.logger.error(f"Error accepting connection from peer {peer}: {e}")

    def _service_socket(self, peer):
            """Handle messages coming an existing connection"""
            try:
                data = peer.recv(1024)
            
                # Deserialize the message and put on queue
                msg = Message.from_json(data.decode())
                self.message_queue.put(msg)
            except Exception as e:
                self.logger.error(f"Error servicing connection from peer {peer}: {e}")
            finally:
                peer.close()

    def _send_message(self, target):
        """Send a message to peer"""

        peer = None
        try:
            # Create message
            msg = Message(self.machine_id, self.logical_clock)
            peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer.connect((self.host, self.peers[target]))
            peer.sendall(msg.to_json().encode())
        except Exception as e:
            self.logger.error(f"Error sending message to port {target}: {e}")
        finally:
            self.logger.info(f"[SENT] to Machine {self.peers_id[target]}, Logical clock: {self.logical_clock}")

            if peer:
                peer.close()

        
    def stop(self):
        """Signal stop, close channels, and end run loop."""
        self.running = False
        self.server.close()