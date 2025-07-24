import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import requests
import time
import threading
from visualization import plot_traffic_graph

ox.settings.log_console = True

def get_traffic_data(lat, lng, api_key):
    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
    params = {
        "point": f"{lat},{lng}",
        "key": api_key
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching traffic data: {response.status_code}", flush=True)
        print(f"Response: {response.text}", flush=True)
        return None

def get_road_network(city_name: str) -> nx.MultiDiGraph:
    """
    Loads the drivable road network for a specific city using OSMNX.

    Args:
        city_name: The name of the city (e.g., "Kathmandu, Nepal").

    Returns:
        A directed graph where nodes are intersections and edges are road segments.
    """
    print(f"Loading road network for {city_name}...", flush=True)
    # Get the road network for the specified city
    # 'drive' network type includes all drivable roads
    graph = ox.graph_from_place(city_name, network_type='drive')
    print(f"Successfully loaded graph for {city_name}.", flush=True)
    print(f"Graph has {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges.", flush=True)
    return graph

def update_graph_with_traffic(G, midpoints, api_key):
    print("\nUpdating graph with real-time traffic data...", flush=True)
    updated_edges = 0
    for point in midpoints:
        data = get_traffic_data(point["lat"], point["lng"], api_key)
        if data and "flowSegmentData" in data:
            flow = data["flowSegmentData"]
            u, v, key = point["u"], point["v"], point["key"]
            G[u][v][key]["currentSpeed"] = flow.get("currentSpeed")
            G[u][v][key]["freeFlowSpeed"] = flow.get("freeFlowSpeed")
            
            free_flow_speed = flow.get("freeFlowSpeed", 0)
            if free_flow_speed > 0:
                congestion = flow.get("currentSpeed", 0) / free_flow_speed
            else:
                congestion = 1.0  # Assume max congestion if freeFlowSpeed is 0 or not available
            G[u][v][key]["congestion"] = congestion
            updated_edges += 1
    print(f"Successfully updated {updated_edges} edges with traffic data.", flush=True)

def refresh_traffic_data(graph, api_key):
    """Periodically fetches traffic data and updates the graph visualization."""
    while True:
        print("\nRefreshing traffic data...", flush=True)
        midpoints = get_edge_midpoints(graph)
        if midpoints:
            update_graph_with_traffic(graph, midpoints, api_key)
            plot_traffic_graph(graph)
        else:
            print("No midpoints found, skipping update.", flush=True)
        
        print("\nNext update in 5 minutes.", flush=True)
        time.sleep(300)  # Wait for 5 minutes (300 seconds)

def get_edge_midpoints(G):
    coords = []
    for u, v, key, data in G.edges(keys=True, data=True):
        if "geometry" in data:
            midpoint = data["geometry"].interpolate(0.5, normalized=True)
            coords.append({
                "u": u, "v": v, "key": key,
                "lat": midpoint.y, "lng": midpoint.x
            })
    return coords

if __name__ == '__main__':
    city = "Patan, Nepal"
    api_key = "tEZ8WgFXLuAuDjHmB3AB5y89ue31PsGL"  # Your TomTom API key

    try:
        # Get the road network graph
        city_graph = get_road_network(city)

        # Initial plot
        print("\nPerforming initial data load and plot...", flush=True)
        initial_midpoints = get_edge_midpoints(city_graph)
        if initial_midpoints:
            update_graph_with_traffic(city_graph, initial_midpoints, api_key)
            plot_traffic_graph(city_graph)
        else:
            print("No midpoints found for initial plot.", flush=True)

        # Start the background thread for continuous updates
        update_thread = threading.Thread(
            target=refresh_traffic_data, 
            args=(city_graph, api_key),
            daemon=True
        )
        update_thread.start()

        print("\nApplication is running. Close the plot window to exit.", flush=True)
        # Keep the main thread alive to allow the daemon thread to run
        while update_thread.is_alive():
            time.sleep(1)

    except Exception as e:
        print(f"An error occurred: {e}", flush=True)
