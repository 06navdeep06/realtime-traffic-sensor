import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import requests
import time
import threading
import os
from dotenv import load_dotenv
from visualization import plot_traffic_graph

# Load environment variables from .env file
load_dotenv()

# Configure OSMnx settings
ox.settings.log_console = True
ox.settings.use_cache = True
ox.settings.timeout = 180  # Increase timeout for large queries

def get_traffic_data(lat, lng, api_key=None):
    """
    Fetch traffic data from TomTom API for a given latitude and longitude.
    
    Args:
        lat: Latitude of the point
        lng: Longitude of the point
        api_key: Optional API key (will use TOMTOM_API_KEY from environment if not provided)
        
    Returns:
        dict: Traffic data or None if the request fails
    """
    if api_key is None:
        api_key = os.getenv('TOMTOM_API_KEY')
        if not api_key:
            print("Error: TOMTOM_API_KEY environment variable not set", flush=True)
            return None
            
    url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
    
    try:
        params = {
            "point": f"{lat},{lng}",
            "key": api_key,
            "unit": "KMPH"
        }
        
        # Add timeout and retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()  # Raise HTTPError for bad responses
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:  # Last attempt
                    print(f"Error fetching traffic data after {max_retries} attempts: {e}", flush=True)
                    return None
                print(f"Attempt {attempt + 1} failed, retrying...", flush=True)
                time.sleep(1)  # Wait before retry
                
    except Exception as e:
        print(f"Unexpected error in get_traffic_data: {e}", flush=True)
        return None

def get_road_network(location_query: str, distance: int = 1000) -> nx.MultiDiGraph:
    """
    Loads the drivable road network for a specific location using OSMnx.
    This version is compatible with OSMnx 2.0.5 and doesn't use the speed module.

    Args:
        location_query: The name of the location (e.g., "Kathmandu, Nepal" or coordinates like "27.7172, 85.3240").
        distance: Distance in meters around the point/address to get the network for.

    Returns:
        A directed graph where nodes are intersections and edges are road segments.
        
    Raises:
        ValueError: If no road network can be loaded for the given location.
    """
    print(f"Loading road network for {location_query}...", flush=True)
    
    # List of fallback locations to try if the primary location fails
    fallback_locations = ["27.7172, 85.3240"]  # Kathmandu coordinates
    
    # Try the primary location first, then fallbacks
    for i, loc in enumerate([location_query] + fallback_locations):
        try:
            if i > 0:  # Only print fallback message for fallback attempts
                print(f"Attempting fallback location: {loc}", flush=True)
                
            # Check if the input is coordinates
            if ',' in loc and all(part.strip().replace('.', '').replace('-', '').isdigit() for part in loc.split(',')):
                lat, lon = map(float, loc.split(','))
                graph = ox.graph_from_point(
                    (lat, lon), 
                    dist=distance, 
                    network_type='drive',
                    simplify=True,
                    retain_all=True
                )
            else:
                # Try with a point-based search first
                try:
                    graph = ox.graph_from_address(
                        loc, 
                        dist=distance, 
                        network_type='drive',
                        simplify=True,
                        retain_all=True
                    )
                except Exception as e:
                    # Fall back to place query if address search fails
                    graph = ox.graph_from_place(
                        loc, 
                        network_type='drive',
                        simplify=True,
                        retain_all=True
                    )
            
            if graph is None or len(graph.nodes()) == 0:
                raise ValueError("No road network found for the specified location.")
            
            print(f"Successfully loaded graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges.", flush=True)
                
            # Ensure all edges have required attributes
            for u, v, data in graph.edges(data=True):
                # Set default maxspeed if missing (in km/h)
                if 'maxspeed' not in data:
                    # Default speed limits based on road type (in km/h)
                    highway_type = data.get('highway', '')
                    if isinstance(highway_type, list):
                        highway_type = highway_type[0] if highway_type else ''
                    
                    # Set default speeds based on road type
                    if 'motorway' in highway_type:
                        default_speed = 100
                    elif 'trunk' in highway_type:
                        default_speed = 80
                    elif 'primary' in highway_type:
                        default_speed = 60
                    elif 'secondary' in highway_type:
                        default_speed = 50
                    elif 'tertiary' in highway_type:
                        default_speed = 40
                    elif 'residential' in highway_type:
                        default_speed = 30
                    else:
                        default_speed = 40  # Default for other road types
                    
                    data['maxspeed'] = str(default_speed)
                
                # Set speed_kph from maxspeed
                if 'speed_kph' not in data:
                    try:
                        if 'maxspeed' in data:
                            # Handle cases where maxspeed might be a list or have multiple values
                            maxspeed = data['maxspeed']
                            if isinstance(maxspeed, list):
                                maxspeed = maxspeed[0]
                            if isinstance(maxspeed, str):
                                # Take the first number if there are multiple values
                                maxspeed = maxspeed.split(';')[0].strip()
                                maxspeed = maxspeed.split()[0]  # Take first part if there's a unit
                            data['speed_kph'] = float(maxspeed)
                        else:
                            data['speed_kph'] = 40.0  # Default speed
                    except (ValueError, TypeError) as e:
                        print(f"Warning: Could not parse maxspeed '{data.get('maxspeed')}': {e}", flush=True)
                        data['speed_kph'] = 40.0  # Fallback default speed
                
                # Ensure length is set and is a number
                if 'length' not in data or not isinstance(data['length'], (int, float)) or data['length'] <= 0:
                    # Calculate length from node coordinates if not set or invalid
                    try:
                        u_coords = (graph.nodes[u]['y'], graph.nodes[u]['x'])
                        v_coords = (graph.nodes[v]['y'], graph.nodes[v]['x'])
                        data['length'] = ox.distance.great_circle_vec(u_coords[0], u_coords[1], 
                                                                   v_coords[0], v_coords[1])
                    except Exception as e:
                        print(f"Warning: Could not calculate edge length: {e}", flush=True)
                        data['length'] = 100.0  # Default length in meters
                
                # Calculate travel time in seconds
                if 'travel_time' not in data and 'length' in data and 'speed_kph' in data:
                    try:
                        # Convert length to km, speed to km/h, then to hours, then to seconds
                        distance_km = data['length'] / 1000
                        speed_kmh = float(data['speed_kph'])
                        if speed_kmh > 0:
                            data['travel_time'] = (distance_km / speed_kmh) * 3600
                        else:
                            data['travel_time'] = 10.0  # Default travel time for zero/negative speed
                    except Exception as e:
                        print(f"Warning: Could not calculate travel time: {e}", flush=True)
                        data['travel_time'] = 10.0  # Default travel time
            
            print(f"Successfully processed graph attributes for {loc}.", flush=True)
            return graph
            
        except Exception as e:
            if i == len(fallback_locations):  # Last attempt
                raise ValueError(f"Failed to load road network for any location. Last error: {str(e)}")
            print(f"Error loading road network for {loc}: {str(e)}", flush=True)
            continue

