import os
import pandas as pd
import matplotlib.pyplot as plt

def plot_raw(dataframes, experiment_path):
    """Plot the raw logical clock values for each machine."""
    plt.figure(figsize=(12, 6))
    
    colors = ['blue', 'red', 'green', 'orange']  # In case you have >3
    
    for i, df in enumerate(dataframes):
        # 1) Convert timestamp from object to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

        # 2) Drop any invalid timestamps
        df = df.dropna(subset=["timestamp"])

        # 3) Sort by timestamp
        df = df.sort_values("timestamp")

        # 4) Group/aggregate if needed
        df = df.groupby("timestamp", as_index=False, sort=True)["logical_clock"].mean()

        # 5) Round or clean up if desired
        df["logical_clock"] = df["logical_clock"].round(4)

        # 6) Plot
        plt.plot(
            df["timestamp"], 
            df["logical_clock"],
            marker='o',
            label=f"Machine {i+1}",
            color=colors[i % len(colors)]
        )

    plt.title(f"{experiment}: Raw Logical Clock Values")
    plt.xlabel("Timestamp")
    plt.ylabel("Logical Clock Value")
    plt.xticks(rotation=90)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    # Save
    save_path = os.path.join(experiment_path, "test.png")
    plt.savefig(save_path)
    plt.close()

    print(f"Plot saved for {experiment} at {save_path}")

if __name__ == "__main__":
    logs_directory = '/Users/durdledoor/Library/Mobile Documents/com~apple~CloudDocs/testing/cs262_design3/logs'

    experiment = 'run_clock_1741069347'
 
    # input("EXPERIMENT")
    experiment_path = os.path.join(logs_directory, experiment)
    
    # Find the CSV files in the experiment directory
    csv_files = [f for f in os.listdir(experiment_path) if f.endswith(".csv")]
    
    # Read each CSV file (modify column names as needed)
    dataframes = [pd.read_csv(os.path.join(experiment_path, csv)) for csv in csv_files]

    plot_raw(dataframes, experiment_path)