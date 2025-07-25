"""
Test script to verify the road network loading works with OSMnx 2.0.5
"""
import os
import sys
import logging
import networkx as nx
import osmnx as ox
from road_network import get_road_network

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def main():
    print("="*80)
    print("ROAD NETWORK LOADING TEST (OSMnx 2.0.5 Compatible)")
    print("="*80)
    
    # Test location (Kathmandu)
    location = "27.7172, 85.3240"
    distance = 500  # meters
    
    print(f"\n1. Loading road network for {location} (distance: {distance}m)")
    
    try:
        # Get the road network
        graph = get_road_network(location, distance=distance)
        
        if graph is None:
            print("ERROR: get_road_network returned None")
            return False
            
        if not isinstance(graph, (nx.MultiDiGraph, nx.DiGraph, nx.MultiGraph, nx.Graph)):
            print(f"ERROR: Expected a NetworkX graph, got {type(graph)}")
            return False
            
        # Print basic graph info
        print(f"\n2. Graph Information:")
        print(f"   - Type: {type(graph)}")
        print(f"   - Is directed: {isinstance(graph, nx.DiGraph) or isinstance(graph, nx.MultiDiGraph)}")
        print(f"   - Number of nodes: {graph.number_of_nodes()}")
        print(f"   - Number of edges: {graph.number_of_edges()}")
        
        # Check for required attributes
        print("\n3. Checking for required edge attributes:")
        required_attrs = ['length', 'speed_kph', 'travel_time']
        
        for attr in required_attrs:
            missing = sum(1 for u, v, data in graph.edges(data=True) if attr not in data)
            total = graph.number_of_edges()
            status = "✅" if missing == 0 else f"❌ (missing in {missing}/{total} edges)"
            print(f"   - {attr}: {status}")
        
        # Print sample edges
        print("\n4. Sample edges:")
        for i, (u, v, data) in enumerate(graph.edges(data=True)):
            if i >= 2:  # Only show first 2 edges
                break
            print(f"   Edge {u} -> {v}:")
            for k, v in data.items():
                print(f"     {k}: {v}")
        
        print("\n✅ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
