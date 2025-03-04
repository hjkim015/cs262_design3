import multiprocessing
import time
import random
from machine import Machine
import yaml
import threading
import os

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


if __name__ == "__main__":
    for trial in range(N_TRIALS):
        # Create a unique logging folder for each run
        log_folder = f"logs/run_{int(time.time())}"
        os.makedirs(log_folder, exist_ok=True)

        ports = [f"localhost:{BASE_PORT + i}" for i in range(N_MACHINES)]
        machines = []

        for i in range(N_MACHINES):
            my_port = BASE_PORT + i
            clock_rate = random.randint(1, CYCLE_MAX)  # Random clock ticks per second
            # TODO rm self from peer addresses, make peers just int not localhost etc
            peers = []
            for j in range(N_MACHINES):
                if j != i:
                    peers.append(f"localhost:{BASE_PORT + j}")
            m = Machine(i, my_port, clock_rate, peers, log_path=log_folder)
            machines.append(m)

        threads = []
        for m in machines:
            t = threading.Thread(target=m.run, args=(PROB_MSG_A,PROB_MSG_B,PROB_MSG_C),daemon=True)
            t.start()
            threads.append(t)

        # Allow threads to run for RUN_DURATION seconds
        time.sleep(DURATION)

        # Stop all machines
        for m in machines:
            m.stop()

        # Wait for them to shut down
        for t in threads:
            t.join()

    print("All machines have stopped.")