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
        self.end_step = -1 # -1 indicates not finished

    @property
    def current_location(self) -> int:
        """Return the current node the vehicle is at."""
        return self.path[self.current_node_index]

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
            return

        current_node = self.current_location
        next_node = self.path[self.current_node_index + 1]

        # Check if the next node is an intersection with a traffic signal
        if next_node in traffic_signals:
            # The lane is the edge from the current node to the next node
            current_lane = (current_node, next_node, 0) # OSMNX adds a 0 for the edge key
            if not traffic_signals[next_node].is_green(current_lane):
                return  # Stop for red light

        self.current_node_index += 1
        # Check if vehicle has reached the destination after moving
        if self.current_node_index >= len(self.path) - 1:
            self.end_step = current_step

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

        # A. Calculate vehicle queues for all incoming lanes at intersections
        vehicle_queues = defaultdict(int)
        for vehicle in self.vehicles.values():
            if vehicle.is_active and vehicle.current_node_index < len(vehicle.path) - 1:
                current_node = vehicle.current_location
                next_node = vehicle.path[vehicle.current_node_index + 1]
                if next_node in self.intersections:
                    lane = (current_node, next_node, 0)
                    vehicle_queues[lane] += 1

        # B. Update all traffic signals based on the current graph state and queues
        for signal in self.traffic_signals.values():
            signal.update(self.graph, vehicle_queues)

        # C. Move vehicles and calculate edge congestion
        active_vehicles = 0
        edge_congestion = defaultdict(int)
        for vehicle in self.vehicles.values():
            # Move vehicle
            vehicle.move(self.traffic_signals, self.step_count)

            # If vehicle is still active after move, count it and its congestion
            if vehicle.is_active:
                active_vehicles += 1
                if vehicle.current_node_index < len(vehicle.path) - 1:
                    current_node = vehicle.current_location
                    next_node = vehicle.path[vehicle.current_node_index + 1]
                    edge_congestion[(current_node, next_node)] += 1
            # If vehicle just finished, record trip time
            elif vehicle.end_step == self.step_count:
                self.completed_trip_times.append(vehicle.end_step - vehicle.start_step)

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
