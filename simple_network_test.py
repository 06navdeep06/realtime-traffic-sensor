import os
import sys
import logging
import networkx as nx
import osmnx as ox
import traceback

# Configure logging to console only
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # Simpler format
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def main():
    print("="*80)
    print("SIMPLE ROAD NETWORK TEST")
    print("="*80)
    
    # Test location (Kathmandu)
    location = "27.7172, 85.3240"
    distance = 500  # meters
    
    print(f"\n1. Attempting to load road network for {location} (distance: {distance}m)")
    
    try:
        # Try to get a small road network
        print("\nCalling ox.graph_from_point()...")
        graph = ox.graph_from_point(
            (27.7172, 85.3240),  # Kathmandu coordinates
            dist=distance,
            network_type='drive',
            simplify=True,
            retain_all=True
        )
        
        if graph is None:
            print("ERROR: ox.graph_from_point() returned None")
            return
            
        print(f"\n2. Graph loaded successfully!")
        print(f"   - Type: {type(graph)}")
        print(f"   - Nodes: {graph.number_of_nodes()}")
        print(f"   - Edges: {graph.number_of_edges()}")
        
        # Check if graph has nodes and edges
        if graph.number_of_nodes() == 0 or graph.number_of_edges() == 0:
            print("WARNING: Graph has no nodes or edges!")
            return
            
        # Check first few nodes
        print("\n3. First 3 nodes:")
        for i, (node_id, node_data) in enumerate(graph.nodes(data=True)):
            if i >= 3:
                break
            print(f"   Node {node_id}: {node_data}")
            
        # Check first few edges
        print("\n4. First 3 edges:")
        for i, (u, v, data) in enumerate(graph.edges(data=True)):
            if i >= 3:
                break
            print(f"   Edge {u} -> {v}:")
            for k, v in data.items():
                print(f"     {k}: {v}")
        
        # Check for required attributes
        print("\n5. Checking for required attributes:")
        required_attrs = ['length', 'speed_kph', 'travel_time']
        
        for attr in required_attrs:
            missing = sum(1 for u, v, data in graph.edges(data=True) if attr not in data)
            total = graph.number_of_edges()
            print(f"   - {attr}: {total - missing}/{total} edges have this attribute")
            
            # Try to add missing attributes
            if missing > 0:
                print(f"     Adding missing {attr}...")
                if attr == 'speed_kph':
                    for u, v, data in graph.edges(data=True):
                        if 'speed_kph' not in data:
                            data['speed_kph'] = 30.0
                elif attr == 'length':
                    for u, v, data in graph.edges(data=True):
                        if 'length' not in data and 'x' in graph.nodes[u] and 'y' in graph.nodes[u] and 'x' in graph.nodes[v] and 'y' in graph.nodes[v]:
                            import math
                            dx = graph.nodes[u]['x'] - graph.nodes[v]['x']
                            dy = graph.nodes[u]['y'] - graph.nodes[v]['y']
                            data['length'] = math.sqrt(dx*dx + dy*dy) * 100000  # Approx meters
                elif attr == 'travel_time':
                    for u, v, data in graph.edges(data=True):
                        if 'travel_time' not in data and 'length' in data and 'speed_kph' in data and data['speed_kph'] > 0:
                            data['travel_time'] = (data['length'] / 1000) / float(data['speed_kph']) * 3600
        
        print("\n6. Final edge attributes:")
        for i, (u, v, data) in enumerate(graph.edges(data=True)):
            if i >= 2:  # Only show first 2 edges
                break
            print(f"   Edge {u} -> {v}:")
            for k, v in data.items():
                print(f"     {k}: {v}")
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nStack trace:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
