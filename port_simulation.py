import simpy
import pandas as pd
import os

# --- Simulation Parameters ---
NUM_BERTHS = 2
NUM_CRANES = 2
TIME_TO_UNLOAD_ONE_CONTAINER = 2  # In minutes
INPUT_FILE = 'ship_arrivals_normal.csv'
RESULTS_FILE = 'results_normal.csv'

# This list will store dictionaries, each representing a completed ship process
results_data = []

def ship(env, name, port, arrival_time, cargo_containers):
    """
    Models the process of a single ship. It records key timestamps during its journey.
    """
    # Record the actual arrival time (which might be different from scheduled if sim starts late)
    time_arrived = env.now
    
    # Store data for this ship
    ship_data = {
        'ship_id': name,
        'cargo_containers': cargo_containers,
        'time_arrived_port': time_arrived
    }

    print(f"Time {time_arrived:.2f}: Ship {name} has arrived at the port.")

    with port.berths.request() as berth_request:
        yield berth_request
        time_docked = env.now
        ship_data['time_docked'] = time_docked
        print(f"Time {time_docked:.2f}: Ship {name} has docked.")

        with port.cranes.request() as crane_request:
            yield crane_request
            time_crane_secured = env.now
            ship_data['time_crane_secured'] = time_crane_secured
            print(f"Time {time_crane_secured:.2f}: Ship {name} has secured a crane.")

            unloading_duration = cargo_containers * TIME_TO_UNLOAD_ONE_CONTAINER
            yield env.timeout(unloading_duration)
            
            time_unloading_complete = env.now
            ship_data['time_unloading_complete'] = time_unloading_complete
            print(f"Time {time_unloading_complete:.2f}: Ship {name} has finished unloading.")
            
        print(f"Time {env.now:.2f}: Ship {name} has released the crane.")

    time_departed = env.now
    ship_data['time_departed_port'] = time_departed
    print(f"Time {time_departed:.2f}: Ship {name} is departing.")
    
    # Add the completed ship's data to our results list
    results_data.append(ship_data)


class Port:
    def __init__(self, env, num_berths, num_cranes):
        self.env = env
        self.berths = simpy.Resource(env, capacity=num_berths)
        self.cranes = simpy.Resource(env, capacity=num_cranes)


def calculate_and_save_results(output_filename):
    """
    Processes the simulation results, calculates KPIs, and saves them.
    """
    if not results_data:
        print("Warning: Results data is empty. No output file will be generated.")
        return

    # Convert the list of dictionaries to a pandas DataFrame
    results_df = pd.DataFrame(results_data)

    # --- Calculate KPIs ---
    results_df['wait_time_for_berth'] = results_df['time_docked'] - results_df['time_arrived_port']
    results_df['wait_time_for_crane'] = results_df['time_crane_secured'] - results_df['time_docked']
    results_df['turnaround_time'] = results_df['time_departed_port'] - results_df['time_arrived_port']

    # --- Print KPI Summary to Console ---
    print("\n" + "="*40)
    print("           PORT PERFORMANCE KPIs")
    print("="*40)
    print(f"Total Ships Processed: {len(results_df)}")
    print(f"Average Berth Wait Time: {results_df['wait_time_for_berth'].mean():.2f} minutes")
    print(f"Maximum Berth Wait Time: {results_df['wait_time_for_berth'].max():.2f} minutes")
    print(f"Average Crane Wait Time: {results_df['wait_time_for_crane'].mean():.2f} minutes")
    print(f"Average Turnaround Time: {results_df['turnaround_time'].mean():.2f} minutes")
    print("="*40 + "\n")

    # --- Save Detailed Results to CSV ---
    try:
        results_df.to_csv(output_filename, index=False)
        full_path = os.path.abspath(output_filename)
        print(f"Detailed results saved to '{full_path}'")
    except IOError as e:
        print(f"Error saving results file: {e}")


def run_simulation(num_berths, num_cranes, unload_time, input_file, results_file):
    """
    Sets up and runs the port simulation with configurable parameters.
    """
    print(f"--- Starting Simulation: {results_file} ---")
    print(f"Berths: {num_berths}, Cranes: {num_cranes}\n")
    
    global results_data # Use the global results list
    results_data.clear() # Clear results from any previous run

    try:
        arrivals_df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return

    env = simpy.Environment()
    port = Port(env, num_berths, num_cranes)

    # Inner ship function needs access to the unload time per container
    def ship_process(env, name, port, arrival_time, cargo_containers):
        
        time_arrived = env.now
        ship_data = {'ship_id': name, 'cargo_containers': cargo_containers, 'time_arrived_port': time_arrived}
        print(f"Time {time_arrived:.2f}: Ship {name} has arrived.")
        with port.berths.request() as berth_request:
            yield berth_request
            ship_data['time_docked'] = env.now
            print(f"Time {env.now:.2f}: Ship {name} has docked.")
            with port.cranes.request() as crane_request:
                yield crane_request
                ship_data['time_crane_secured'] = env.now
                print(f"Time {env.now:.2f}: Ship {name} has secured a crane.")
                unloading_duration = cargo_containers * unload_time # Use passed-in parameter
                yield env.timeout(unloading_duration)
                ship_data['time_unloading_complete'] = env.now
                print(f"Time {env.now:.2f}: Ship {name} has finished unloading.")
            print(f"Time {env.now:.2f}: Ship {name} has released the crane.")
        ship_data['time_departed_port'] = env.now
        print(f"Time {env.now:.2f}: Ship {name} is departing.")
        results_data.append(ship_data)

    def arrival_process(env, port, arrivals_df):
        for _, row in arrivals_df.iterrows():
            yield env.timeout(row['arrival_time_minutes'] - env.now)
            env.process(ship_process(env, row['ship_id'], port, row['arrival_time_minutes'], row['cargo_containers']))

    env.process(arrival_process(env, port, arrivals_df))
    simulation_runtime = arrivals_df['arrival_time_minutes'].max() + 20000 # More buffer time
    env.run(until=simulation_runtime)
    
    print("\n--- Simulation Complete ---")
    calculate_and_save_results(results_file)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Port Congestion Simulation")
    parser.add_argument("--berths", type=int, default=2, help="Number of berths available.")
    parser.add_argument("--cranes", type=int, default=2, help="Number of cranes available.")
    parser.add_argument("--input", type=str, default="ship_arrivals_normal.csv", help="Input CSV file for ship arrivals.")
    parser.add_argument("--output", type=str, default="results_normal.csv", help="Output CSV file for results.")
    
    args = parser.parse_args()

    run_simulation(
        num_berths=args.berths,
        num_cranes=args.cranes,
        unload_time=2, # Corresponds to TIME_TO_UNLOAD_ONE_CONTAINER
        input_file=args.input,
        results_file=args.output
    )