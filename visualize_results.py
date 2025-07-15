import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- Configuration ---
# A dictionary mapping the file names to the names we want in our plot legends.
RESULT_FILES = {
    'Normal': 'results_normal.csv',
    'Influx': 'results_influx.csv',
    'Crane Shortage': 'results_crane_shortage.csv'
}

# Create a directory to save the plots, if it doesn't already exist.
PLOTS_DIR = 'plots'
if not os.path.exists(PLOTS_DIR):
    os.makedirs(PLOTS_DIR)

def load_all_results(files_dict):
    """Loads multiple result CSVs into a single DataFrame."""
    all_data = []
    for scenario_name, file_path in files_dict.items():
        try:
            df = pd.read_csv(file_path)
            df['scenario'] = scenario_name  # Add a column to identify the scenario
            all_data.append(df)
        except FileNotFoundError:
            print(f"Warning: Result file not found at '{file_path}'. Skipping.")
    
    if not all_data:
        return pd.DataFrame() # Return empty df if no files were found
        
    return pd.concat(all_data, ignore_index=True)

def create_and_save_plots(results_df):
    """Generates and saves all the comparison plots."""
    
    if results_df.empty:
        print("Cannot generate plots because no result data was loaded.")
        return

    print("Generating and saving plots...")

    # Set a professional plot style
    sns.set_theme(style="whitegrid")

    # --- Plot 1: Average Wait Times (Bar Chart) ---
    avg_times = results_df.groupby('scenario')[['wait_time_for_berth', 'wait_time_for_crane']].mean().reset_index()
    avg_times_melted = avg_times.melt(id_vars='scenario', var_name='wait_type', value_name='average_minutes')
    
    plt.figure(figsize=(10, 6))
    barplot = sns.barplot(data=avg_times_melted, x='scenario', y='average_minutes', hue='wait_type')
    plt.title('Average Wait Times by Scenario', fontsize=16)
    plt.ylabel('Average Wait Time (minutes)')
    plt.xlabel('Scenario')
    plt.legend(title='Wait Type', labels=['Berth Wait', 'Crane Wait'])
    # Add text labels on bars
    for p in barplot.patches:
        barplot.annotate(f"{p.get_height():.0f}", 
                         (p.get_x() + p.get_width() / 2., p.get_height()), 
                         ha = 'center', va = 'center', 
                         xytext = (0, 9), 
                         textcoords = 'offset points')
    plt.savefig(os.path.join(PLOTS_DIR, 'average_wait_times.png'))
    plt.close() # Close the plot to free memory

    # --- Plot 2: Distribution of Turnaround Times (Box Plot) ---
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=results_df, x='scenario', y='turnaround_time')
    plt.title('Distribution of Ship Turnaround Times by Scenario', fontsize=16)
    plt.ylabel('Turnaround Time (minutes)')
    plt.xlabel('Scenario')
    plt.savefig(os.path.join(PLOTS_DIR, 'turnaround_time_distribution.png'))
    plt.close()
    
    # --- Plot 3: Wait Time for Berth (Box Plot) ---
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=results_df, x='scenario', y='wait_time_for_berth')
    plt.title('Distribution of Berth Wait Times by Scenario', fontsize=16)
    plt.ylabel('Wait Time for Berth (minutes)')
    plt.xlabel('Scenario')
    plt.savefig(os.path.join(PLOTS_DIR, 'berth_wait_time_distribution.png'))
    plt.close()
    
    print(f"Successfully saved 3 plots to the '{PLOTS_DIR}' directory.")


def main():
    """Main function to run the visualization script."""
    all_results_df = load_all_results(RESULT_FILES)
    create_and_save_plots(all_results_df)

if __name__ == "__main__":
    main()