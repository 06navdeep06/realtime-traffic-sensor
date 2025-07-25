"""
Debug script to load a road network using OSMnx and save it to a file.
This will help us inspect the network structure and attributes.
"""
import os
import osmnx as ox
import networkx as nx
import json

# Configuration
LOCATION = (27.7172, 85.3240)  # Kathmandu coordinates
DISTANCE = 500  # meters
OUTPUT_FILE = "debug_road_network.json"

def save_graph_to_file(graph, filename):
    """Save a NetworkX graph to a JSON file for inspection."""
    # Convert graph to a serializable format
    graph_data = {
        'directed': graph.is_directed(),
        'multigraph': graph.is_multigraph(),
        'graph': dict(graph.graph) if hasattr(graph, 'graph') else {},
        'nodes': [
            {
                'id': node_id,
                'data': {k: v for k, v in data.items() if isinstance(v, (str, int, float, bool, type(None)))}
            }
            for node_id, data in graph.nodes(data=True)
        ],
        'edges': [
            {
                'source': u,
                'target': v,
                'key': key,
                'data': {k: v for k, v in data.items() if isinstance(v, (str, int, float, bool, type(None)))}
            }
            for u, v, key, data in graph.edges(keys=True, data=True)
        ]
    }
    
    # Save to file
    with open(filename, 'w') as f:
        json.dump(graph_data, f, indent=2)
    
    print(f"Graph saved to {os.path.abspath(filename)}")

def main():
    print("="*80)
    print("DEBUG ROAD NETWORK LOADING")
    print("="*80)
    
    try:
        # Load the road network using OSMnx
        print(f"\n1. Loading road network for {LOCATION} (distance: {DISTANCE}m)")
        graph = ox.graph_from_point(
            LOCATION,
            dist=DISTANCE,
            network_type='drive',
            simplify=True,
            retain_all=True
        )
        
        if graph is None:
            print("ERROR: Failed to load road network (graph is None)")
            return
            
        # Add edge speeds and travel times
        print("\n2. Adding edge speeds and travel times...")
        graph = ox.speed.add_edge_speeds(graph)
        graph = ox.speed.add_edge_travel_times(graph)
        
        # Print basic info
        print(f"\n3. Graph information:")
        print(f"   - Type: {type(graph)}")
        print(f"   - Is directed: {isinstance(graph, nx.DiGraph)}")
        print(f"   - Is multigraph: {isinstance(graph, nx.MultiGraph) or isinstance(graph, nx.MultiDiGraph)}")
        print(f"   - Number of nodes: {graph.number_of_nodes()}")
        print(f"   - Number of edges: {graph.number_of_edges()}")
        
        # Check for required attributes
        print("\n4. Checking for required attributes:")
        required_attrs = ['length', 'speed_kph', 'travel_time']
        for attr in required_attrs:
            missing = sum(1 for u, v, data in graph.edges(data=True) if attr not in data)
            total = graph.number_of_edges()
            print(f"   - {attr}: {total - missing}/{total} edges have this attribute")
        
        # Save the graph to a file for inspection
        print(f"\n5. Saving graph to {OUTPUT_FILE}...")
        save_graph_to_file(graph, OUTPUT_FILE)
        
        # Print sample edges
        print("\n6. Sample edges:")
        for i, (u, v, data) in enumerate(graph.edges(data=True)):
            if i >= 2:  # Only show first 2 edges
                break
            print(f"   Edge {u} -> {v}:")
            for k, v in data.items():
                print(f"     {k}: {v}")
        
        print("\n✅ Debugging complete!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
