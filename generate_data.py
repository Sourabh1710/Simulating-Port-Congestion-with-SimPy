import pandas as pd
import numpy as np
import os

# --- Simulation Parameters ---
# These are now for the INFLUX scenario
NUM_SHIPS = 80 # More ships to simulate a busy period
AVG_ARRIVAL_INTERVAL_NORMAL = 120 # 2 hours
AVG_ARRIVAL_INTERVAL_INFLUX = 30  # A ship every 30 minutes during the surge
INFLUX_START_SHIP = 20 # The surge starts after the 20th ship
INFLUX_END_SHIP = 60   # The surge ends after the 60th ship
CONTAINER_MEAN = 150
CONTAINER_STD_DEV = 50
RANDOM_SEED = 42
# IMPORTANT: New filename for the new scenario
FILENAME = "ship_arrivals_influx.csv"

def generate_arrival_data(num_ships, normal_interval, influx_interval, influx_start, influx_end, container_mean, container_std_dev, seed):
    """
    Generates ship arrival data with a period of high traffic (influx).
    """
    if num_ships <= 0:
        return pd.DataFrame()

    rng = np.random.RandomState(seed)
    
    inter_arrival_times = []
    for i in range(num_ships):
        if influx_start <= i < influx_end:
            # Use the high-traffic interval during the influx period
            inter_arrival_times.append(rng.exponential(scale=influx_interval))
        else:
            # Use the normal interval
            inter_arrival_times.append(rng.exponential(scale=normal_interval))

    arrival_times = np.cumsum(inter_arrival_times).astype(int)
    
    cargo_containers = np.maximum(10, rng.normal(loc=container_mean, scale=container_std_dev, size=num_ships)).astype(int)
    ship_ids = range(1, num_ships + 1)

    df = pd.DataFrame({
        'ship_id': ship_ids,
        'arrival_time_minutes': arrival_times,
        'cargo_containers': cargo_containers
    })
    return df

def main():
    print(f"Generating INFLUX ship arrival data for '{FILENAME}'...")
    arrival_data = generate_arrival_data(
        num_ships=NUM_SHIPS,
        normal_interval=AVG_ARRIVAL_INTERVAL_NORMAL,
        influx_interval=AVG_ARRIVAL_INTERVAL_INFLUX,
        influx_start=INFLUX_START_SHIP,
        influx_end=INFLUX_END_SHIP,
        container_mean=CONTAINER_MEAN,
        container_std_dev=CONTAINER_STD_DEV,
        seed=RANDOM_SEED
    )

    if arrival_data.empty:
        print("Error: Generated data is empty. File will not be created.")
    else:
        try:
            arrival_data.to_csv(FILENAME, index=False)
            full_path = os.path.abspath(FILENAME)
            print(f"Successfully generated {len(arrival_data)} records.")
            print(f"Data saved to '{full_path}'")
        except IOError as e:
            print(f"Error saving file: {e}")

if __name__ == "__main__":
    main()