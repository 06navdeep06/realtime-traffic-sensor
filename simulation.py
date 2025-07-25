import random
import networkx as nx
from typing import List, Dict
from collections import defaultdict
from traffic_signal import TrafficSignal
import logging

# Configure logger
logger = logging.getLogger(__name__)

class Vehicle:
    """
    Represents a single vehicle in the simulation.
    """
    def __init__(self, vehicle_id: int, source: int, destination: int, path: List[int], start_step: int):
        self.vehicle_id = vehicle_id
        self.source = source
        self.destination = destination
        self.path = path if path else []
        self.current_node_index = 0
        self.start_step = start_step
        self.end_step = -1  # -1 indicates not finished
        self._current_edge = None  # Track the current edge the vehicle is on
        
        # Validate inputs
        if not isinstance(vehicle_id, int):
            raise ValueError(f"vehicle_id must be an integer, got {type(vehicle_id)}")
        if not self.path or len(self.path) < 2:
            raise ValueError(f"Path must have at least 2 nodes, got {self.path}")

    @property
    def current_location(self) -> int:
        """Return the current node the vehicle is at."""
        if not self.path or self.current_node_index >= len(self.path):
            return None
        return self.path[self.current_node_index]
        
    @property
    def current_edge(self):
        """Return the current edge the vehicle is on as (u, v, key)."""
        if (self._current_edge is None and 
            self.path and 
            self.current_node_index < len(self.path) - 1 and
            self.current_node_index >= 0):
            # If no current edge but path is valid, set the current edge
            self._current_edge = (self.path[self.current_node_index], 
                                self.path[self.current_node_index + 1], 
                                0)  # Default key for OSMnx
        return self._current_edge

    @property
    def is_active(self) -> bool:
        """Check if the vehicle has reached its destination."""
        return self.end_step == -1

    def move(self, traffic_signals: Dict[int, TrafficSignal], current_step: int):
        """Move the vehicle to the next node if the path is clear."""
        if not self.is_active or not self.path:
            return

        # Check if vehicle has reached the destination in this step
        if self.current_node_index >= len(self.path) - 1:
            self.end_step = current_step
            self._current_edge = None
            return

        current_node = self.current_location
        if current_node is None:
            logger.error(f"Vehicle {self.vehicle_id} has invalid current location")
            self.end_step = current_step
            return
            
        next_node = self.path[self.current_node_index + 1]
        
        # Update current edge
        self._current_edge = (current_node, next_node, 0)  # OSMNX uses 0 as default key

        # Check if the next node is an intersection with a traffic signal
        if next_node in traffic_signals and traffic_signals[next_node]:
            try:
                if not traffic_signals[next_node].is_green(self._current_edge):
                    return  # Stop for red light
            except Exception as e:
                logger.warning(f"Error checking traffic signal for vehicle {self.vehicle_id}: {e}")
                return  # Stop for red light

        # Move to the next node
        self.current_node_index += 1
        
        # Check if vehicle has reached the destination after moving
        if self.current_node_index >= len(self.path) - 1:
            self.end_step = current_step
            self._current_edge = None

    def __repr__(self):
        return (
            f"Vehicle(id={self.vehicle_id}, "
            f"source={self.source}, "
            f"destination={self.destination}, "
            f"current_location={self.current_location})"
        )

