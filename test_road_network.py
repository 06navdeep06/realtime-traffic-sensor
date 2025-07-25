import os
import sys
import logging
import networkx as nx
import osmnx as ox
from road_network import get_road_network

# Configure logging to console only
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Set your TomTom API key
os.environ['TOMTOM_API_KEY'] = 'tEZ8WgFXLuAuDjHmB3AB5y89ue31PsGL'

def log_graph_info(graph):
    """Log detailed information about the graph"""
    if not isinstance(graph, (nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph)):
        logger.error(f"Invalid graph type: {type(graph)}")
        return
    
    logger.info("\n" + "="*50)
    logger.info("GRAPH INFORMATION")
    logger.info("="*50)
    logger.info(f"Type: {type(graph)}")
    logger.info(f"Number of nodes: {graph.number_of_nodes()}")
    logger.info(f"Number of edges: {graph.number_of_edges()}")
    
    # Log graph attributes
    logger.info("\nGraph attributes:")
    if hasattr(graph, 'graph') and isinstance(graph.graph, dict):
        for k, v in graph.graph.items():
            logger.info(f"  {k}: {v}")
    else:
        logger.warning("No graph-level attributes found")
    
    # Log sample node data
    logger.info("\nSample node data:")
    for i, (node_id, node_data) in enumerate(graph.nodes(data=True)):
        if i >= 2:  # Only show first 2 nodes
            break
        logger.info(f"  Node {node_id}: {node_data}")
    
    # Log sample edge data
    logger.info("\nSample edge data:")
    for i, (u, v, data) in enumerate(graph.edges(data=True)):
        if i >= 2:  # Only show first 2 edges
            break
        logger.info(f"  Edge {u} -> {v}: {data}")
    
    logger.info("="*50 + "\n")

def debug_osmnx_import():
    """Debug information about OSMnx import and version"""
    logger.info("\nOSMnx Debug Information:")
    logger.info("-" * 50)
    try:
        logger.info(f"OSMnx version: {ox.__version__}")
        logger.info(f"NetworkX version: {nx.__version__}")
        logger.info(f"Python version: {sys.version}")
        
        # Check OSMnx configuration
        logger.info("\nOSMnx Configuration:")
        for k, v in ox.config.all_asdict().items():
            logger.info(f"  {k}: {v}")
            
    except Exception as e:
        logger.error(f"Error getting debug info: {e}")

