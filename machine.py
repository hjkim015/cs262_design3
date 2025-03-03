import grpc
from concurrent import futures
import multiprocessing
import random
import time
import system_pb2
import system_pb2_grpc
from queue import Queue
from datetime import datetime

class Machine(system_pb2_grpc.PeerServiceServicer):
    def __init__(self, machine_id, clock_rate, peers):
        self.machine_id = machine_id
        self.logical_clock = 0
        self.clock_rate = clock_rate  # Clock ticks per second
        self.peers = peers  # List of peer addresses
        self.log_file = f"logs/log_machine_{machine_id}.txt"
        self.queue = Queue()

    def receive_message(self, request, context):
        """Handle incoming messages."""
        self.logical_clock = max(self.logical_clock, request.logical_clock) + 1
        now = datetime.now()

        with open(self.log_file, "a") as f:
            f.write(f"[RECEIVED] Clock: {self.logical_clock} | From: {request.sender_id} | Global Time: {now} | Queue Length: {len(self.queue)}\n")
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
            time.sleep(1 / self.clock_rate)  # Simulate clock speed
            self.logical_clock += 1  # Internal event

            message = self.queue.pop(0)
            
            if message:
                now = datetime.now()
                with open(self.log_file, "a") as f:
                    f.write(f"[RECEIVED] Clock: {self.logical_clock} | Global Time: {now} | Queue Length: {len(self.queue)}\n")
            else:
                action = random.randint(1, 10)
                if action < t1:
                    self.send_message(self.peers[1])
                elif action < t2:
                    self.send_message(self.peers[2])
                elif action < t3: 
                    pass
                else:
                    #Trigger an internal event 
                    with open(self.log_file, "a") as f:
                        f.write(f"[INTERNAL EVENT] Clock: {self.logical_clock} | Global Time: {now}\n")

    def send_message(self, target):
        """Send a message to another machine."""
        with grpc.insecure_channel(target) as channel:
            stub = system_pb2_grpc.PeerServiceStub(channel)
            stub.receive_message(system_pb2.Message(logical_clock=self.logical_clock, sender_id=str(self.machine_id)))

        with open(self.log_file, "a") as f:
            f.write(f"[SENT] Clock: {self.logical_clock} | To: {target}\n")

