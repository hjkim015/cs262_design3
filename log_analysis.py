import re
import logging
import os
import sys
import yaml

# Load the log file
def load_log_file(log_file):
    with open(log_file, "r") as f:
        lines = f.readlines()

    # Return list of log entries
    return lines

# Parse the log file
def parse_machine_log(machine_log):
    pass

if __name__ == "__main__":
    # Load log files
    for i in range(3):
        log_file = f"logs/log_machine_{i}.txt"
        load_log_file(log_file)