class Simulation:
    """Manages the state and progression of the traffic simulation."""
    def __init__(self, graph: nx.MultiDiGraph, num_vehicles: int):
        if not isinstance(graph, (nx.MultiDiGraph, nx.DiGraph)):
            raise ValueError(f"Expected MultiDiGraph or DiGraph, got {type(graph)}")
        if num_vehicles <= 0:
            raise ValueError(f"num_vehicles must be positive, got {num_vehicles}")
            
        self.graph = graph
        self.nodes = list(graph.nodes)
        
        if not self.nodes:
            raise ValueError("Graph has no nodes")
            
        self.num_vehicles = num_vehicles
        self.step_count = 0
        self.completed_trip_times = []

        # 1. Identify intersections and create RL-controlled traffic signals
        self.intersections = {node for node, degree in graph.degree() if degree > 2}
        self.traffic_signals = {}
        
        for node in self.intersections:
            try:
                self.traffic_signals[node] = TrafficSignal(node, graph)
            except Exception as e:
                logger.warning(f"Failed to create traffic signal for node {node}: {e}")

        # 2. Create vehicles
        self.vehicles: Dict[int, Vehicle] = {}
        created_vehicles = 0
        max_attempts = num_vehicles * 3  # Prevent infinite loops
        attempts = 0
        
        while created_vehicles < num_vehicles and attempts < max_attempts:
            try:
                self._create_vehicle(created_vehicles)
                created_vehicles += 1
            except Exception as e:
                logger.warning(f"Failed to create vehicle {created_vehicles}: {e}")
            attempts += 1
            
        if created_vehicles < num_vehicles:
            logger.warning(f"Only created {created_vehicles}/{num_vehicles} vehicles")
            
    def add_vehicle(self, vehicle: Vehicle):
        """Add a vehicle to the simulation."""
        if not isinstance(vehicle, Vehicle):
            raise ValueError(f"Expected Vehicle instance, got {type(vehicle)}")
        self.vehicles[vehicle.vehicle_id] = vehicle

    def _create_vehicle(self, vehicle_id: int):
        """Creates a single vehicle with a random source and destination."""
        if len(self.nodes) < 2:
            raise ValueError("Need at least 2 nodes to create vehicles")
            
        source, destination = random.sample(self.nodes, 2)
        try:
            path = nx.dijkstra_path(self.graph, source, destination, weight='length')
            if len(path) < 2:
                raise ValueError(f"Path too short: {path}")
                
            self.vehicles[vehicle_id] = Vehicle(
                vehicle_id=vehicle_id, 
                source=source, 
                destination=destination, 
                path=path, 
                start_step=self.step_count
            )
        except (nx.NetworkXNoPath, ValueError) as e:
            # Try with different nodes
            if len(self.nodes) >= 2:
                available_nodes = [n for n in self.nodes if n != source]
                if available_nodes:
                    destination = random.choice(available_nodes)
                    try:
                        path = nx.dijkstra_path(self.graph, source, destination, weight='length')
                        if len(path) >= 2:
                            self.vehicles[vehicle_id] = Vehicle(
                                vehicle_id=vehicle_id, 
                                source=source, 
                            return
                    except nx.NetworkXNoPath:
                        pass
            raise ValueError(f"Could not create valid path for vehicle {vehicle_id}")

    def step(self):
        """Advance the simulation by one time step."""
        self.step_count += 1
        
        try:
            # A. Calculate vehicle queues for all incoming lanes at intersections
            vehicle_queues = defaultdict(int)
            for vehicle in self.vehicles.values():
                if not vehicle or not vehicle.is_active or not vehicle.path:
                    continue
                    
                try:
                    if (vehicle.current_node_index < len(vehicle.path) - 1 and 
                        vehicle.current_node_index >= 0):
                        current_node = vehicle.current_location
                        if current_node is None:
                            continue
                        next_node = vehicle.path[vehicle.current_node_index + 1]
                        
                        # Create both (u, v) and (u, v, key) versions for compatibility
                        lane_with_key = (current_node, next_node, 0)  # OSMnx default key
                        lane_without_key = (current_node, next_node)
                        
                        if next_node in self.intersections:
                            vehicle_queues[lane_with_key] += 1
                            vehicle_queues[lane_without_key] += 1  # For backward compatibility
                except Exception as e:
                    logger.error(f"Error processing vehicle {getattr(vehicle, 'vehicle_id', 'unknown')} in queue calculation: {str(e)}")

            # B. Update all traffic signals based on the current graph state and queues
            for node_id, signal in self.traffic_signals.items():
                if not signal:
                    continue
                try:
                    signal.update(self.graph, vehicle_queues)
                except Exception as e:
                    logger.error(f"Error updating traffic signal at node {node_id}: {str(e)}")

            # C. Move vehicles and calculate edge congestion
            active_vehicles = 0
            edge_congestion = defaultdict(int)
            
            for vid, vehicle in list(self.vehicles.items()):  # Create a list to avoid modification during iteration
                if not vehicle or not vehicle.is_active or not vehicle.path:
                    continue
                    
                try:
                    # Store previous state for debugging
                    prev_location = vehicle.current_location
                    prev_edge = getattr(vehicle, 'current_edge', None)
                    
                    # Move vehicle
                    vehicle.move(self.traffic_signals, self.step_count)
                    
                    # Log movement for debugging
                    if logger.isEnabledFor(logging.DEBUG) and prev_location != vehicle.current_location:
                        logger.debug(f"Vehicle {vid} moved from {prev_location} to {vehicle.current_location}")
                        logger.debug(f"  Previous edge: {prev_edge}, New edge: {getattr(vehicle, 'current_edge', None)}")

                    # If vehicle is still active after move, count it and its congestion
                    if vehicle.is_active:
                        active_vehicles += 1
                        if (vehicle.current_node_index < len(vehicle.path) - 1 and 
                            vehicle.current_node_index >= 0):
                            current_node = vehicle.current_location
                            if current_node is None:
                                continue
                            next_node = vehicle.path[vehicle.current_node_index + 1]
                            
                            # Update congestion for both edge formats
                            edge_with_key = (current_node, next_node, 0)
                            edge_without_key = (current_node, next_node)
                            edge_congestion[edge_with_key] += 1
                            edge_congestion[edge_without_key] += 1  # For backward compatibility
                    
                    # If vehicle just finished, record trip time
                    elif vehicle.end_step == self.step_count:
                        trip_time = vehicle.end_step - vehicle.start_step
                        if trip_time > 0:
                            self.completed_trip_times.append(trip_time)
                            logger.info(f"Vehicle {vid} completed trip in {trip_time} steps")
                        
                        # Optionally remove completed vehicles to save memory
                        # del self.vehicles[vid]
                        
                except Exception as e:
                    logger.error(f"Error moving vehicle {vid}: {str(e)}")
                    if logger.isEnabledFor(logging.DEBUG):
                        import traceback
                        logger.debug(traceback.format_exc())
                    
                    # Mark vehicle as inactive to prevent repeated errors
                    if vehicle:
                        vehicle.end_step = self.step_count
                    
        except Exception as e:
            logger.error(f"Error in simulation step {self.step_count}: {str(e)}")
            if logger.isEnabledFor(logging.DEBUG):
                import traceback
                logger.debug(traceback.format_exc())

        # D. Calculate metrics
        avg_trip_time = sum(self.completed_trip_times) / len(self.completed_trip_times) if self.completed_trip_times else 0
        signal_states = {}
        for nid, sig in self.traffic_signals.items():
            if sig and hasattr(sig, 'green_lane_index'):
                signal_states[nid] = str(sig.green_lane_index)
            else:
                signal_states[nid] = "N/A"

        return {
            "step": self.step_count,
            "active_vehicles": active_vehicles,
            "avg_trip_time": avg_trip_time,
            "edge_congestion": edge_congestion,
            "signal_states": signal_states
        }

def run_simulation(graph: nx.MultiDiGraph, num_vehicles: int, steps: int):
    """
    Initializes and runs the traffic simulation for a given number of steps.

    Args:
        graph: The road network graph.
        num_vehicles: The number of vehicles to simulate.
        steps: The number of time steps to run the simulation for.

    Yields:
        A dictionary containing the simulation state at each step.
    """
    if not isinstance(graph, (nx.MultiDiGraph, nx.DiGraph)):
        raise ValueError(f"Expected MultiDiGraph or DiGraph, got {type(graph)}")
    if num_vehicles <= 0:
        raise ValueError(f"num_vehicles must be positive, got {num_vehicles}")
    if steps <= 0:
        raise ValueError(f"steps must be positive, got {steps}")
        
    simulation = Simulation(graph, num_vehicles)
    for _ in range(steps):
        yield simulation.step()
