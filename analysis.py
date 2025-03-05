import matplotlib.pyplot as plt
import numpy as np 
import pandas as pd
import os
import json

def preprocess(df):
    """Convert timestamp to datetime and round logical clock values."""
    # 1) Convert timestamp from object to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    # drop any invalid timestamps
    df = df.dropna(subset=["timestamp"])
    # round or clean up if desired
    df["logical_clock"] = df["logical_clock"].round(4)
    return df

def plot_raw(dataframes, experiment_path, experiment_config):
    """Plot the raw logical clock values for each machine."""
    plt.figure(figsize=(12, 6))

    colors = ['blue', 'red', 'green']

    for i, df in enumerate(dataframes):
        # Get machine clock rate
        cr = experiment_config[f'machine_{i}']

        # Skip if the required columns are missing
        if "timestamp" not in df.columns or "logical_clock" not in df.columns:
            print(f"Skipping {experiment} (Missing required columns in {csv_files[i]})")
            continue

        # Sort by timestamp and group by timestamp
        df = df.sort_values("timestamp")  
        df = df.groupby("timestamp", as_index=False, sort=True)["logical_clock"].mean()  # handle duplicate x-values
        df["logical_clock"] = df["logical_clock"].round(4)

        # Plot the logical clock values
        plt.plot(df["timestamp"], df["logical_clock"], label=f"Machine {i}: Clock Rate {cr}", color=colors[i])  
    
    plt.title(f"{experiment}: Raw Logical Clock Values")
    plt.xlabel("Timestamp")
    plt.ylabel("Logical Clock Value")
    plt.xticks(rotation=90)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    # Save the plot
    plt.savefig(os.path.join(experiment_path, "plot_raw_clock.png"))
    plt.close()

def plot_jumps(dataframes, experiment_path, experiment_config):
    '''Plots the clock jumps between instructions per machine'''

    plt.figure(figsize=(12, 6))

    colors = ['blue', 'red', 'green']

    for i, df in enumerate(dataframes):
        # Get machine clock rate
        cr = experiment_config[f'machine_{i}']

        # Skip if the required columns are missing
        if "timestamp" not in df.columns or "logical_clock" not in df.columns:
            print(f"Skipping {experiment} (Missing required columns in {csv_files[i]})")
            continue

        # print("dataframe before:", df)
        df = df.sort_values("timestamp")  
        df["jumps"] = df["logical_clock"].diff()
        mean_jumps = df.groupby("timestamp", as_index=False, sort=True)["jumps"].mean()  # handle duplicate x-value
   

        # Plot the logical clock values
        plt.plot(mean_jumps["timestamp"], mean_jumps["jumps"], label=f"Machine {i}: Clock Rate {cr}", color=colors[i])  
        
        plt.title(f"{experiment}: Logical Clock Value Jump Averages / Second")
        plt.xlabel("Timestamp")
        plt.ylabel("Jump Average")
        plt.xticks(rotation=90)
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        # Save the plot
        plt.savefig(os.path.join(experiment_path, f"plot_jumps_{i}.png"))
        plt.close()


def plot_queue_length(dataframes, experiment_path, experiment_config):
    """Plot the queue length for each machine."""
    plt.figure(figsize=(10,6))

    for i, df in enumerate(dataframes):
        # Get machine clock rate
        cr = experiment_config[f'machine_{i}']

        colors = ['blue', 'red', 'green']
        plt.plot(df['timestamp'], df['queue_length'], label=f'Machine {i}: Clock Rate {cr}', color=colors[i])

    plt.xlabel('Timestamp')
    plt.ylabel('Queue Length')
    plt.title('Queue Length for Each Machine')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(experiment_path, "plot_queue_length.png"))
    plt.close()

def plot_operations(dataframes, experiment_path, experiment_config):
    '''Prints a histogram of the number of Operation occurrences'''

    plt.figure(figsize=(10,6))

    for i, df in enumerate(dataframes):
        #Createa a new dataframe 
        cr = experiment_config[f'machine_{i}']

        colors = ['blue', 'red', 'green']

        operation_counts = df['operation'].value_counts().sort_index()

        # Use bar plot to stack different machines on top of each other
        plt.bar(operation_counts.index, operation_counts.values, 
                color=colors[i], label=f'Machine {i}')
        # plt.bar(df['operation'].value_counts())

    plt.xlabel('Operation')
    plt.ylabel('Count')
    plt.title('Operation Count per Machine')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(experiment_path, "plot_op_count.png"))
    plt.close()


if __name__ == "__main__":
    """Main function to analyze the logs."""
    logs_directory = f"{os.getcwd()}/logs"
 
    for experiment in os.listdir(logs_directory):
        # input("EXPERIMENT")
        experiment_path = os.path.join(logs_directory, experiment)
        
        # Skip if not a directory
        if not os.path.isdir(experiment_path):
            continue  

        # Find the experiment configs
        experiment_config_path = os.path.join(experiment_path, "clock_rates.json")
        if not os.path.exists(experiment_config_path):
            print(f"Skipping {experiment} (Missing experiment config)")
            continue
        with open(experiment_config_path, "r") as f:
            experiment_config = json.load(f)

        # Find the CSV files in the experiment directory
        csv_files = [f for f in os.listdir(experiment_path) if f.endswith(".csv")]
        # Order by machine number
        csv_files = sorted(csv_files, key=lambda x: x[-5])
        
        if len(csv_files) != 3:
            print(f"Skipping {experiment} (Expected 3 CSV files, found {len(csv_files)})")
            continue

        # Read each CSV file (modify column names as needed)
        dataframes = [pd.read_csv(os.path.join(experiment_path, csv)) for csv in csv_files]
        print(csv_files)

        # Preprocess the dataframes
        dataframes = [preprocess(df) for df in dataframes]

        # plot_raw(dataframes, experiment_path, experiment_config)
        # plot_queue_length(dataframes, experiment_path, experiment_config)
        # plot_operations(dataframes, experiment_path, experiment_config)
        plot_jumps(dataframes, experiment_path, experiment_config)



