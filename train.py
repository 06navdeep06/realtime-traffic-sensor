import os
from road_network import get_road_network
from simulation import Simulation

def train_agent(city_name, num_episodes, num_steps, num_vehicles):
    """
    Train the RL agent for traffic signal control.
    """
    print(f"--- Starting Training for {city_name} ---")
    
    # Create a directory to save the learned Q-tables
    q_tables_dir = "q_tables"
    if not os.path.exists(q_tables_dir):
        os.makedirs(q_tables_dir)

    # Load the road network once
    graph = get_road_network(city_name)

    for episode in range(num_episodes):
        print(f"--- Episode {episode + 1}/{num_episodes} ---")
        
        # Initialize a new simulation for each episode
        sim = Simulation(graph, num_vehicles)

        # Load Q-tables for all signals at the start of the episode
        for signal_id, signal in sim.traffic_signals.items():
            q_table_path = os.path.join(q_tables_dir, f"q_table_{signal_id}.json")
            signal.agent.load_q_table(q_table_path)

        # Run the simulation for a fixed number of steps
        for step in range(num_steps):
            sim.step()
            if (step + 1) % 100 == 0:
                print(f"  Step {step + 1}/{num_steps} completed.")

        # Save the learned Q-tables for all signals
        for signal_id, signal in sim.traffic_signals.items():
            q_table_path = os.path.join(q_tables_dir, f"q_table_{signal_id}.json")
            signal.agent.save_q_table(q_table_path)
            
        print(f"--- Episode {episode + 1} completed. Q-tables saved. ---")

if __name__ == "__main__":
    CITY = "Patan, Nepal"
    EPISODES = 10  # Number of full simulation runs for training
    STEPS_PER_EPISODE = 1000  # Number of time steps in each simulation
    VEHICLES = 200 # Number of vehicles in the simulation
    
    train_agent(CITY, EPISODES, STEPS_PER_EPISODE, VEHICLES)
