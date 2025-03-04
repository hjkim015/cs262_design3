import re
import logging
import os
import sys
import yaml
import json
import pandas as pd

TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")

# Load the log file
def load_log_file(log_file):
    """Load the log file and return the log entries."""
    with open(log_file, "r") as f:
        lines = f.readlines()

    # Return list of log entries
    return lines

def get_clock_rate(init_line):
    """Get the clock rate from the initialization line."""
    cr = re.search(r"with clock rate (\d+)", init_line)
    return cr

def parse_machine_log(lines):
    """Parse machine log into a dataframe"""
    # Initialize the list of rows
    row_list = []
    
    # Parse each line
    for l in lines:

        # Get values
        timestamp = TIMESTAMP_PATTERN.search(l).group(0)
        operation = re.search(r"\[(\w+)\]", l).group(1)
        logical_clock = int(re.search(r"Logical clock: (\d+)", l).group(1))
        queue_length = 0
        if operation == "RECEIVED":
            queue_length = int(re.search(r"Queue length: (\d+)", l).group(1))
    
        # Append to the list of rows
        row_list.append([timestamp,operation,logical_clock,queue_length])
    
    # Create a dataframe
    df = pd.DataFrame(row_list)
    # Give df column names in place
    df.columns = ["timestamp", "operation", "logical_clock", "queue_length"]
    return df

def main(log_path):

    # Load log files
    m0_logs = load_log_file(f"{log_path}/machine_0.log")
    m1_logs = load_log_file(f"{log_path}/machine_1.log")
    m2_logs = load_log_file(f"{log_path}/machine_2.log")

    # Get clock rate for each machine
    cr0 = get_clock_rate(m0_logs.pop(0))
    cr1 = get_clock_rate(m1_logs.pop(0))
    cr2 = get_clock_rate(m2_logs.pop(0))
    
    # Save clock rates to json for legibility
    clock_rates = {"machine_0": int(cr0.group(1)),
                   "machine_1": int(cr1.group(1)),
                   "machine_2": int(cr2.group(1))}
    with open(f"{log_path}/clock_rates.json", "w") as f:
        json.dump(clock_rates, f)

    # Create tabular datasets for each machine and save to csv
    df0 = parse_machine_log(m0_logs)
    df1 = parse_machine_log(m1_logs)
    df2 = parse_machine_log(m2_logs)
    df0.to_csv(f"{log_path}/machine_0.csv", index=False)
    df1.to_csv(f"{log_path}/machine_1.csv", index=False)
    df2.to_csv(f"{log_path}/machine_2.csv", index=False)

if __name__ == "__main__":
    # Get CLI args
    if len(sys.argv) > 1:
        log_path = sys.argv[1]
    else:
        print("Please provide the log path.")
        sys.exit(1)

    main(log_path)
    print("Log parsing complete.")

    # # Log path
    # log_path = "logs/run_1741065634"
