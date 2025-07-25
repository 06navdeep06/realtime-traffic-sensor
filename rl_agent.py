import random
import json
import os
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class QLearningAgent:
    """
    A simple Q-learning agent.
    """
    def __init__(self, action_space, learning_rate=0.1, discount_factor=0.9, exploration_rate=0.1):
        if not action_space:
            raise ValueError("action_space cannot be empty")
        if not all(isinstance(a, int) for a in action_space):
            raise ValueError("All actions in action_space must be integers")
        if not (0 <= learning_rate <= 1):
            raise ValueError(f"learning_rate must be between 0 and 1, got {learning_rate}")
        if not (0 <= discount_factor <= 1):
            raise ValueError(f"discount_factor must be between 0 and 1, got {discount_factor}")
        if not (0 <= exploration_rate <= 1):
            raise ValueError(f"exploration_rate must be between 0 and 1, got {exploration_rate}")
            
        self.action_space = action_space
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = exploration_rate
        self.q_table = defaultdict(lambda: [0.0] * len(self.action_space))

    def load_q_table(self, path):
        """
        Load the Q-table from a file.
        """
        if not path:
            logger.warning("No path provided for Q-table loading")
            return
            
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    # The state (a tuple) gets converted to a string key in JSON
                    str_keys_q_table = json.load(f)
                    
                    if not isinstance(str_keys_q_table, dict):
                        logger.warning(f"Invalid Q-table format in {path}")
                        return
                        
                    loaded_table = {}
                    for k, v in str_keys_q_table.items():
                        try:
                            # Safely evaluate the key
                            key = eval(k) if isinstance(k, str) else k
                            if isinstance(v, list) and len(v) == len(self.action_space):
                                loaded_table[key] = v
                            else:
                                logger.warning(f"Skipping invalid Q-table entry: {k} -> {v}")
                        except Exception as e:
                            logger.warning(f"Error parsing Q-table entry {k}: {e}")
                            
                    self.q_table = defaultdict(
                        lambda: [0.0] * len(self.action_space),
                        loaded_table
                    )
                    logger.info(f"Loaded Q-table with {len(loaded_table)} entries from {path}")
            else:
                logger.info(f"Q-table file {path} not found, starting with empty table")
        except Exception as e:
            logger.error(f"Error loading Q-table from {path}: {e}")

    def save_q_table(self, path):
        """
        Save the Q-table to a file.
        """
        if not path:
            logger.warning("No path provided for Q-table saving")
            return
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Convert tuple keys to strings for JSON compatibility
            str_keys_q_table = {}
            for k, v in self.q_table.items():
                try:
                    if isinstance(v, list) and all(isinstance(x, (int, float)) for x in v):
                        str_keys_q_table[str(k)] = v
                except Exception as e:
                    logger.warning(f"Skipping invalid Q-table entry during save: {k} -> {v}: {e}")
                    
            with open(path, 'w') as f:
                json.dump(str_keys_q_table, f, indent=4)
            logger.info(f"Saved Q-table with {len(str_keys_q_table)} entries to {path}")
        except Exception as e:
            logger.error(f"Error saving Q-table to {path}: {e}")

    def get_action(self, state):
        """
        Choose an action using an epsilon-greedy policy.
        
        Args:
            state: The current state of the environment
            
        Returns:
            An action from the action space
        """
        if state is None or not self.action_space:
            return 0  # Default action if state or action space is invalid
            
        try:
            # Ensure epsilon is valid
            epsilon = max(0, min(1, self.epsilon))
            
            if random.random() < epsilon:
                return random.choice(self.action_space)  # Explore
            else:
                # Ensure state exists in Q-table
                if state not in self.q_table:
                    self.q_table[state] = [0.0] * len(self.action_space)
                    
                # Find the action with the highest Q-value for the current state
                q_values = self.q_table[state]
                
                # Validate Q-values
                if not q_values or len(q_values) != len(self.action_space):
                    logger.warning(f"Invalid Q-values for state {state}: {q_values}")
                    self.q_table[state] = [0.0] * len(self.action_space)
                    q_values = self.q_table[state]
                
                max_q = max(q_values)
                
                # If multiple actions have the same max Q-value, choose one randomly
                best_actions = [i for i, q in enumerate(q_values) if q == max_q]
                if best_actions:
                    return random.choice(best_actions)  # Exploit
                else:
                    return 0  # Fallback
        except Exception as e:
            logger.error(f"Error in get_action: {e}")
            return 0  # Fallback to default action

    def update_q_table(self, state, action, reward, next_state):
        """
        Update the Q-table using the Bellman equation.
        
        Args:
            state: The current state
            action: The action taken
            reward: The reward received
            next_state: The next state after taking the action
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            # Validate inputs
            if state is None or next_state is None or action is None:
                logger.warning("Invalid state or action in update_q_table")
                return False
                
            # Validate reward
            if not isinstance(reward, (int, float)):
                logger.warning(f"Invalid reward type: {type(reward)}")
                reward = 0.0
                
            # Initialize state in Q-table if it doesn't exist
            if state not in self.q_table:
                self.q_table[state] = [0.0] * len(self.action_space)
                
            # Initialize next_state in Q-table if it doesn't exist
            if next_state not in self.q_table:
                self.q_table[next_state] = [0.0] * len(self.action_space)
                
            # Ensure action is within valid range
            if not (0 <= action < len(self.action_space)):
                logger.warning(f"Invalid action {action} for action space size {len(self.action_space)}")
                return False
            
            # Get current Q-value and calculate next max Q-value
            old_value = self.q_table[state][action]
            
            # Safely calculate next max Q-value
            next_q_values = self.q_table[next_state]
            if next_q_values and all(isinstance(x, (int, float)) for x in next_q_values):
                next_max = max(next_q_values)
            else:
                next_max = 0.0

            # Bellman equation: Q(s,a) = Q(s,a) + α[r + γ * max(Q(s',a')) - Q(s,a)]
            try:
                new_value = old_value + self.lr * (reward + self.gamma * next_max - old_value)
                
                # Ensure new_value is a valid number
                if isinstance(new_value, (int, float)) and not (new_value != new_value):  # Check for NaN
                    self.q_table[state][action] = new_value
                else:
                    logger.warning(f"Invalid new Q-value calculated: {new_value}")
                    return False
            except (OverflowError, ZeroDivisionError) as e:
                logger.warning(f"Numerical error in Q-value update: {e}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error in update_q_table: {e}")
            return False
