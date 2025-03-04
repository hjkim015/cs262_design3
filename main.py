import multiprocessing
import time
import random
from machine import Machine
import yaml

# Load config
with open("experiment_config.yaml", "r") as f:
    config = yaml.safe_load(f)
    PROB_MSG_A = config["PROB_MSG_A"]
    PROB_MSG_B = config["PROB_MSG_B"]
    PROB_MSG_C = config["PROB_MSG_C"]
    N_MACHINES = config["N_MACHINES"]
    N_TRIALS = config["N_TRIALS"]
    DURATION = config["DURATION"]
    CYCLE_MAX = config["CYCLE_MAX"]
    BASE_PORT = config["BASE_PORT"]

def start_peer(machine_id, port, clock_rate, peer_addresses):
    machine = Machine(machine_id, clock_rate, peer_addresses)
    machine.run(port, PROB_MSG_A, PROB_MSG_B, PROB_MSG_C)

if __name__ == "__main__":
    peer_addresses = [f"localhost:{BASE_PORT + i}" for i in range(N_MACHINES)]

    for _ in range(N_TRIALS):
    # TODO: kill at 60 seconds
    # TODO: create new logging folder for each run

        processes = []
        for i in range(N_MACHINES):
            clock_rate = random.randint(1, CYCLE_MAX)  # Random clock ticks per second
            p = multiprocessing.Process(target=start_peer, args=(i, BASE_PORT + i, clock_rate, peer_addresses))
            processes.append(p)
            p.start()

        for p in processes:
            p.join()