"""
Simple test script to verify the core simulation functionality.
"""
import os
import sys
import logging
import networkx as nx
import osmnx as ox
import numpy as np
from road_network import get_road_network
from simulation import Simulation, Vehicle
from traffic_signal import TrafficSignal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def create_test_network():
    """Create a simple test road network with 4 nodes and 4 edges."""
    logger.info("Creating test road network...")
    
    # Create a simple 2x2 grid graph
    G = nx.DiGraph()
    
    # Add nodes with coordinates (x, y)
    G.add_node(1, x=0, y=0)
    G.add_node(2, x=1, y=0)
    G.add_node(3, x=0, y=1)
    G.add_node(4, x=1, y=1)
    
    # Add edges with required attributes
    edges = [
        (1, 2, {'length': 100.0, 'speed_kph': 50.0, 'travel_time': 7.2}),
        (2, 1, {'length': 100.0, 'speed_kph': 50.0, 'travel_time': 7.2}),
        (1, 3, {'length': 100.0, 'speed_kph': 30.0, 'travel_time': 12.0}),
        (3, 1, {'length': 100.0, 'speed_kph': 30.0, 'travel_time': 12.0}),
        (2, 4, {'length': 100.0, 'speed_kph': 30.0, 'travel_time': 12.0}),
        (4, 2, {'length': 100.0, 'speed_kph': 30.0, 'travel_time': 12.0}),
        (3, 4, {'length': 100.0, 'speed_kph': 50.0, 'travel_time': 7.2}),
        (4, 3, {'length': 100.0, 'speed_kph': 50.0, 'travel_time': 7.2}),
    ]
    
    G.add_edges_from(edges)
    
    # Add graph attributes
    G.graph['crs'] = 'epsg:4326'
    
    logger.info(f"Created test network with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    return G

def run_test_simulation():
    """Run a test simulation with a simple road network."""
    logger.info("="*80)
    logger.info("SIMPLE SIMULATION TEST")
    logger.info("="*80)
    
    try:
        # Step 1: Create or load road network
        use_real_network = False  # Set to True to test with real OSM data
        
        if use_real_network:
            logger.info("Loading road network from OSM...")
            graph = get_road_network("27.7172, 85.3240", distance=500)  # Kathmandu
        else:
            logger.info("Creating test road network...")
            graph = create_test_network()
        
        if graph is None or graph.number_of_nodes() == 0:
            logger.error("Failed to create/load road network")
            return False
        
        logger.info(f"Road network loaded with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges")
        
        # Initialize simulation with the required number of vehicles
        num_vehicles = 5  # Number of vehicles to simulate
        logger.info(f"Initializing simulation with {num_vehicles} vehicles...")
        sim = Simulation(graph, num_vehicles=num_vehicles)
        
        # The Simulation class creates its own traffic signals, so we don't need to add them manually
        logger.info(f"Simulation initialized with {len(sim.traffic_signals)} traffic signals")
        
        # Step 4: Add some vehicles
        logger.info("Adding vehicles...")
        nodes = list(graph.nodes())
        
        for i in range(5):
            origin = np.random.choice(nodes)
            destination = np.random.choice([n for n in nodes if n != origin])
            
            try:
                path = nx.shortest_path(graph, origin, destination, weight='travel_time')
                # Create a vehicle with the required parameters
                vehicle = Vehicle(
                    vehicle_id=i,  # Integer ID
                    source=path[0],  # Source node
                    destination=path[-1],  # Destination node
                    path=path,  # Full path
                    start_step=0  # Start step
                )
                sim.add_vehicle(vehicle)
                logger.info(f"Added vehicle {i} from node {origin} to {destination} (path length: {len(path)})")
            except Exception as e:
                logger.warning(f"Failed to add vehicle {i}: {str(e)}")
        
        # Step 5: Run simulation steps
        num_steps = 10
        logger.info(f"\nRunning simulation for {num_steps} steps...")
        
        for step in range(num_steps):
            logger.info(f"\n--- Step {step + 1}/{num_steps} ---")
            
            # Update simulation
            sim.step()
            
            # Log vehicle positions
            for vehicle in sim.vehicles:
                if vehicle.current_edge:
                    logger.info(f"Vehicle {vehicle.vehicle_id} on edge {vehicle.current_edge} "
                               f"({vehicle.progress:.1f}% of edge)")
            
            # Log signal states
            for signal in sim.traffic_signals.values():
                logger.info(f"Signal at node {signal.node_id}: {signal.current_state}")
        
        logger.info("\nSimulation completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error in simulation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Set up console output
    print("="*80)
    print("TRAFFIC SIMULATION TEST")
    print("="*80)
    print("This test will verify the core simulation functionality with a simple road network.\n")
    
    # Run the test
    success = run_test_simulation()
    
    # Print final result
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test completed with errors.")
