import networkx as nx
from typing import Dict, Tuple
from rl_agent import QLearningAgent

class TrafficSignal:
    """
    An intelligent traffic signal controller using a Q-learning agent.
    """
    def __init__(self, intersection_id: int, graph: nx.MultiDiGraph):
        self.id = intersection_id
        # The action space is the set of incoming roads to turn green.
        # An 'action' is the index into this list.
        self.incoming_lanes = list(graph.in_edges(self.id))
        action_space = list(range(len(self.incoming_lanes)))
        
        self.agent = QLearningAgent(action_space=action_space)
        self.green_lane_index = 0  # Default to the first lane being green
        self.last_state = None
        self.last_action = None

    def _get_state(self, graph: nx.MultiDiGraph) -> Tuple[int, ...]:
        """
        Get the current state of the intersection based on real-time congestion data.
        Discretizes congestion to keep the state space manageable.
        State is a tuple of discretized congestion values for each incoming lane.
        """
        state = []
        for u, v in self.incoming_lanes:
            # Default to 0 congestion if no data is available
            congestion = graph.get_edge_data(u, v, 0).get('congestion', 0.0)
            
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
        try:
            current_state = self._get_state(graph)
            
            # The reward is the negative sum of waiting vehicles on red lanes
            reward = 0
            for i, lane in enumerate(self.incoming_lanes):
                if i != self.green_lane_index:
                    # Handle both (u, v) and (u, v, key) formats in vehicle_queues
                    queue_key = lane
                    if len(lane) == 3 and lane[:2] in vehicle_queues:
                        queue_key = lane[:2]
                    reward -= vehicle_queues.get(queue_key, 0)

            # Update Q-table with the experience from the last step
            if self.last_state is not None:
                self.agent.update_q_table(self.last_state, self.last_action, reward, current_state)

            # Choose the next action (which lane to make green)
            action = self.agent.get_action(current_state)
            self.green_lane_index = action
            
            # Store current state and action for the next update
            self.last_state = current_state
            self.last_action = action
            
        except Exception as e:
            import logging
            logging.error(f"Error in TrafficSignal.update: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())

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
            
        # Handle both (u, v) and (u, v, key) formats for backward compatibility
        if isinstance(lane, tuple) and len(lane) >= 2:
            lane_to_check = lane[:2]  # Just use (u, v) part for comparison
            current_green = self.incoming_lanes[self.green_lane_index]
            
            # Compare (u, v) parts
            return (lane_to_check[0] == current_green[0] and 
                    lane_to_check[1] == current_green[1])
                    
        return False  # Invalid lane format
