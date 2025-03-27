import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import random
from collections import deque
import os
import pickle
from tqdm import tqdm
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial
import copy

from features.wizard.wizard_game_logic import WizardGame, GameState, Player, Color

# Add matplotlib imports at the top
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
from IPython.display import clear_output, display
import time
from datetime import datetime

# Check for GPU availability
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Determine optimal number of worker processes
NUM_CORES = max(1, mp.cpu_count() - 1)  # Leave one core free for system
print(f"Using {NUM_CORES} CPU cores for parallel training")

# Flag to indicate whether this process is a child worker process
# This will help prevent loading Discord-related code in worker processes
IS_WORKER_PROCESS = False

class WizardNN(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(WizardNN, self).__init__()
        # Create three hidden layers with gradually decreasing sizes
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size // 2)
        self.fc3 = nn.Linear(hidden_size // 2, hidden_size // 4)
        self.fc4 = nn.Linear(hidden_size // 4, output_size)
        
        # Batch normalization for better training stability
        self.bn1 = nn.BatchNorm1d(hidden_size)
        self.bn2 = nn.BatchNorm1d(hidden_size // 2)
        self.bn3 = nn.BatchNorm1d(hidden_size // 4)
        
        # Dropout for regularization
        self.dropout = nn.Dropout(0.2)
        
        # Initialize weights using He initialization
        nn.init.kaiming_normal_(self.fc1.weight)
        nn.init.kaiming_normal_(self.fc2.weight)
        nn.init.kaiming_normal_(self.fc3.weight)
        nn.init.kaiming_normal_(self.fc4.weight)

    def forward(self, x):
        # Apply batch normalization only during training, not for single inputs
        if x.size(0) > 1:  # If batch size > 1
            x = F.relu(self.bn1(self.fc1(x)))
            x = self.dropout(x)
            x = F.relu(self.bn2(self.fc2(x)))
            x = self.dropout(x)
            x = F.relu(self.bn3(self.fc3(x)))
        else:
            x = F.relu(self.fc1(x))
            x = F.relu(self.fc2(x))
            x = F.relu(self.fc3(x))

        return self.fc4(x)

class ReplayMemory:
    def __init__(self, capacity=10000):
        self.memory = deque(maxlen=capacity)

    def add(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)

def play_single_game(bot_state_dict, state_size, hidden_size, action_size, num_players, epsilon, device_type="cpu"):
    """
    Play a single game independently and return experiences
    This function runs in a separate process
    """
    # Set worker process flag to prevent Discord initialization
    global IS_WORKER_PROCESS
    IS_WORKER_PROCESS = True

    # Create a local device (CPU for worker processes to avoid GPU contention)
    local_device = torch.device(device_type)

    # Reconstruct model for this process
    model = WizardNN(state_size, hidden_size, action_size).to(local_device)
    model.load_state_dict(bot_state_dict)
    model.eval()  # Set to evaluation mode

    # Helper functions
    def encode_state(game, player_idx):
        """Convert game state to neural network input."""
        player = game.players[player_idx]
        state = np.zeros(state_size)

        # Basic game info
        state[0] = game.current_round / 20.0
        state[1] = player.called_stiche / max(1, game.current_round)
        state[2] = player.gewonnene_stiche / max(1, game.current_round)
        state[3] = (player.called_stiche - player.gewonnene_stiche) / max(1, game.current_round)
        # Trump card
        trump_color_idx = 4 + game.trump.color.value
        state[trump_color_idx] = 1.0
        state[8] = game.trump.value / 14.0

        # Encode player's hand (first 60 slots after basic info)
        card_idx = 9
        for card in player.hand[:10]:  # Limit to first 10 cards
            if card_idx + 6 > state_size:
                break
            state[card_idx + card.color.value] = 1.0
            state[card_idx + 5] = card.value / 14.0
            card_idx += 6

        # Encode current trick
        for card in game.stich[:6]:  # Limit to first 6 trick cards
            if card_idx + 6 > state_size:
                break
            state[card_idx + card.color.value] = 1.0
            state[card_idx + 5] = card.value / 14.0
            card_idx += 6

        return state

    def choose_action(game_state, player_idx):
        """Choose an action based on the game state."""
        state = encode_state(game_state, player_idx)
        valid_indices = game_state.get_valid_cards(player_idx)
        player = game_state.players[player_idx]

        if not valid_indices:
            return -1

        if random.random() < epsilon:
            # Exploration: choose random valid card
            return random.choice(valid_indices)

        # Exploitation: choose best valid card based on Q-values
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(local_device)

        with torch.no_grad():
            # Get Q-values for all 60 cards
            q_values = model(state_tensor).squeeze(0).cpu().numpy()

        # Map valid hand indices to actual card indices in the full 60-card deck
        valid_card_indices = []
        for idx in valid_indices:
            card = player.hand[idx]
            # Calculate global card index from color and value
            # Each color has 15 cards (1-13, Wizard, Jester)
            card_global_idx = card.color.value * 15 + (card.value - 1)  # -1 because card values start at 1
            valid_card_indices.append(card_global_idx)

        # Filter to only valid actions (cards in hand that can be played)
        masked_q_values = np.ones_like(q_values) * float('-inf')
        for valid_idx, hand_idx in zip(valid_card_indices, valid_indices):
            if 0 <= valid_idx < action_size:
                masked_q_values[valid_idx] = q_values[valid_idx]

        # Choose best valid action
        best_card_global_idx = np.argmax(masked_q_values)

        # Map back to hand index
        best_hand_idx = -1
        for valid_idx, hand_idx in zip(valid_card_indices, valid_indices):
            if valid_idx == best_card_global_idx:
                best_hand_idx = hand_idx
                break

        # If mapping failed, just pick a random card (shouldn't happen)
        if best_hand_idx == -1:
            best_hand_idx = random.choice(valid_indices)

        return best_hand_idx

    def predict_tricks(game, player_idx):
        """Predict number of tricks to call based on a simple heuristic."""
        player = game.players[player_idx]
        high_cards = sum(1 for card in player.hand if card.value >= 11 or card.color == game.trump.color)
        prediction = max(0, min(game.current_round, high_cards))

        valid_predictions = game.get_player_valid_predictions(player_idx)

        if prediction not in valid_predictions and valid_predictions:
            prediction = random.choice(valid_predictions)

        return prediction

    # Initialize game
    wizard_game = WizardGame()

    # Add players
    for i in range(num_players):
        bot_player = Player(0, f"Bot{i}")
        bot_player.is_bot = True
        wizard_game.game_state.add_player(bot_player)

    # Store experiences for the bot
    experiences = []
    prediction_accuracy = []

    # Play full game
    wizard_game.start_game()

    while not wizard_game.game_state.is_game_over():
        # Start round
        needs_trump = wizard_game.start_round()

        # Set trump color if needed
        if needs_trump:
            random_color = random.choice([Color.RED, Color.GREEN, Color.BLUE, Color.YELLOW])
            wizard_game.set_trump_color(random_color)

        # Make predictions for each player
        for i in range(len(wizard_game.game_state.players)):
            player_idx = (wizard_game.game_state.current_player + i) % len(wizard_game.game_state.players)
            prediction = predict_tricks(wizard_game.game_state, player_idx)
            wizard_game.make_prediction(player_idx, prediction)

        # Play tricks until round is over
        while not wizard_game.game_state.is_round_over():
            # Reset trick
            wizard_game.game_state.reset_stich()

            # Each player plays a card
            for i in range(len(wizard_game.game_state.players)):
                player_idx = (wizard_game.game_state.current_player + i) % len(wizard_game.game_state.players)

                # Get state before action
                state = encode_state(wizard_game.game_state, player_idx)

                # Get action
                valid_indices = wizard_game.game_state.get_valid_cards(player_idx)
                if valid_indices:
                    card_idx = choose_action(wizard_game.game_state, player_idx)
                    wizard_game.play_card(player_idx, card_idx)

                    # Store experience (will set reward later)
                    experiences.append({
                        'state': state,
                        'action': card_idx,
                        'player_idx': player_idx,
                        'reward': 0,
                        'next_state': None,
                        'done': False
                    })

            # Complete trick and determine winner
            trick_winner = wizard_game.end_trick()

            # Update experiences with rewards and next states
            for exp in experiences:
                # Get updated state
                next_state = encode_state(wizard_game.game_state, exp['player_idx'])
                exp['next_state'] = next_state

                player = wizard_game.game_state.players[exp['player_idx']]

                # Strategic reward based on prediction and current tricks won
                if exp['player_idx'] == trick_winner:
                    if player.gewonnene_stiche <= player.called_stiche:
                        # Good to win a trick when you need more tricks
                        exp['reward'] += 3.0
                    else:
                        # Bad to win a trick when you already have enough
                        exp['reward'] -= 2.0
                else:
                    # For losing a trick
                    if player.gewonnene_stiche >= player.called_stiche:
                        # Good to lose a trick when you already have enough
                        exp['reward'] += 2.0
                    else:
                        # Small penalty for losing a trick when you need more
                        exp['reward'] -= 0.5

        # End of round: update scores and add prediction accuracy rewards
        wizard_game.game_state.update_scores()

        for player_idx, player in enumerate(wizard_game.game_state.players):
            # Track prediction accuracy
            is_accurate = player.gewonnene_stiche == player.called_stiche
            prediction_accuracy.append(1 if is_accurate else 0)

            # Update rewards for this player's experiences
            for exp in [e for e in experiences if e['player_idx'] == player_idx]:
                # Reward for prediction accuracy
                if is_accurate:
                    exp['reward'] += 2.0
                else:
                    exp['reward'] -= 1.0

        # Reset for next round
        wizard_game.game_state.current_round += 1
        for player in wizard_game.game_state.players:
            player.gewonnene_stiche = 0
            player.called_stiche = 0

    # Game is over - add terminal rewards
    final_scores = [player.score for player in wizard_game.game_state.players]
    max_score = max(final_scores)
    win_info = []

    for player_idx, player in enumerate(wizard_game.game_state.players):
        # Record win info
        is_winner = player.score == max_score
        win_info.append((player.score, is_winner))

        # Terminal reward based on final score
        score_ratio = player.score / max(1, max_score)
        for exp in [e for e in experiences if e['player_idx'] == player_idx]:
            terminal_reward = 5.0 if player.score == max_score else 2.0 * score_ratio - 1.0
            exp['reward'] += terminal_reward
            exp['done'] = True

    # Return relevant data
    avg_accuracy = sum(prediction_accuracy) / max(1, len(prediction_accuracy))
    return experiences, win_info, avg_accuracy

def play_batch_games(model, state_size, hidden_size, action_size, num_players, epsilon, num_games=10):
    """
    Play multiple games in sequence and return all experiences
    """
    all_experiences = []
    win_info = []
    prediction_accuracy = []

    # Helper functions
    def encode_state(game, player_idx):
        """Convert game state to neural network input."""
        player = game.players[player_idx]
        state = np.zeros(state_size)

        # Basic game info
        state[0] = game.current_round / 20.0
        state[1] = player.called_stiche / max(1, game.current_round)
        state[2] = player.gewonnene_stiche / max(1, game.current_round)

        # Trump card
        trump_color_idx = 3 + game.trump.color.value
        state[trump_color_idx] = 1.0
        state[8] = game.trump.value / 14.0

        # Encode player's hand (first 60 slots after basic info)
        card_idx = 9
        for card in player.hand[:10]:  # Limit to first 10 cards
            if card_idx + 6 > state_size:
                break
            state[card_idx + card.color.value] = 1.0
            state[card_idx + 5] = card.value / 14.0
            card_idx += 6

        # Encode current trick
        for card in game.stich[:6]:  # Limit to first 6 trick cards
            if card_idx + 6 > state_size:
                break
            state[card_idx + card.color.value] = 1.0
            state[card_idx + 5] = card.value / 14.0
            card_idx += 6

        return state

    def choose_action(game_state, player_idx):
        """Choose an action based on the game state."""
        state = encode_state(game_state, player_idx)
        valid_indices = game_state.get_valid_cards(player_idx)
        player = game_state.players[player_idx]

        if not valid_indices:
            return -1

        if random.random() < epsilon:
            # Exploration: choose random valid card
            return random.choice(valid_indices)

        # Exploitation: choose best valid card based on Q-values
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)

        with torch.no_grad():
            # Get Q-values for all 60 cards
            q_values = model(state_tensor).squeeze(0).cpu().numpy()

        # Map valid hand indices to actual card indices in the full 60-card deck
        valid_card_indices = []
        for idx in valid_indices:
            card = player.hand[idx]
            # Calculate global card index from color and value
            card_global_idx = card.color.value * 15 + (card.value - 1)  # -1 because card values start at 1
            valid_card_indices.append(card_global_idx)

        # Filter to only valid actions
        masked_q_values = np.ones_like(q_values) * float('-inf')
        for valid_idx, hand_idx in zip(valid_card_indices, valid_indices):
            if 0 <= valid_idx < action_size:
                masked_q_values[valid_idx] = q_values[valid_idx]

        # Choose best valid action
        best_card_global_idx = np.argmax(masked_q_values)

        # Map back to hand index
        best_hand_idx = -1
        for valid_idx, hand_idx in zip(valid_card_indices, valid_indices):
            if valid_idx == best_card_global_idx:
                best_hand_idx = hand_idx
                break

        # If mapping failed, just pick a random card
        if best_hand_idx == -1:
            best_hand_idx = random.choice(valid_indices)

        return best_hand_idx

    def predict_tricks(game, player_idx):
        """Predict number of tricks to call based on a simple heuristic."""
        player = game.players[player_idx]
        high_cards = sum(1 for card in player.hand if card.value >= 11 or card.color == game.trump.color)
        prediction = max(0, min(game.current_round, high_cards))

        valid_predictions = game.get_player_valid_predictions(player_idx)

        if prediction not in valid_predictions and valid_predictions:
            prediction = random.choice(valid_predictions)

        return prediction

    for _ in range(num_games):
        # Initialize game
        wizard_game = WizardGame()

        # Add players
        for i in range(num_players):
            bot_player = Player(0, f"Bot{i}")
            bot_player.is_bot = True
            wizard_game.game_state.add_player(bot_player)

        # Store experiences for the bot
        game_experiences = []
        game_prediction_accuracy = []

        # Play full game
        wizard_game.start_game()

        while not wizard_game.game_state.is_game_over():
            # Start round
            needs_trump = wizard_game.start_round()

            # Set trump color if needed
            if needs_trump:
                random_color = random.choice([Color.RED, Color.GREEN, Color.BLUE, Color.YELLOW])
                wizard_game.set_trump_color(random_color)

            # Make predictions for each player
            for i in range(len(wizard_game.game_state.players)):
                player_idx = (wizard_game.game_state.current_player + i) % len(wizard_game.game_state.players)
                prediction = predict_tricks(wizard_game.game_state, player_idx)
                wizard_game.make_prediction(player_idx, prediction)

            # Play tricks until round is over
            while not wizard_game.game_state.is_round_over():
                # Reset trick
                wizard_game.game_state.reset_stich()

                # Each player plays a card
                for i in range(len(wizard_game.game_state.players)):
                    player_idx = (wizard_game.game_state.current_player + i) % len(wizard_game.game_state.players)

                    # Get state before action
                    state = encode_state(wizard_game.game_state, player_idx)

                    # Get action
                    valid_indices = wizard_game.game_state.get_valid_cards(player_idx)
                    if valid_indices:
                        card_idx = choose_action(wizard_game.game_state, player_idx)
                        wizard_game.play_card(player_idx, card_idx)

                        # Store experience (will set reward later)
                        game_experiences.append({
                            'state': state,
                            'action': card_idx,
                            'player_idx': player_idx,
                            'reward': 0,
                            'next_state': None,
                            'done': False
                        })

                # Complete trick and determine winner
                trick_winner = wizard_game.end_trick()

                # Update experiences with rewards and next states
                for exp in game_experiences:
                    # Get updated state
                    next_state = encode_state(wizard_game.game_state, exp['player_idx'])
                    exp['next_state'] = next_state

                    # Basic reward: win trick = +1, lose trick = -0.2
                    player = wizard_game.game_state.players[exp['player_idx']]
                    if exp['player_idx'] == trick_winner:
                        exp['reward'] += 1.0
                    else:
                        exp['reward'] -= 0.2

            # End of round: update scores and add prediction accuracy rewards
            wizard_game.game_state.update_scores()

            for player_idx, player in enumerate(wizard_game.game_state.players):
                # Track prediction accuracy
                is_accurate = player.gewonnene_stiche == player.called_stiche
                game_prediction_accuracy.append(1 if is_accurate else 0)

                # Update rewards for this player's experiences
                for exp in [e for e in game_experiences if e['player_idx'] == player_idx]:
                    # Reward for prediction accuracy
                    if is_accurate:
                        exp['reward'] += 2.0
                    else:
                        exp['reward'] -= 1.0

            # Reset for next round
            wizard_game.game_state.current_round += 1
            for player in wizard_game.game_state.players:
                player.gewonnene_stiche = 0
                player.called_stiche = 0

        # Game is over - add terminal rewards
        final_scores = [player.score for player in wizard_game.game_state.players]
        max_score = max(final_scores)
        game_win_info = []

        for player_idx, player in enumerate(wizard_game.game_state.players):
            # Record win info
            is_winner = player.score == max_score
            game_win_info.append((player.score, is_winner))

            # Terminal reward based on final score
            score_ratio = player.score / max(1, max_score)
            for exp in [e for e in game_experiences if e['player_idx'] == player_idx]:
                terminal_reward = 5.0 if player.score == max_score else 2.0 * score_ratio - 1.0
                exp['reward'] += terminal_reward
                exp['done'] = True

        # Collect data from this game
        all_experiences.extend(game_experiences)
        win_info.extend(game_win_info)
        prediction_accuracy.extend(game_prediction_accuracy)

    # Return relevant data
    avg_accuracy = sum(prediction_accuracy) / max(1, len(prediction_accuracy))
    return all_experiences, win_info, avg_accuracy

class WizardRLBot:
    def __init__(self, state_size=120, hidden_size=256, action_size=60):
        # Basic parameters
        self.state_size = state_size
        self.hidden_size = hidden_size
        self.action_size = action_size  # Changed from 15 to 60 (representing all cards in the deck)
        self.gamma = 0.95  # discount factor
        self.epsilon = 0.5  # exploration rate
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.05
        self.batch_size = 64
        self.update_target_every = 50
        self.train_count = 0
        self.best_score = -float('inf')
        self.reward_scale = 10.0  # Add reward scaling factor
        self.learning_rate = 0.01
        self.device = device  # Store device for tensor operations

        # Neural networks (move to GPU if available)
        self.model = WizardNN(state_size, hidden_size, action_size).to(device)
        self.target_model = WizardNN(state_size, hidden_size, action_size).to(device)
        self.target_model.load_state_dict(self.model.state_dict())

        # Optimizer
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)

        # Experience replay memory
        self.memory = ReplayMemory(20000)

        # Model paths
        self.model_path = "wizard_nn_model.pt"
        self.full_bot_path = "wizard_full_bot.pkl"

        # Training metrics for plotting
        self.metrics = {
            'losses': [],
            'avg_scores': [],
            'win_rates': [],
            'epsilons': [],
            'trick_accuracies': [],
            'iterations': []
        }

        # Create logs directory
        os.makedirs("training_logs", exist_ok=True)
        self.log_path = f"training_logs/training_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        # Initialize log file with header
        with open(self.log_path, 'w') as f:
            f.write("iteration,epoch,loss,avg_score,win_rate,epsilon,trick_accuracy\n")

        # Try to load saved model
        if os.path.exists(self.model_path):
            self.load_model()

    def encode_state(self, game: GameState, player_idx: int) -> np.ndarray:
        """Convert game state to neural network input."""
        player = game.players[player_idx]
        state = np.zeros(self.state_size)

        # Basic game info
        state[0] = game.current_round / 20.0
        state[1] = player.called_stiche / max(1, game.current_round)
        state[2] = player.gewonnene_stiche / max(1, game.current_round)

        # Trump card
        trump_color_idx = 3 + game.trump.color.value
        state[trump_color_idx] = 1.0
        state[8] = game.trump.value / 14.0

        # Encode player's hand (first 60 slots after basic info)
        card_idx = 9
        for card in player.hand[:15]:  # Limit to first 10 cards
            if card_idx + 6 > self.state_size:
                break
            state[card_idx + card.color.value] = 1.0
            state[card_idx + 5] = card.value / 14.0
            card_idx += 6

        # Encode current trick
        for card in game.stich[:6]:  # Limit to first 6 trick cards
            if card_idx + 6 > self.state_size:
                break
            state[card_idx + card.color.value] = 1.0
            state[card_idx + 5] = card.value / 14.0
            card_idx += 6

        return state

    def choose_action(self, game_state, player_idx, return_q_values=False):
        """Choose an action based on the game state."""
        state = self.encode_state(game_state, player_idx)
        valid_indices = game_state.get_valid_cards(player_idx)
        player = game_state.players[player_idx]

        if not valid_indices:
            if return_q_values:
                return -1, None
            return -1

        if random.random() < self.epsilon:
            # Exploration: choose random valid card
            choice = random.choice(valid_indices)
            if return_q_values:
                return choice, None
            return choice

        # Exploitation: choose best valid card based on Q-values
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)

        with torch.no_grad():
            # Get Q-values for all 60 cards
            q_values = self.model(state_tensor).squeeze(0).cpu().numpy()

        # Map valid hand indices to actual card indices in the full 60-card deck
        valid_card_indices = []
        for idx in valid_indices:
            card = player.hand[idx]
            # Calculate global card index from color and value
            # Each color has 15 cards (1-13, Wizard, Jester)
            card_global_idx = card.color.value * 15 + (card.value - 1)  # -1 because card values start at 1
            valid_card_indices.append(card_global_idx)

        # Filter to only valid actions (cards in hand that can be played)
        masked_q_values = np.ones_like(q_values) * float('-inf')
        for valid_idx, hand_idx in zip(valid_card_indices, valid_indices):
            if 0 <= valid_idx < self.action_size:
                masked_q_values[valid_idx] = q_values[valid_idx]

        # Choose best valid action
        best_card_global_idx = np.argmax(masked_q_values)

        # Map back to hand index
        best_hand_idx = -1
        for valid_idx, hand_idx in zip(valid_card_indices, valid_indices):
            if valid_idx == best_card_global_idx:
                best_hand_idx = hand_idx
                break

        # If mapping failed, just pick a random card (shouldn't happen)
        if best_hand_idx == -1:
            best_hand_idx = random.choice(valid_indices)

        if return_q_values:
            return best_hand_idx, q_values
        return best_hand_idx

    def predict_tricks(self, game: GameState, player_idx: int) -> int:
        """Predict number of tricks to call based on a simple heuristic."""
        player = game.players[player_idx]
        high_cards = sum(1 for card in player.hand if card.value >= 11 or card.color == game.trump.color)
        prediction = max(0, min(game.current_round, high_cards))

        valid_predictions = game.get_player_valid_predictions(player_idx)

        if prediction not in valid_predictions and valid_predictions:
            prediction = random.choice(valid_predictions)

        return prediction

    def remember(self, state, action, reward, next_state, done):
        """Add experience to memory"""
        # Scale the reward to avoid near-zero values
        scaled_reward = reward * self.reward_scale
        self.memory.add(state, action, scaled_reward, next_state, done)

    def update_model(self):
        """Train the model on a batch of experiences."""
        if len(self.memory) < self.batch_size:
            return None  # Return None if not enough samples

        batch = self.memory.sample(self.batch_size)
        states = torch.FloatTensor(np.array([exp[0] for exp in batch])).to(self.device)

        # Get actions (hand indices) and convert to global card indices
        actions_hand_idx = [exp[1] for exp in batch]
        actions_global_idx = []

        for i, (state, action_idx) in enumerate(zip([exp[0] for exp in batch], actions_hand_idx)):
            # This is a simplification - in a real implementation, you would need
            # to reconstruct the game state and get the actual card from the player's hand
            # For now, we'll just use the action index directly (assuming it's already global)
            actions_global_idx.append(action_idx)

        actions = torch.LongTensor(actions_global_idx).unsqueeze(1).to(self.device)
        rewards = torch.FloatTensor([exp[2] for exp in batch]).to(self.device)
        next_states = torch.FloatTensor(np.array([exp[3] for exp in batch])).to(self.device)
        dones = torch.FloatTensor([exp[4] for exp in batch]).to(self.device)

        # Current Q values
        current_q = self.model(states).gather(1, actions).squeeze(1)

        # Target Q values
        with torch.no_grad():
            # Double DQN
            next_actions = self.model(next_states).max(1)[1].unsqueeze(1)
            next_q = self.target_model(next_states).gather(1, next_actions).squeeze(1)
            target_q = rewards + (1 - dones) * self.gamma * next_q

        # Huber loss for stability
        loss = F.smooth_l1_loss(current_q, target_q)

        # Update model
        self.optimizer.zero_grad()
        loss.backward()
        # Gradient clipping to prevent exploding gradients
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
        self.optimizer.step()

        # Update target network periodically
        self.train_count += 1
        if self.train_count % self.update_target_every == 0:
            self.target_model.load_state_dict(self.model.state_dict())

        return loss.item()

    def save_model(self):
        """Save the model weights."""
        torch.save(self.model.state_dict(), self.model_path)
        print(f"Model saved to {self.model_path}")

    def load_model(self):
        """Load the model weights."""
        try:
            # Load model to the appropriate device
            self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
            self.target_model.load_state_dict(self.model.state_dict())
            print(f"Model loaded successfully to {self.device}")
        except Exception as e:
            print(f"Error loading model: {e}")

    def save_full_bot(self):
        """Save the complete bot (including hyperparameters)."""
        # Move models to CPU for saving to ensure compatibility when loading
        model_cpu = self.model.to('cpu')
        target_model_cpu = self.target_model.to('cpu')

        save_dict = {
            'state_size': self.state_size,
            'hidden_size': self.hidden_size,
            'action_size': self.action_size,
            'epsilon': self.epsilon,
            'model_state': model_cpu.state_dict(),
            'target_model_state': target_model_cpu.state_dict(),
        }

        with open(self.full_bot_path, 'wb') as f:
            pickle.dump(save_dict, f)
        print(f"Full bot saved to {self.full_bot_path}")

        # Move models back to the original device
        self.model.to(self.device)
        self.target_model.to(self.device)

    def log_metrics(self, iteration, epoch, loss, avg_score, win_rate, trick_accuracy):
        """Log metrics to CSV file."""
        with open(self.log_path, 'a') as f:
            f.write(f"{iteration},{epoch},{loss},{avg_score},{win_rate},{self.epsilon},{trick_accuracy}\n")

    def create_bot_player(self, name):
        """Create a bot player for the game."""
        bot_player = Player(0, name)
        bot_player.is_bot = True
        return bot_player

    def display_training_metrics(self, clear=True):
        """Display live training metrics during training."""
        if clear:
            clear_output(wait=True)

        if len(self.metrics['iterations']) > 0:
            # Create a figure for display
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

            iterations = self.metrics['iterations']

            # Plot average scores
            ax1.plot(iterations, self.metrics['avg_scores'], 'b-', linewidth=2)
            ax1.set_title('Average Scores')
            ax1.set_xlabel('Iteration')
            ax1.set_ylabel('Score')
            ax1.grid(True)

            # Plot win rates and epsilon
            ax2.plot(iterations, self.metrics['win_rates'], 'g-', linewidth=2, label='Win Rate')
            ax2.plot(iterations, self.metrics['epsilons'], 'r--', linewidth=1, label='Epsilon')
            if len(self.metrics['trick_accuracies']) == len(iterations):
                ax2.plot(iterations, self.metrics['trick_accuracies'], 'y-', linewidth=1.5, label='Trick Accuracy')
            ax2.set_title('Win Rate and Exploration Rate')
            ax2.set_xlabel('Iteration')
            ax2.set_ylabel('Rate')
            ax2.legend()
            ax2.grid(True)

            plt.tight_layout()

            # Display the plot in Jupyter/IPython environment
            display(fig)
            plt.close(fig)

    def train(self, num_iterations=100, games_per_iteration=100, num_players=4):
        """Train the model using GPU-accelerated reinforcement learning."""
        print(f"Starting GPU-accelerated training: {num_iterations} iterations, {games_per_iteration} games per iteration")
        print(f"Using device: {self.device}")

        # Enable CUDA optimizations if available
        if self.device.type == 'cuda':
            torch.backends.cudnn.benchmark = True

        # Create directories for logs and stats
        os.makedirs("training_logs", exist_ok=True)

        for iteration in range(num_iterations):
            print(f"\nIteration {iteration+1}/{num_iterations}")

            # Metrics for this iteration
            iteration_losses = []
            scores = []
            wins = 0
            games_played = 0
            prediction_accuracy = []

            # Play games in smaller batches for better GPU memory management
            batch_size = min(10, games_per_iteration)
            num_batches = games_per_iteration // batch_size

            all_experiences = []

            for batch in tqdm(range(num_batches), desc=f"Playing {games_per_iteration} games in batches"):
                # Run a batch of games
                game_experiences, win_info, game_accuracy = play_batch_games(
                    self.model,
                    self.state_size,
                    self.hidden_size,
                    self.action_size,
                    num_players,
                    self.epsilon,
                    num_games=batch_size
                )

                # Process game results
                all_experiences.extend(game_experiences)
                prediction_accuracy.append(game_accuracy)
                games_played += batch_size

                # Process win info
                for player_score, is_winner in win_info:
                    scores.append(player_score)
                    if is_winner:
                        wins += 1

            # Shuffle experiences to break correlation
            random.shuffle(all_experiences)

            # Add experiences to memory
            for exp in all_experiences:
                self.remember(exp['state'], exp['action'], exp['reward'], exp['next_state'], exp['done'])

            # Determine number of training updates
            num_updates = min(len(all_experiences) // self.batch_size, max(50, games_per_iteration))
            print(f"Performing {num_updates} batch updates")

            # Train on GPU in batches
            for _ in tqdm(range(num_updates), desc="Training batches"):
                loss = self.update_model()
                if loss is not None:
                    iteration_losses.append(loss)

            # Calculate metrics for this iteration
            avg_loss = sum(iteration_losses) / max(1, len(iteration_losses))
            avg_score = sum(scores) / max(1, len(scores))
            win_rate = wins / max(1, len(scores))
            avg_accuracy = sum(prediction_accuracy) / max(1, len(prediction_accuracy))

            # Store metrics for plotting
            self.metrics['losses'].append(avg_loss)
            self.metrics['avg_scores'].append(avg_score)
            self.metrics['win_rates'].append(win_rate)
            self.metrics['epsilons'].append(self.epsilon)
            self.metrics['trick_accuracies'].append(avg_accuracy)
            self.metrics['iterations'].append(iteration+1)

            # Print stats
            print(f"Iteration {iteration+1} - Avg Loss: {avg_loss:.4f}")
            print(f"Average score: {avg_score:.1f}")
            print(f"Win rate: {win_rate:.1%}")
            print(f"Prediction accuracy: {avg_accuracy:.1%}")
            print(f"Epsilon: {self.epsilon:.4f}")

            # Log metrics
            self.log_metrics(
                iteration=iteration+1,
                epoch=iteration * games_per_iteration,
                loss=avg_loss,
                avg_score=avg_score,
                win_rate=win_rate,
                trick_accuracy=avg_accuracy
            )

            # Display live training metrics
            self.display_training_metrics()

            # Save best model
            if avg_score > self.best_score:
                self.best_score = avg_score
                print(f"New best score: {self.best_score:.1f}")

            # Decay epsilon
            self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

            # Save model after each iteration
            self.save_model()
            self.save_full_bot()

            # Save simple plot of progress
            self.plot_training_progress()

        print("Training complete!")

    def plot_training_progress(self):
        """Create a simple plot of training progress."""
        try:
            # Create basic plot of avg scores and win rates
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

            iterations = self.metrics['iterations']

            # Plot average scores
            if len(iterations) > 0 and len(self.metrics['avg_scores']) > 0:
                ax1.plot(iterations, self.metrics['avg_scores'], 'b-', linewidth=2)
                ax1.set_title('Average Scores')
                ax1.set_xlabel('Iteration')
                ax1.set_ylabel('Score')
                ax1.grid(True)

            # Plot win rates and epsilon
            if len(iterations) > 0 and len(self.metrics['win_rates']) > 0:
                ax2.plot(iterations, self.metrics['win_rates'], 'g-', linewidth=2, label='Win Rate')
                ax2.plot(iterations, self.metrics['epsilons'], 'r--', linewidth=1, label='Epsilon')
                ax2.set_title('Win Rate and Exploration Rate')
                ax2.set_xlabel('Iteration')
                ax2.set_ylabel('Rate')
                ax2.legend()
                ax2.grid(True)

            plt.tight_layout()
            plt.savefig('training_stats/training_progress.png')
            plt.close()

        except Exception as e:
            print(f"Error creating progress plot: {e}")


def train_new_bot():
    """Train a new bot using GPU-accelerated reinforcement learning."""
    # Make sure we're not in a worker process
    if IS_WORKER_PROCESS:
        print("Warning: Attempting to train bot in a worker process. This is not allowed.")
        return None

    bot = WizardRLBot(state_size=120, hidden_size=256, action_size=60)
    try:
        bot.load_model()
    except:
        print("Starting with a new model")

    # Train the bot
    bot.train(
        num_iterations=2000,     # Total iterations
        games_per_iteration=20, # Games per iteration
        num_players=2           # Number of players per game
    )

    # Final save
    bot.save_model()
    bot.save_full_bot()

    return bot

