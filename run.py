import multiprocessing
import time
import random
from machine import Machine

def start_peer(machine_id, port, clock_rate, peer_addresses):
    machine = Machine(machine_id, clock_rate, peer_addresses)
    machine.run(port)

if __name__ == "__main__":
    num_machines = 3
    base_port = 50050
    peer_addresses = [f"localhost:{base_port + i}" for i in range(num_machines)]
    
    processes = []
    for i in range(num_machines):
        clock_rate = random.randint(1, 6)  # Random clock ticks per second
        p = multiprocessing.Process(target=start_peer, args=(i, base_port + i, clock_rate, peer_addresses))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()
