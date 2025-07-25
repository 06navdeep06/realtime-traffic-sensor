import os
import time
import logging
import networkx as nx
from road_network import get_road_network, update_graph_with_traffic
from simulation import Simulation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('simulation_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Suppress some of the verbose logging from dependencies
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('osmnx').setLevel(logging.WARNING)

# Set your TomTom API key
os.environ['TOMTOM_API_KEY'] = 'tEZ8WgFXLuAuDjHmB3AB5y89ue31PsGL'

def log_step(step_num, message):
    """Helper function to log steps with consistent formatting"""
    logger.info(f"STEP {step_num}: {message}")

def log_graph_stats(graph):
    """Log detailed statistics about the graph"""
    if not isinstance(graph, nx.Graph):
        logger.error("Invalid graph object provided")
        return
        
    logger.info("\n" + "="*50)
    logger.info("GRAPH STATISTICS")
    logger.info("="*50)
    logger.info(f"Number of nodes: {graph.number_of_nodes()}")
    logger.info(f"Number of edges: {graph.number_of_edges()}")
    
    # Check for required node and edge attributes
    required_node_attrs = ['x', 'y']
    required_edge_attrs = ['length', 'speed_kph', 'travel_time']
    
    # Check node attributes
    missing_node_attrs = []
    for node_id, node_data in graph.nodes(data=True):
        for attr in required_node_attrs:
            if attr not in node_data:
                missing_node_attrs.append(attr)
    if missing_node_attrs:
        logger.warning(f"Missing node attributes: {set(missing_node_attrs)}")
    
    # Check edge attributes
    missing_edge_attrs = []
    for u, v, data in graph.edges(data=True):
        for attr in required_edge_attrs:
            if attr not in data:
                missing_edge_attrs.append(attr)
    if missing_edge_attrs:
        logger.warning(f"Missing edge attributes: {set(missing_edge_attrs)}")
    
    # Log sample edge data
    logger.info("\nSample edge data:")
    for i, (u, v, data) in enumerate(graph.edges(data=True)):
        if i >= 3:  # Only show first 3 edges
            break
        logger.info(f"  Edge {u} -> {v}: {data}")
    
    logger.info("="*50 + "\n")

def run_basic_simulation():
    logger.info("🚦 Starting Basic Traffic Simulation Test 🚦")
    logger.info("=" * 50)
    
    try:
        # 1. Load a small road network
        log_step(1, "Loading road network...")
        location = "27.7172, 85.3240"  # Kathmandu coordinates
        logger.info(f"Location: {location}")
        logger.info("This may take a moment...")
        
        try:
            # Try to load the road network
            graph = get_road_network(location, distance=300)  # Small area for testing
            if graph is None or len(graph.nodes()) == 0:
                logger.error("Failed to load road network: Empty graph returned")
                return False
                
            logger.info(f"Success! Loaded graph with {len(graph.nodes())} nodes and {len(graph.edges())} edges.")
            
            # Log detailed graph statistics
            log_graph_stats(graph)
            
            # Ensure the graph has required attributes
            if not hasattr(graph, 'graph'):
                graph.graph = {}
                
            # Add required attributes if missing
            if 'crs' not in graph.graph:
                graph.graph['crs'] = 'epsg:4326'  # Default to WGS84
                logger.warning("Added missing CRS to graph")
                
            if 'name' not in graph.graph:
                graph.graph['name'] = 'unnamed_graph'
                
            # Double-check that all edges have required attributes
            for u, v, data in graph.edges(data=True):
                if 'speed_kph' not in data:
                    data['speed_kph'] = 30.0  # Default speed
                    logger.warning(f"Added missing speed_kph to edge {u}->{v}")
                if 'length' not in data:
                    # Calculate length from coordinates if possible
                    if 'x' in graph.nodes[u] and 'y' in graph.nodes[u] and 'x' in graph.nodes[v] and 'y' in graph.nodes[v]:
                        import math
                        dx = graph.nodes[u]['x'] - graph.nodes[v]['x']
                        dy = graph.nodes[u]['y'] - graph.nodes[v]['y']
                        data['length'] = math.sqrt(dx*dx + dy*dy) * 100000  # Approximate conversion to meters
                        logger.warning(f"Calculated missing length for edge {u}->{v}: {data['length']:.2f}m")
                    else:
                        data['length'] = 100.0  # Default length
                        logger.warning(f"Added default length to edge {u}->{v}")
                        
                if 'travel_time' not in data and 'length' in data and 'speed_kph' in data:
                    # Calculate travel time in seconds: (distance in km) / (speed in km/h) * 3600
                    distance_km = data['length'] / 1000  # Convert meters to km
                    speed_kmh = float(data['speed_kph'])
                    if speed_kmh > 0:
                        data['travel_time'] = (distance_km / speed_kmh) * 3600
                        logger.info(f"Calculated travel time for edge {u}->{v}: {data['travel_time']:.2f}s")
                    else:
                        data['travel_time'] = 10.0  # Default travel time
                        logger.warning(f"Added default travel time to edge {u}->{v}")
                        
        except Exception as e:
            logger.error(f"Error loading or processing road network: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
            
        # Ensure edges have required attributes
        for u, v, data in graph.edges(data=True):
            # Add default speed if missing (in km/h)
            if 'speed_kph' not in data:
                data['speed_kph'] = 30.0  # Default speed
                
            # Add length if missing (in meters)
            if 'length' not in data:
                data['length'] = 100.0  # Default length
                
            # Add travel time if missing (in seconds)
            if 'travel_time' not in data and 'speed_kph' in data and 'length' in data:
                if data['speed_kph'] > 0:
                    data['travel_time'] = (data['length'] / 1000) / data['speed_kph'] * 3600  # seconds
        
        # 2. Initialize simulation with a small number of vehicles
        log_step(2, "Initializing simulation...")
        num_vehicles = 20
        
        try:
            sim = Simulation(graph, num_vehicles)
            logger.info(f"Created simulation with {num_vehicles} vehicles")
            logger.info(f"Found {len(sim.intersections)} intersections")
            
            # Log some simulation details
            if hasattr(sim, 'traffic_signals'):
                logger.info(f"Created {len(sim.traffic_signals)} traffic signals")
            else:
                logger.warning("No traffic signals were created")
                
        except Exception as e:
            logger.error(f"Failed to initialize simulation: {str(e)}")
            logger.error("This might be due to missing nodes/edges or other graph issues")
            return False
        
        # 3. Run simulation for a few steps
        log_step(3, "Running simulation (10 steps)...")
        logger.info("Starting simulation loop...")
        
        for step in range(10):
            try:
                logger.info(f"\n--- Step {step + 1} ---")
                
                # Get the current simulation state
                state = sim.step()
                
                # Log basic metrics
                logger.info(f"Active vehicles: {state['active_vehicles']}")
                logger.info(f"Average trip time: {state['avg_trip_time']:.1f} steps")
                
                # Log congestion information
                if 'edge_congestion' in state and state['edge_congestion']:
                    congested_edges = [(e, c) for e, c in state['edge_congestion'].items() if c > 0]
                    logger.info(f"Congested edges: {len(congested_edges)}")
                    if congested_edges:
                        logger.info(f"Most congested: {max(congested_edges, key=lambda x: x[1])}")
                
                # Log signal states
                if 'signal_states' in state and state['signal_states']:
                    signals = list(state['signal_states'].items())
                    logger.info(f"Signal states (sample): {signals[:3]}")
                
                # Small delay to prevent overwhelming the output
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error in simulation step {step + 1}: {str(e)}")
                logger.error("This might indicate an issue with the simulation state")
                return False
            
        logger.info("\n✅ Simulation completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Critical error in simulation: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("="*80)
    print("TRAFFIC SIMULATION TEST")
    print("="*80)
    print("This test will verify the full simulation pipeline with the updated road network code.\n")
    
    try:
        print("1. Starting main test function...")
        success = run_basic_simulation()
        if success:
            print("\n✅ Test completed successfully!")
        else:
            print("\n❌ Test completed with warnings or errors.")
    except Exception as e:
        print(f"\n❌ ERROR: Unhandled exception in test: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\n❌ Test failed with errors.")
