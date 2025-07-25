import random
import json
from collections import defaultdict

class QLearningAgent:
    """
    A simple Q-learning agent.
    """
    def __init__(self, action_space, learning_rate=0.1, discount_factor=0.9, exploration_rate=0.1):
        self.action_space = action_space
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = exploration_rate
        self.q_table = defaultdict(lambda: [0.0] * len(self.action_space))

    def load_q_table(self, path):
        """
        Load the Q-table from a file.
        """
        try:
            with open(path, 'r') as f:
                # The state (a tuple) gets converted to a string key in JSON
                str_keys_q_table = json.load(f)
                self.q_table = defaultdict(
                    lambda: [0.0] * len(self.action_space),
                    {eval(k): v for k, v in str_keys_q_table.items()}
                )
        except FileNotFoundError:
            # Silently ignore if no file is found, agent will start fresh
            pass

    def save_q_table(self, path):
        """
        Save the Q-table to a file.
        """
        with open(path, 'w') as f:
            # Convert tuple keys to strings for JSON compatibility
            str_keys_q_table = {str(k): v for k, v in self.q_table.items()}
            json.dump(str_keys_q_table, f, indent=4)

    def get_action(self, state):
        """
        Choose an action using an epsilon-greedy policy.
        
        Args:
            state: The current state of the environment
            
        Returns:
            An action from the action space
        """
        if not state or not self.action_space:
            return 0  # Default action if state or action space is invalid
            
        try:
            if random.random() < self.epsilon:
                return random.choice(self.action_space)  # Explore
            else:
                # Ensure state exists in Q-table
                if state not in self.q_table:
                    self.q_table[state] = [0.0] * len(self.action_space)
                    
                # Find the action with the highest Q-value for the current state
                q_values = self.q_table[state]
                max_q = max(q_values)
                
                # If multiple actions have the same max Q-value, choose one randomly
                best_actions = [i for i, q in enumerate(q_values) if q == max_q]
                return random.choice(best_actions)  # Exploit
        except Exception as e:
            print(f"Error in get_action: {e}")
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
                print("Warning: Invalid state or action in update_q_table")
                return False
                
            # Initialize state in Q-table if it doesn't exist
            if state not in self.q_table:
                self.q_table[state] = [0.0] * len(self.action_space)
                
            # Initialize next_state in Q-table if it doesn't exist
            if next_state not in self.q_table:
                self.q_table[next_state] = [0.0] * len(self.action_space)
                
            # Ensure action is within valid range
            if not (0 <= action < len(self.action_space)):
                print(f"Warning: Invalid action {action} for action space size {len(self.action_space)}")
                return False
            
            # Get current Q-value and calculate next max Q-value
            old_value = self.q_table[state][action]
            next_max = max(self.q_table[next_state]) if self.q_table[next_state] else 0

            # Bellman equation: Q(s,a) = Q(s,a) + α[r + γ * max(Q(s',a')) - Q(s,a)]
            new_value = old_value + self.lr * (reward + self.gamma * next_max - old_value)
            self.q_table[state][action] = new_value
            
            return True
            
        except Exception as e:
            print(f"Error in update_q_table: {e}")
            return False
