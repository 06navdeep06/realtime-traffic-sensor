import networkx as nx
from typing import Dict, Tuple
from rl_agent import QLearningAgent
import logging

logger = logging.getLogger(__name__)

class TrafficSignal:
    """
    An intelligent traffic signal controller using a Q-learning agent.
    """
    def __init__(self, intersection_id: int, graph: nx.MultiDiGraph):
        if not isinstance(intersection_id, int):
            raise ValueError(f"intersection_id must be an integer, got {type(intersection_id)}")
        if not isinstance(graph, (nx.MultiDiGraph, nx.DiGraph)):
            raise ValueError(f"Expected MultiDiGraph or DiGraph, got {type(graph)}")
        if intersection_id not in graph.nodes:
            raise ValueError(f"Node {intersection_id} not found in graph")
            
        self.id = intersection_id
        self.intersection_node = intersection_id  # Add alias for compatibility
        
        # The action space is the set of incoming roads to turn green.
        # An 'action' is the index into this list.
        self.incoming_lanes = list(graph.in_edges(self.id))
        
        if not self.incoming_lanes:
            logger.warning(f"No incoming lanes found for intersection {intersection_id}")
            
        action_space = list(range(len(self.incoming_lanes)))
        if not action_space:
            action_space = [0]  # Default action space if no incoming lanes
        
        try:
            self.agent = QLearningAgent(action_space=action_space)
        except Exception as e:
            logger.error(f"Failed to create QLearningAgent for intersection {intersection_id}: {e}")
            # Create a dummy agent that always returns action 0
            self.agent = None
            
        self.green_lane_index = 0  # Default to the first lane being green
        self.last_state = None
        self.last_action = None

    def _get_state(self, graph: nx.MultiDiGraph) -> Tuple[int, ...]:
        """
        Get the current state of the intersection based on real-time congestion data.
        Discretizes congestion to keep the state space manageable.
        State is a tuple of discretized congestion values for each incoming lane.
        """
        if not self.incoming_lanes:
            return (0,)  # Default state if no incoming lanes
            
        state = []
        for u, v in self.incoming_lanes:
            try:
                # Default to 0 congestion if no data is available
                edge_data = graph.get_edge_data(u, v, 0)
                if edge_data is None:
                    congestion = 0.0
                else:
                    congestion = edge_data.get('congestion', 0.0)
                    
                # Ensure congestion is a valid number
                if not isinstance(congestion, (int, float)) or congestion < 0:
                    congestion = 0.0
                elif congestion > 1:
                    congestion = 1.0
            except Exception as e:
                logger.warning(f"Error getting congestion data for edge {u}->{v}: {e}")
                congestion = 0.0
            
            # Discretize congestion: 0=low, 1=medium, 2=high, 3=very high
            if congestion < 0.3:
                discretized_congestion = 0
            elif congestion < 0.6:
                discretized_congestion = 1
            elif congestion < 0.9:
                discretized_congestion = 2
            else:
                discretized_congestion = 3
            state.append(discretized_congestion)
        return tuple(state)

    def update(self, graph: nx.MultiDiGraph, vehicle_queues: Dict[Tuple[int, int], int]):
        """
        Update the agent and the signal state.
        This is the core logic loop for the RL agent.
        """
        if not self.agent:
            return  # Skip update if agent creation failed
            
        try:
            current_state = self._get_state(graph)
            if not current_state:
                return
            
            # The reward is the negative sum of waiting vehicles on red lanes
            reward = 0
            for i, lane in enumerate(self.incoming_lanes):
                if i != self.green_lane_index and lane:
                    # Handle both (u, v) and (u, v, key) formats in vehicle_queues
                    queue_key = lane
                    if len(lane) >= 2 and lane[:2] in vehicle_queues:
                        queue_key = lane[:2]
                    queue_count = vehicle_queues.get(queue_key, 0)
                    if isinstance(queue_count, (int, float)) and queue_count >= 0:
                        reward -= queue_count

            # Update Q-table with the experience from the last step
            if self.last_state is not None and self.last_action is not None:
                success = self.agent.update_q_table(self.last_state, self.last_action, reward, current_state)
                if not success:
                    logger.warning(f"Failed to update Q-table for intersection {self.id}")

            # Choose the next action (which lane to make green)
            action = self.agent.get_action(current_state)
            
            # Validate action
            if isinstance(action, int) and 0 <= action < len(self.incoming_lanes):
                self.green_lane_index = action
            else:
                logger.warning(f"Invalid action {action} for intersection {self.id}, using default")
                self.green_lane_index = 0
            
            # Store current state and action for the next update
            self.last_state = current_state
            self.last_action = self.green_lane_index
            
        except Exception as e:
            logger.error(f"Error in TrafficSignal.update for intersection {self.id}: {str(e)}")
            if logger.isEnabledFor(logging.DEBUG):
                import traceback
                logger.debug(traceback.format_exc())

    def is_green(self, lane) -> bool:
        """
        Check if a specific incoming lane has a green light.
        
        Args:
            lane: Can be either a tuple of (u, v) or (u, v, key) representing the edge
            
        Returns:
            bool: True if the lane has a green light, False otherwise
        """
        if not self.incoming_lanes:
            return True  # No signals if no incoming lanes
            
        if not lane or not isinstance(lane, tuple) or len(lane) < 2:
            return False  # Invalid lane format
            
        # Ensure green_lane_index is valid
        if not (0 <= self.green_lane_index < len(self.incoming_lanes)):
            logger.warning(f"Invalid green_lane_index {self.green_lane_index} for intersection {self.id}")
            self.green_lane_index = 0
            
        try:
            # Handle both (u, v) and (u, v, key) formats for backward compatibility
            lane_to_check = lane[:2]  # Just use (u, v) part for comparison
            current_green = self.incoming_lanes[self.green_lane_index]
            
            # Compare (u, v) parts
            return (lane_to_check[0] == current_green[0] and 
                    lane_to_check[1] == current_green[1])
        except (IndexError, TypeError) as e:
            logger.warning(f"Error checking green light for lane {lane} at intersection {self.id}: {e}")
            return False
            
    @property
    def current_state(self):
        """Get a string representation of the current signal state."""
        if not self.incoming_lanes:
            return "No lanes"
        if 0 <= self.green_lane_index < len(self.incoming_lanes):
            green_lane = self.incoming_lanes[self.green_lane_index]
            return f"Green: {green_lane[0]}->{green_lane[1]}"
        return "Invalid state"
        
    @property
    def node_id(self):
        """Alias for intersection_id for compatibility."""
        return self.id
