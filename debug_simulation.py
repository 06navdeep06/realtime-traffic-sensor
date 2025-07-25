"""
Debug script to help identify the 'current_edge' attribute issue.
"""
import os
import sys
import logging
import networkx as nx
import osmnx as ox
from simulation import Simulation, Vehicle
from traffic_signal import TrafficSignal

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def create_test_network():
    """Create a simple test road network."""
    G = nx.DiGraph()
    
    # Add nodes with coordinates
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
    G.graph['crs'] = 'epsg:4326'
    return G

def test_vehicle_creation():
    """Test vehicle creation and edge tracking."""
    logger.info("\n" + "="*50)
    logger.info("TESTING VEHICLE CLASS")
    logger.info("="*50)
    
    # Create a simple path
    path = [1, 2, 4, 3]
    logger.info(f"Test path: {path}")
    
    # Create a vehicle
    vehicle = Vehicle(
        vehicle_id=1,
        source=path[0],
        destination=path[-1],
        path=path,
        start_step=0
    )
    
    # Test initial state
    logger.info("\nInitial vehicle state:")
    logger.info(f"  - ID: {vehicle.vehicle_id}")
    logger.info(f"  - Source: {vehicle.source}")
    logger.info(f"  - Destination: {vehicle.destination}")
    logger.info(f"  - Current node index: {vehicle.current_node_index}")
    logger.info(f"  - Current location: {vehicle.current_location}")
    logger.info(f"  - Current edge: {vehicle.current_edge}")
    logger.info(f"  - Is active: {vehicle.is_active}")
    
    # Test moving the vehicle
    logger.info("\nMoving vehicle...")
    try:
        vehicle.move({}, 1)  # Empty traffic signals for now
        logger.info("Move successful")
    except Exception as e:
        logger.error(f"Error moving vehicle: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Log state after move
    logger.info("\nAfter move:")
    logger.info(f"  - Current node index: {vehicle.current_node_index}")
    logger.info(f"  - Current location: {vehicle.current_location}")
    logger.info(f"  - Current edge: {vehicle.current_edge}")
    logger.info(f"  - Is active: {vehicle.is_active}")
    
    # Try moving through the entire path
    logger.info("\nMoving vehicle through entire path:")
    step = 2
    while vehicle.is_active and step < 10:  # Prevent infinite loop
        try:
            logger.info(f"\nStep {step}:")
            logger.info(f"  Current edge before move: {vehicle.current_edge}")
            vehicle.move({}, step)
            logger.info(f"  Current edge after move: {vehicle.current_edge}")
            logger.info(f"  Current location: {vehicle.current_location}")
            logger.info(f"  Is active: {vehicle.is_active}")
            step += 1
        except Exception as e:
            logger.error(f"Error at step {step}: {str(e)}")
            break
    
    logger.info("\nFinal vehicle state:")
    logger.info(f"  - Current node index: {vehicle.current_node_index}")
    logger.info(f"  - Current location: {vehicle.current_location}")
    logger.info(f"  - Current edge: {vehicle.current_edge}")
    logger.info(f"  - Is active: {vehicle.is_active}")
    logger.info(f"  - End step: {vehicle.end_step}")
    
    return vehicle

def test_simulation():
    """Test simulation with a simple network."""
    logger.info("\n" + "="*50)
    logger.info("TESTING SIMULATION")
    logger.info("="*50)
    
    logger.info("\nCreating test network...")
    graph = create_test_network()
    
    # Log network info
    logger.info(f"Network has {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges")
    logger.info(f"Nodes: {list(graph.nodes())}")
    logger.info(f"Edges: {list(graph.edges())}")
    
    # Create simulation with 2 vehicles
    logger.info("\nInitializing simulation with 2 vehicles...")
    sim = Simulation(graph, num_vehicles=2)
    
    # Log initial state
    logger.info("\nInitial simulation state:")
    logger.info(f"  - Number of vehicles: {len(sim.vehicles)}")
    logger.info(f"  - Traffic signals at nodes: {list(sim.traffic_signals.keys())}")
    
    # Log initial vehicle states
    logger.info("\nInitial vehicle states:")
    for vid, vehicle in sim.vehicles.items():
        logger.info(f"  Vehicle {vid}:")
        logger.info(f"    - Source: {vehicle.source}")
        logger.info(f"    - Destination: {vehicle.destination}")
        logger.info(f"    - Path: {vehicle.path}")
        logger.info(f"    - Current location: {vehicle.current_location}")
        logger.info(f"    - Current edge: {getattr(vehicle, 'current_edge', 'N/A')}")
        logger.info(f"    - Is active: {vehicle.is_active}")
    
    # Run simulation steps with detailed logging
    num_steps = 5
    logger.info(f"\nRunning simulation for {num_steps} steps...")
    
    for step in range(num_steps):
        logger.info(f"\n--- Step {step + 1}/{num_steps} ---")
        
        try:
            # Log state before step
            logger.info("Before step:")
            for vid, vehicle in sim.vehicles.items():
                logger.info(f"  Vehicle {vid}: {vehicle}")
                logger.info(f"    - Current edge: {getattr(vehicle, 'current_edge', 'N/A')}")
                logger.info(f"    - Is active: {vehicle.is_active}")
            
            # Execute step
            sim.step()
            
            # Log state after step
            logger.info("After step:")
            for vid, vehicle in sim.vehicles.items():
                logger.info(f"  Vehicle {vid}: {vehicle}")
                logger.info(f"    - Current edge: {getattr(vehicle, 'current_edge', 'N/A')}")
                logger.info(f"    - Is active: {vehicle.is_active}")
                
                # Log traffic signal state if at an intersection
                if (hasattr(vehicle, 'current_location') and 
                    vehicle.current_location in sim.traffic_signals):
                    signal = sim.traffic_signals[vehicle.current_location]
                    logger.info(f"    - At intersection {vehicle.current_location} with signal state: {signal.green_lane_index}")
            
        except Exception as e:
            logger.error(f"Error during step {step + 1}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            break
    
    # Log final simulation statistics
    logger.info("\nSimulation completed")
    logger.info(f"  - Total steps: {sim.step_count}")
    logger.info(f"  - Completed trips: {len(sim.completed_trip_times)}")
    if sim.completed_trip_times:
        logger.info(f"  - Average trip time: {sum(sim.completed_trip_times)/len(sim.completed_trip_times):.2f} steps")
    
    return sim

if __name__ == "__main__":
    # Set up file logging with a unique filename
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"debug_simulation_{timestamp}.log"
    
    # Clear existing handlers to avoid duplicate logs
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Configure file handler
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Configure console handler
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(console_formatter)
    
    # Add both handlers to root logger
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console)
    
    # Configure console logging
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    
    logger.info("="*80)
    logger.info("DEBUG SIMULATION")
    logger.info("="*80)
    logger.info(f"Detailed logs will be saved to: {os.path.abspath(log_file)}")
    
    try:
        # Test 1: Vehicle class
        logger.info("\n" + "#"*50)
        logger.info("1. TESTING VEHICLE CLASS IN ISOLATION")
        logger.info("#"*50)
        test_vehicle_creation()
        
        # Test 2: Full simulation
        logger.info("\n" + "#"*50)
        logger.info("2. TESTING FULL SIMULATION")
        logger.info("#"*50)
        test_simulation()
        
        logger.info("\n✅ Debug tests completed successfully!")
    except Exception as e:
        logger.error(f"\n❌ Error in debug test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Clean up handlers
        root_logger.removeHandler(file_handler)
        file_handler.close()
        
        # Print location of log file
        print(f"\nDetailed logs saved to: {os.path.abspath(log_file)}")
