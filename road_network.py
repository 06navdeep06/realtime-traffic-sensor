import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import requests
import time
import threading
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure OSMnx settings
ox.settings.log_console = True
ox.settings.use_cache = True
ox.settings.timeout = 180  # Increase timeout for large queries

logger = logging.getLogger(__name__)

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
    # Validate inputs
    try:
        lat = float(lat)
        lng = float(lng)
        if not (-90 <= lat <= 90):
            logger.error(f"Invalid latitude: {lat}")
            return None
        if not (-180 <= lng <= 180):
            logger.error(f"Invalid longitude: {lng}")
            return None
    except (ValueError, TypeError):
        logger.error(f"Invalid coordinates: lat={lat}, lng={lng}")
        return None
        
    if api_key is None:
        api_key = os.getenv('TOMTOM_API_KEY')
        if not api_key:
            logger.error("TOMTOM_API_KEY environment variable not set")
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
                
                # Validate response
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        return data
                    else:
                        logger.warning(f"Invalid JSON response format: {type(data)}")
                        return None
                except ValueError as e:
                    logger.warning(f"Invalid JSON response: {e}")
                    return None
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:  # Last attempt
                    logger.error(f"Error fetching traffic data after {max_retries} attempts: {e}")
                    return None
                logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(1)  # Wait before retry
                
    except Exception as e:
        logger.error(f"Unexpected error in get_traffic_data: {e}")
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
    if not location_query or not isinstance(location_query, str):
        raise ValueError(f"Invalid location_query: {location_query}")
    if not isinstance(distance, int) or distance <= 0:
        raise ValueError(f"Distance must be a positive integer, got {distance}")
        
    logger.info(f"Loading road network for {location_query}...")
    
    # List of fallback locations to try if the primary location fails
    fallback_locations = ["27.7172, 85.3240"]  # Kathmandu coordinates
    
    # Try the primary location first, then fallbacks
    for i, loc in enumerate([location_query] + fallback_locations):
        try:
            if i > 0:  # Only print fallback message for fallback attempts
                logger.info(f"Attempting fallback location: {loc}")
                
            # Check if the input is coordinates
            if ',' in loc:
                try:
                    parts = loc.split(',')
                    if len(parts) == 2:
                        lat, lon = map(float, [p.strip() for p in parts])
                        # Validate coordinates
                        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                            raise ValueError(f"Invalid coordinates: {lat}, {lon}")
                    else:
                        raise ValueError(f"Invalid coordinate format: {loc}")
                except ValueError:
                    # Not valid coordinates, treat as place name
                    lat, lon = None, None
            else:
                lat, lon = None, None
                
            if lat is not None and lon is not None:
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
            
            logger.info(f"Successfully loaded graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges.")
                
            # Ensure all edges have required attributes
            for u, v, data in graph.edges(data=True):
                if not isinstance(data, dict):
                    logger.warning(f"Invalid edge data for {u}->{v}: {data}")
                    continue
                    
                # Set default maxspeed if missing (in km/h)
                if 'maxspeed' not in data:
                    # Default speed limits based on road type (in km/h)
                    highway_type = data.get('highway', '')
                    if isinstance(highway_type, list):
                        highway_type = highway_type[0] if highway_type else ''
                    
                    # Set default speeds based on road type
                    if 'motorway' in str(highway_type):
                        default_speed = 100
                    elif 'trunk' in str(highway_type):
                        default_speed = 80
                    elif 'primary' in str(highway_type):
                        default_speed = 60
                    elif 'secondary' in str(highway_type):
                        default_speed = 50
                    elif 'tertiary' in str(highway_type):
                        default_speed = 40
                    elif 'residential' in str(highway_type):
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
                            speed_value = float(maxspeed)
                            if speed_value > 0:
                                data['speed_kph'] = speed_value
                            else:
                                data['speed_kph'] = 40.0
                        else:
                            data['speed_kph'] = 40.0  # Default speed
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Could not parse maxspeed '{data.get('maxspeed')}': {e}")
                        data['speed_kph'] = 40.0  # Fallback default speed
                
                # Ensure length is set and is a number
                if 'length' not in data or not isinstance(data['length'], (int, float)) or data['length'] <= 0:
                    # Calculate length from node coordinates if not set or invalid
                    try:
                        if u in graph.nodes and v in graph.nodes:
                            u_node = graph.nodes[u]
                            v_node = graph.nodes[v]
                            if 'x' in u_node and 'y' in u_node and 'x' in v_node and 'y' in v_node:
                                u_coords = (u_node['y'], u_node['x'])
                                v_coords = (v_node['y'], v_node['x'])
                                calculated_length = ox.distance.great_circle_vec(
                                    u_coords[0], u_coords[1], v_coords[0], v_coords[1]
                                )
                                if calculated_length > 0:
                                    data['length'] = calculated_length
                                else:
                                    data['length'] = 100.0
                            else:
                                data['length'] = 100.0
                        else:
                            data['length'] = 100.0
                    except Exception as e:
                        logger.warning(f"Could not calculate edge length for {u}->{v}: {e}")
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
                        logger.warning(f"Could not calculate travel time for {u}->{v}: {e}")
                        data['travel_time'] = 10.0  # Default travel time
            
            logger.info(f"Successfully processed graph attributes for {loc}.")
            return graph
            
        except Exception as e:
            if i == len(fallback_locations):  # Last attempt
                raise ValueError(f"Failed to load road network for any location. Last error: {str(e)}")
            logger.warning(f"Error loading road network for {loc}: {str(e)}")
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
    if not isinstance(G, (nx.MultiDiGraph, nx.DiGraph)):
        logger.error(f"Invalid graph type: {type(G)}")
        return 0
        
    if not midpoints:
        logger.warning("No midpoints provided for traffic data update.")
        return 0
        
    logger.info("Updating graph with real-time traffic data...")
    updated_edges = 0
    total_edges = len(midpoints)
    
    for i, point in enumerate(midpoints, 1):
        try:
            if not isinstance(point, dict):
                logger.warning(f"Invalid midpoint format: {point}")
                continue
                
            lat = point.get("lat")
            lng = point.get("lng")
            if lat is None or lng is None:
                logger.warning(f"Missing coordinates in midpoint: {point}")
                continue
                
            data = get_traffic_data(point.get("lat"), point.get("lng"), api_key)
            if not data or "flowSegmentData" not in data:
                continue
                
            flow = data["flowSegmentData"]
            if not isinstance(flow, dict):
                logger.warning(f"Invalid flow data format: {flow}")
                continue
                
            u, v, key = point.get("u"), point.get("v"), point.get("key", 0)
            
            if u is None or v is None:
                logger.warning(f"Missing edge information in midpoint: {point}")
                continue
            
            # Skip if edge doesn't exist in the graph
            if u not in G or v not in G[u] or key not in G[u][v]:
                continue
                
            # Update edge attributes
            current_speed = flow.get("currentSpeed")
            free_flow_speed = flow.get("freeFlowSpeed")
            
            # Safely calculate congestion with division by zero protection
            if (isinstance(free_flow_speed, (int, float)) and free_flow_speed > 0 and 
                isinstance(current_speed, (int, float)) and current_speed >= 0):
                congestion = min(1.0, max(0.0, 1.0 - (current_speed / free_flow_speed)))
            else:
                congestion = 0.5  # Default to medium congestion if data is missing
                
            # Update edge attributes
            G[u][v][key]["currentSpeed"] = current_speed
            G[u][v][key]["freeFlowSpeed"] = free_flow_speed
            G[u][v][key]["congestion"] = congestion
            
            updated_edges += 1
            
            # Print progress every 10% of edges
            if i % max(1, total_edges // 10) == 0:
                logger.info(f"  Updated {i}/{total_edges} edges...")
                
        except Exception as e:
            logger.warning(f"Error updating edge {i}: {str(e)}")
            continue
            
    logger.info(f"Successfully updated {updated_edges}/{total_edges} edges with traffic data.")
    return updated_edges

def refresh_traffic_data(graph, api_key):
    """Periodically fetches traffic data and updates the graph visualization."""
    if not isinstance(graph, (nx.MultiDiGraph, nx.DiGraph)):
        logger.error("Invalid graph for traffic data refresh")
        return
        
    while True:
        try:
            logger.info("Refreshing traffic data...")
            midpoints = get_edge_midpoints(graph)
            if midpoints:
                update_graph_with_traffic(graph, midpoints, api_key)
                # Import here to avoid circular imports
                try:
                    from visualization import plot_traffic_graph
                    plot_traffic_graph(graph)
                except ImportError:
                    logger.warning("Could not import visualization module")
            else:
                logger.warning("No midpoints found, skipping update.")
            
            logger.info("Next update in 5 minutes.")
            time.sleep(300)  # Wait for 5 minutes (300 seconds)
        except Exception as e:
            logger.error(f"Error in refresh_traffic_data: {e}")
            time.sleep(60)  # Wait 1 minute before retrying

def get_edge_midpoints(G):
    """Get midpoints of edges for traffic data queries."""
    if not isinstance(G, (nx.MultiDiGraph, nx.DiGraph)):
        logger.error(f"Invalid graph type: {type(G)}")
        return []
        
    coords = []
    try:
        for u, v, key, data in G.edges(keys=True, data=True):
            if not isinstance(data, dict):
                continue
                
            if "geometry" in data and data["geometry"] is not None:
                try:
                    midpoint = data["geometry"].interpolate(0.5, normalized=True)
                    if hasattr(midpoint, 'y') and hasattr(midpoint, 'x'):
                        coords.append({
                            "u": u, "v": v, "key": key,
                            "lat": midpoint.y, "lng": midpoint.x
                        })
                except Exception as e:
                    logger.warning(f"Error getting midpoint for edge {u}->{v}: {e}")
            else:
                # Use node coordinates as fallback
                try:
                    if (u in G.nodes and v in G.nodes and 
                        'x' in G.nodes[u] and 'y' in G.nodes[u] and
                        'x' in G.nodes[v] and 'y' in G.nodes[v]):
                        
                        u_x, u_y = G.nodes[u]['x'], G.nodes[u]['y']
                        v_x, v_y = G.nodes[v]['x'], G.nodes[v]['y']
                        mid_x = (u_x + v_x) / 2
                        mid_y = (u_y + v_y) / 2
                        
                        coords.append({
                            "u": u, "v": v, "key": key,
                            "lat": mid_y, "lng": mid_x
                        })
                except Exception as e:
                    logger.warning(f"Error calculating midpoint for edge {u}->{v}: {e}")
    except Exception as e:
        logger.error(f"Error in get_edge_midpoints: {e}")
        
    return coords

if __name__ == '__main__':
    city = "Patan, Nepal"
    api_key = "tEZ8WgFXLuAuDjHmB3AB5y89ue31PsGL"  # Your TomTom API key

    try:
        # Get the road network graph
        city_graph = get_road_network(city)

        # Initial plot
        logger.info("Performing initial data load and plot...")
        initial_midpoints = get_edge_midpoints(city_graph)
        if initial_midpoints:
            update_graph_with_traffic(city_graph, initial_midpoints, api_key)
            try:
                from visualization import plot_traffic_graph
                plot_traffic_graph(city_graph)
            except ImportError:
                logger.warning("Could not import visualization module")
        else:
            logger.warning("No midpoints found for initial plot.")

        # Start the background thread for continuous updates
        update_thread = threading.Thread(
            target=refresh_traffic_data, 
            args=(city_graph, api_key),
            daemon=True
        )
        update_thread.start()

        logger.info("Application is running. Close the plot window to exit.")
        # Keep the main thread alive to allow the daemon thread to run
        while update_thread.is_alive():
            time.sleep(1)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
