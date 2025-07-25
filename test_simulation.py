import os
import sys
import time
import networkx as nx
import matplotlib.pyplot as plt
from road_network import get_road_network, update_graph_with_traffic, get_edge_midpoints

# Suppress some of the verbose logging
import logging
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('osmnx').setLevel(logging.WARNING)


def test_api():
    # Set the API key in the environment
    os.environ['TOMTOM_API_KEY'] = 'tEZ8WgFXLuAuDjHmB3AB5y89ue31PsGL'
    
    print("🚦 Testing Traffic Simulation Setup 🚦")
    print("=" * 50)
    
    try:
        # 1. Test road network loading
        print("\n1. Testing road network loading...")
        location = "27.7172, 85.3240"  # Kathmandu coordinates
        print(f"   - Fetching road network for {location}")
        graph = get_road_network(location, distance=300)  # Small area for testing
        
        if graph is None or len(graph.nodes()) == 0:
            print("❌ Failed to fetch road network.")
            return False
            
        print(f"   ✅ Success! Graph has {len(graph.nodes())} nodes and {len(graph.edges())} edges.")
        
        # 2. Test traffic data fetching
        print("\n2. Testing traffic data fetching...")
        try:
            # Get midpoints of a few edges
            midpoints = list(get_edge_midpoints(graph))[:5]  # Just test first 5 edges
            if not midpoints:
                print("   ⚠️ No edges found to test traffic data.")
                return True
                
            print(f"   - Updating traffic data for {len(midpoints)} edges...")
            updated = update_graph_with_traffic(graph, midpoints, os.environ['TOMTOM_API_KEY'])
            
            if updated > 0:
                print(f"   ✅ Success! Updated {updated} edges with traffic data.")
                
                # Show some sample traffic data
                print("\nSample Traffic Data:")
                print("-" * 50)
                for u, v, data in graph.edges(data=True):
                    if 'currentSpeed' in data:
                        print(f"Edge {u} -> {v}:")
                        print(f"  - Current Speed: {data.get('currentSpeed')} km/h")
                        print(f"  - Free Flow Speed: {data.get('freeFlowSpeed')} km/h")
                        print(f"  - Congestion: {data.get('congestion', 0):.1%}")
                        print("-" * 50)
                        break
                
                return True
            else:
                print("   ⚠️ No traffic data was updated. This might be normal if the area has no traffic data.")
                return True
                
        except Exception as e:
            print(f"   ❌ Error testing traffic data: {str(e)}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error in test_api: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_api()
