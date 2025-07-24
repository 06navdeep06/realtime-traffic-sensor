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

    def save_q_table(self, path):
        """
        Save the Q-table to a file.
        """
        with open(path, 'w') as f:
            # Convert tuple keys to strings for JSON compatibility
            str_keys_q_table = {str(k): v for k, v in self.q_table.items()}
            json.dump(str_keys_q_table, f)

    def get_action(self, state):
        """
        Choose an action using an epsilon-greedy policy.
        """
        if random.random() < self.epsilon:
            return random.choice(self.action_space)  # Explore
        else:
            # Find the action with the highest Q-value for the current state
            q_values = self.q_table[state]
            max_q = max(q_values)
            # If multiple actions have the same max Q-value, choose one randomly
            best_actions = [i for i, q in enumerate(q_values) if q == max_q]
            return random.choice(best_actions) # Exploit

    def update_q_table(self, state, action, reward, next_state):
        """
        Update the Q-table using the Bellman equation.
        """
        old_value = self.q_table[state][action]
        next_max = max(self.q_table[next_state])

        # Bellman equation
        new_value = old_value + self.lr * (reward + self.gamma * next_max - old_value)
        self.q_table[state][action] = new_value