def test_road_network():
    logger.info("🚦 Testing Road Network Loading 🚦")
    logger.info("=" * 50)
    
    # Print debug information first
    debug_osmnx_import()
    
    # Test with a small area in Kathmandu
    location = "27.7172, 85.3240"
    distance = 300  # meters
    
    logger.info(f"\n1. Loading road network for {location} (distance: {distance}m)")
    try:
        # Try to load the road network with detailed logging
        logger.info("\n1. Calling get_road_network...")
        try:
            graph = get_road_network(location, distance=distance)
            logger.info("get_road_network call completed")
            
            if graph is None:
                logger.error("get_road_network returned None")
                return False
                
            if not isinstance(graph, (nx.MultiDiGraph, nx.DiGraph, nx.MultiGraph, nx.Graph)):
                logger.error(f"Expected a NetworkX graph, got {type(graph)}")
                return False
                
            # Log basic graph info
            logger.info(f"Graph type: {type(graph)}")
            logger.info(f"Number of nodes: {graph.number_of_nodes()}")
            logger.info(f"Number of edges: {graph.number_of_edges()}")
            
            # Check if graph has nodes and edges
            if graph.number_of_nodes() == 0 or graph.number_of_edges() == 0:
                logger.warning("Graph has no nodes or edges")
                
            # Check if graph has required attributes
            if not hasattr(graph, 'graph') or not isinstance(graph.graph, dict):
                logger.warning("Graph is missing graph attributes dictionary")
                graph.graph = {}
                
            # Ensure CRS is set
            if 'crs' not in graph.graph:
                logger.warning("Setting default CRS to 'epsg:4326'")
                graph.graph['crs'] = 'epsg:4326'
                
        except Exception as e:
            logger.error(f"Error in get_road_network: {str(e)}")
            logger.error(traceback.format_exc())
            return False
            
        num_nodes = graph.number_of_nodes()
        num_edges = graph.number_of_edges()
        
        logger.info(f"Successfully loaded graph with {num_nodes} nodes and {num_edges} edges")
        log_graph_info(graph)
        
        # Detailed edge attribute validation
        logger.info("\n2. Validating edge attributes...")
        required_edge_attrs = ['length', 'speed_kph', 'travel_time']
        edge_issues = {attr: 0 for attr in required_edge_attrs}
        
        # Check first few edges in detail
        sample_edges = list(graph.edges(data=True))[:5]  # Check first 5 edges
        
        for i, (u, v, data) in enumerate(graph.edges(data=True)):
            # For all edges, count missing attributes
            for attr in required_edge_attrs:
                if attr not in data:
                    edge_issues[attr] += 1
                elif data[attr] is None or (isinstance(data[attr], (int, float)) and data[attr] <= 0):
                    logger.warning(f"Invalid {attr} value for edge {u}->{v}: {data[attr]}")
            
            # Log detailed info for first few edges
            if i < 3:  # First 3 edges
                logger.info(f"\nEdge {i+1}: {u} -> {v}")
                for k, v in data.items():
                    logger.info(f"  {k}: {v}")
        
        # Log validation results
        logger.info("\nEdge Attribute Summary:")
        logger.info("-" * 50)
        all_valid = True
        
        for attr in required_edge_attrs:
            count = edge_issues[attr]
            total_edges = graph.number_of_edges()
            if count > 0:
                logger.warning(f"  - {attr}: missing in {count}/{total_edges} edges ({count/total_edges*100:.1f}%)")
                all_valid = False
                
                # For missing attributes, try to add default values
                if attr == 'speed_kph':
                    logger.info("    Adding default speed_kph=30 to missing edges")
                    for u, v, data in graph.edges(data=True):
                        if 'speed_kph' not in data:
                            data['speed_kph'] = 30.0
                elif attr == 'length':
                    logger.info("    Calculating missing lengths from node coordinates")
                    for u, v, data in graph.edges(data=True):
                        if 'length' not in data and 'x' in graph.nodes[u] and 'y' in graph.nodes[u] and 'x' in graph.nodes[v] and 'y' in graph.nodes[v]:
                            import math
                            dx = graph.nodes[u]['x'] - graph.nodes[v]['x']
                            dy = graph.nodes[u]['y'] - graph.nodes[v]['y']
                            data['length'] = math.sqrt(dx*dx + dy*dy) * 100000  # Approx meters
            else:
                logger.info(f"  - {attr}: present in all edges")
        
        # Calculate travel times if missing
        missing_tt = sum(1 for u, v, data in graph.edges(data=True) if 'travel_time' not in data and 'length' in data and 'speed_kph' in data)
        if missing_tt > 0:
            logger.info(f"Calculating travel_time for {missing_tt} edges")
            for u, v, data in graph.edges(data=True):
                if 'travel_time' not in data and 'length' in data and 'speed_kph' in data and data['speed_kph'] > 0:
                    data['travel_time'] = (data['length'] / 1000) / float(data['speed_kph']) * 3600  # in seconds
        
        if all_valid:
            logger.info("\n✅ All required edge attributes are present and valid")
        else:
            logger.warning("\n⚠️  Some edge attributes were missing or invalid (see above)")
        
        # Test graph connectivity
        try:
            if num_nodes > 0:
                if not nx.is_weakly_connected(graph):
                    logger.warning("Graph is not weakly connected")
                    # Count weakly connected components
                    wcc = list(nx.weakly_connected_components(graph))
                    logger.info(f"Number of weakly connected components: {len(wcc)}")
                    logger.info(f"Component sizes: {[len(comp) for comp in wcc[:5]]}...")
        except Exception as e:
            logger.warning(f"Could not check graph connectivity: {str(e)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in test_road_network: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    test_road_network()
