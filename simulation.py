import random
import networkx as nx
from typing import List, Dict
from collections import defaultdict
from traffic_signal import TrafficSignal
from visualization import plot_congestion_heatmap

class Vehicle:
    """
    Represents a single vehicle in the simulation.
    """
    def __init__(self, vehicle_id: int, source: int, destination: int, path: List[int], start_step: int):
        self.vehicle_id = vehicle_id
        self.source = source
        self.destination = destination
        self.path = path
        self.current_node_index = 0
        self.start_step = start_step
        self.end_step = -1  # -1 indicates not finished
        self._current_edge = None  # Track the current edge the vehicle is on

    @property
    def current_location(self) -> int:
        """Return the current node the vehicle is at."""
        if not self.path or self.current_node_index >= len(self.path):
            return None
        return self.path[self.current_node_index]
        
    @property
    def current_edge(self):
        """Return the current edge the vehicle is on as (u, v, key)."""
        if self._current_edge is None and self.current_node_index < len(self.path) - 1:
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
        if not self.is_active:
            return

        # Check if vehicle has reached the destination in this step
        if self.current_node_index >= len(self.path) - 1:
            self.end_step = current_step
            self._current_edge = None
            return

        current_node = self.current_location
        next_node = self.path[self.current_node_index + 1]
        
        # Update current edge
        self._current_edge = (current_node, next_node, 0)  # OSMNX uses 0 as default key

        # Check if the next node is an intersection with a traffic signal
        if next_node in traffic_signals:
            if not traffic_signals[next_node].is_green(self._current_edge):
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
        self.graph = graph
        self.nodes = list(graph.nodes)
        self.num_vehicles = num_vehicles
        self.step_count = 0
        self.completed_trip_times = []

        # 1. Identify intersections and create RL-controlled traffic signals
        self.intersections = {node for node, degree in graph.degree() if degree > 2}
        self.traffic_signals = {node: TrafficSignal(node, graph) for node in self.intersections}

        # 2. Create vehicles
        self.vehicles: Dict[int, Vehicle] = {}
        for i in range(num_vehicles):
            self._create_vehicle(i)

    def _create_vehicle(self, vehicle_id: int):
        """Creates a single vehicle with a random source and destination."""
        source, destination = random.sample(self.nodes, 2)
        try:
            path = nx.dijkstra_path(self.graph, source, destination, weight='length')
            self.vehicles[vehicle_id] = Vehicle(
                vehicle_id=vehicle_id, 
                source=source, 
                destination=destination, 
                path=path, 
                start_step=self.step_count
            )
        except nx.NetworkXNoPath:
            # Try again with a different destination
            self._create_vehicle(vehicle_id)

    def step(self):
        """Advance the simulation by one time step."""
        self.step_count += 1
        
        try:
            # A. Calculate vehicle queues for all incoming lanes at intersections
            vehicle_queues = defaultdict(int)
            for vehicle in self.vehicles.values():
                if not vehicle.is_active:
                    continue
                    
                try:
                    if vehicle.current_node_index < len(vehicle.path) - 1:
                        current_node = vehicle.current_location
                        next_node = vehicle.path[vehicle.current_node_index + 1]
                        
                        # Create both (u, v) and (u, v, key) versions for compatibility
                        lane_with_key = (current_node, next_node, 0)  # OSMnx default key
                        lane_without_key = (current_node, next_node)
                        
                        if next_node in self.intersections:
                            vehicle_queues[lane_with_key] += 1
                            vehicle_queues[lane_without_key] += 1  # For backward compatibility
                except Exception as e:
                    import logging
                    logging.error(f"Error processing vehicle {vehicle.vehicle_id} in queue calculation: {str(e)}")

            # B. Update all traffic signals based on the current graph state and queues
            for node_id, signal in self.traffic_signals.items():
                try:
                    signal.update(self.graph, vehicle_queues)
                except Exception as e:
                    import logging
                    logging.error(f"Error updating traffic signal at node {node_id}: {str(e)}")

            # C. Move vehicles and calculate edge congestion
            active_vehicles = 0
            edge_congestion = defaultdict(int)
            
            for vid, vehicle in list(self.vehicles.items()):  # Create a list to avoid modification during iteration
                if not vehicle.is_active:
                    continue
                    
                try:
                    # Store previous state for debugging
                    prev_location = vehicle.current_location
                    prev_edge = getattr(vehicle, 'current_edge', None)
                    
                    # Move vehicle
                    vehicle.move(self.traffic_signals, self.step_count)
                    
                    # Log movement for debugging
                    if prev_location != vehicle.current_location:
                        logging.debug(f"Vehicle {vid} moved from {prev_location} to {vehicle.current_location}")
                        logging.debug(f"  Previous edge: {prev_edge}, New edge: {getattr(vehicle, 'current_edge', None)}")

                    # If vehicle is still active after move, count it and its congestion
                    if vehicle.is_active:
                        active_vehicles += 1
                        if vehicle.current_node_index < len(vehicle.path) - 1:
                            current_node = vehicle.current_location
                            next_node = vehicle.path[vehicle.current_node_index + 1]
                            
                            # Update congestion for both edge formats
                            edge_with_key = (current_node, next_node, 0)
                            edge_without_key = (current_node, next_node)
                            edge_congestion[edge_with_key] += 1
                            edge_congestion[edge_without_key] += 1  # For backward compatibility
                    
                    # If vehicle just finished, record trip time
                    elif vehicle.end_step == self.step_count:
                        trip_time = vehicle.end_step - vehicle.start_step
                        self.completed_trip_times.append(trip_time)
                        logging.info(f"Vehicle {vid} completed trip in {trip_time} steps")
                        
                        # Optionally remove completed vehicles to save memory
                        # del self.vehicles[vid]
                        
                except Exception as e:
                    import logging
                    logging.error(f"Error moving vehicle {vid}: {str(e)}")
                    import traceback
                    logging.error(traceback.format_exc())
                    
                    # Mark vehicle as inactive to prevent repeated errors
                    vehicle.end_step = self.step_count
                    
        except Exception as e:
            import logging
            logging.error(f"Error in simulation step {self.step_count}: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())

        # D. Calculate metrics
        avg_trip_time = sum(self.completed_trip_times) / len(self.completed_trip_times) if self.completed_trip_times else 0
        signal_states = {nid: str(sig.green_lane_index) for nid, sig in self.traffic_signals.items()}

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
    simulation = Simulation(graph, num_vehicles)
    for _ in range(steps):
        yield simulation.step()
