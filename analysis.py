import matplotlib.pyplot as plt
import numpy as np 
import pandas as pd
import os


def plot_raw(dataframes, experiment_path):
    plt.figure(figsize=(12, 6))

    for i, df in enumerate(dataframes):
        if "timestamp" not in df.columns or "logical_clock" not in df.columns:
            print(f"Skipping {experiment} (Missing required columns in {csv_files[i]})")
            continue

        df = df.sort_values("timestamp")  
        df = df.groupby("timestamp", as_index=False)["logical_clock"].mean()  # Handle duplicate x-values
        df["logical_clock"] = df["logical_clock"].round(4)
        colors = ['blue', 'red', 'green']


        plt.plot(df["timestamp"], df["logical_clock"], label=f"Machine {i+1}", color=colors[i])  
    
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

    print(f"Plot saved for {experiment}, dataframe {i}")

def plot_jumps(dataframes, experiment_path):

    plt.figure(figsize=(20, 6))

    for i, df in enumerate(dataframes):
        # Calculate the jumps in logical clock values for each machine
        df['logical_clock_jump'] = df['logical_clock'].diff()
        colors = ['blue', 'red', 'green']
        plt.bar(df['timestamp'], df['logical_clock_jump'], label=f'Machine {i + 1}', color=colors[i])

    plt.xlabel('Timestamp')
    plt.ylabel('Logical Clock Jump')
    plt.title('Jumps in Logical Clock Values for Each Machine')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(experiment_path, "plot_clock_jumps.png"))
    plt.close()


def plot_queue_length(dataframes, experiment_path):
    plt.figure(figsize=(10,6))

    for i, df in enumerate(dataframes):
        colors = ['blue', 'red', 'green']
        plt.plot(df['timestamp'], df['queue_length'], label=f'Machine {i + 1}', color=colors[i])

    plt.xlabel('Timestamp')
    plt.ylabel('Queue Length')
    plt.title('Queue Length for Each Machine')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(experiment_path, "plot_queue_length.png"))
    plt.close()



if __name__ == "__main__":
    logs_directory = '/Users/hannahkim/Desktop/Classes/CS262/cs262_design3/logs/'
 
    for experiment in os.listdir(logs_directory):
        # input("EXPERIMENT")
        experiment_path = os.path.join(logs_directory, experiment)
        
        # Skip if not a directory
        if not os.path.isdir(experiment_path):
            continue  

        # Find the CSV files in the experiment directory
        csv_files = [f for f in os.listdir(experiment_path) if f.endswith(".csv")]
        
        if len(csv_files) != 3:
            print(f"Skipping {experiment} (Expected 3 CSV files, found {len(csv_files)})")
            continue

        # Read each CSV file (modify column names as needed)
        dataframes = [pd.read_csv(os.path.join(experiment_path, csv)) for csv in csv_files]

        plot_raw(dataframes, experiment_path)
        plot_jumps(dataframes, experiment_path)
        plot_queue_length(dataframes, experiment_path)