def update_graph_with_traffic(G, midpoints, api_key=None):
    """
    Update the graph with real-time traffic data from the TomTom API.
    
    Args:
        G: The graph to update
        midpoints: List of dictionaries containing edge information and coordinates
        api_key: Optional API key (will use environment variable if not provided)
        
    Returns:
        int: Number of edges successfully updated
    """
    if not midpoints:
        print("No midpoints provided for traffic data update.", flush=True)
        return 0
        
    print("\nUpdating graph with real-time traffic data...", flush=True)
    updated_edges = 0
    total_edges = len(midpoints)
    
    for i, point in enumerate(midpoints, 1):
        try:
            data = get_traffic_data(point.get("lat"), point.get("lng"), api_key)
            if not data or "flowSegmentData" not in data:
                continue
                
            flow = data["flowSegmentData"]
            u, v, key = point.get("u"), point.get("v"), point.get("key", 0)
            
            # Skip if edge doesn't exist in the graph
            if u not in G or v not in G[u] or key not in G[u][v]:
                continue
                
            # Update edge attributes
            current_speed = flow.get("currentSpeed")
            free_flow_speed = flow.get("freeFlowSpeed")
            
            # Safely calculate congestion with division by zero protection
            if free_flow_speed and free_flow_speed > 0 and current_speed is not None:
                congestion = min(1.0, max(0.0, current_speed / free_flow_speed))
            else:
                congestion = 1.0  # Default to max congestion if data is missing
                
            # Update edge attributes
            G[u][v][key]["currentSpeed"] = current_speed
            G[u][v][key]["freeFlowSpeed"] = free_flow_speed
            G[u][v][key]["congestion"] = congestion
            
            updated_edges += 1
            
            # Print progress every 10% of edges
            if i % max(1, total_edges // 10) == 0:
                print(f"  Updated {i}/{total_edges} edges...", flush=True)
                
        except Exception as e:
            print(f"Error updating edge {i}: {str(e)}", flush=True)
            continue
            
    print(f"Successfully updated {updated_edges}/{total_edges} edges with traffic data.", flush=True)
    return updated_edges

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
