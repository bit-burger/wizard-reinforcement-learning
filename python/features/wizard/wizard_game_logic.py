import random
from enum import Enum
from typing import List, Tuple

import discord

DECK_SIZE = 60
PLAYERS_MIN = 1
PLAYERS_MAX = 6



class Color(Enum):
    RED = 0
    GREEN = 1
    BLUE = 2
    YELLOW = 3
    NILL = 4

class Card:
    def __init__(self, value: int, color: Color):
        self.value = value
        self.color = color

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.value == other.value and self.color == other.color

    def __hash__(self):
        return hash((self.value, self.color))

class Player:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name
        self.score = 0
        self.hand: List[Card] = []
        self.called_stiche = 0
        self.gewonnene_stiche = 0
        self.is_bot = False

    @property
    def formatted_name(self):
        return self.name.replace('_', '\\_')

    @classmethod
    def from_discord_user(cls, user: discord.User):
        return cls(user.id, user.name)

class GameState:
    def __init__(self):
        self.players: List[Player] = []
        self.current_round = 0
        self.deck: List[Card] = []
        self.trump: Card = None
        self.current_player = 0
        self.stich: List[Card] = []
        self.start_player = 0
        self.suit_card: Card = None
        self.round_in_progress = False
        self.tricks_in_progress = False

    def shuffle_deck(self):
        self.deck = [Card(i % 15, Color(i % 4)) for i in range(60)]
        random.shuffle(self.deck)

    def deal_cards(self):
        for player in self.players:
            player.hand = []
        for _ in range(self.current_round):
            for player in self.players:
                if self.deck:  # Make sure there are still cards in the deck
                    player.hand.append(self.deck.pop())

    def play_card(self, player_index: int, card_index: int) -> Card:
        if card_index >= len(self.players[player_index].hand):
            raise ValueError("Invalid card index")
        played_card = self.players[player_index].hand.pop(card_index)
        self.stich.append(played_card)
        return played_card

    def get_valid_cards(self, player_index: int) -> List[int]:
        """Returns indices of valid cards that the player can play."""
        player = self.players[player_index]

        # If no cards have been played yet, all cards are valid
        if not self.stich:
            return list(range(len(player.hand)))

        # Find the suit to follow (first non-Jester, non-Wizard card)
        suit_to_follow = None
        for card in self.stich:
            if card.value not in [0, 14]:  # Not a Jester or Wizard
                suit_to_follow = card.color
                break

        # If no suit to follow was found, all cards are valid
        if suit_to_follow is None:
            return list(range(len(player.hand)))

        # Check if player has any cards of the required suit
        matching_suit_indices = []
        for i, card in enumerate(player.hand):
            # Wizards and Jesters are always valid
            if card.value in [0, 14]:
                matching_suit_indices.append(i)
            # Cards of the required suit are valid
            elif card.color == suit_to_follow:
                matching_suit_indices.append(i)

        # If player has no cards of the required suit, all cards are valid
        if not matching_suit_indices:
            return list(range(len(player.hand)))

        return matching_suit_indices

    def determine_stich_winner(self) -> int:
        # First check for Wizards (highest priority)
        for i, card in enumerate(self.stich):
            if card.value == 14:  # Wizard
                return (self.current_player + i) % len(self.players)

        # Initialize with first card
        winning_card = self.stich[0]
        winning_player = 0

        # Check remaining cards
        for i in range(1, len(self.stich)):
            card = self.stich[i]
            if card.value == 0:  # Jester never wins
                continue
            elif winning_card.value == 0:  # Anything beats a Jester
                winning_card = card
                winning_player = i
            elif card.color == self.trump.color and winning_card.color != self.trump.color:
                winning_card = card
                winning_player = i
            elif card.color == winning_card.color and card.value > winning_card.value:
                winning_card = card
                winning_player = i

        return (self.current_player + winning_player) % len(self.players)

    def reset_stich(self):
        self.stich = []

    def is_round_over(self) -> bool:
        return all(len(player.hand) == 0 for player in self.players)

    def is_game_over(self) -> bool:
        return self.current_round > 15

    def update_scores(self):
        """Update scores at the end of a round"""
        for player in self.players:
            if player.gewonnene_stiche == player.called_stiche:
                player.score += 20 + 10 * player.called_stiche
            else:
                player.score -= 10 * abs(player.gewonnene_stiche - player.called_stiche)

    def reset_predictions_and_tricks(self):
        """Reset predictions and won tricks for all players"""
        for player in self.players:
            player.gewonnene_stiche = 0
            player.called_stiche = 0

    def add_player(self, player):
        """Add a player to the game"""
        self.players.append(player)
        return True

    def get_game_state_snapshot(self):
        """Get a snapshot of the current game state for AI/bot use"""
        return {
            'current_round': self.current_round,
            'trump': self.trump,
            'current_player': self.current_player,
            'stich': self.stich.copy(),
            'players': [
                {
                    'name': p.name,
                    'score': p.score,
                    'hand': p.hand.copy(),
                    'called': p.called_stiche,
                    'won': p.gewonnene_stiche,
                    'is_bot': p.is_bot
                }
                for p in self.players
            ]
        }
    def get_player_valid_predictions(self, player_index: int) -> List[int]:
        """Get valid predictions for a player (handles last player restriction)"""
        if player_index < 0 or player_index >= len(self.players):
            raise ValueError("Invalid player index")

        max_value = self.current_round
        options = list(range(max_value + 1))

        # The dealer (starting player) rotates each round
        dealer_index = (self.current_round - 1) % len(self.players)
        # Prediction order is clockwise from dealer
        prediction_positions = [(dealer_index + i) % len(self.players) for i in range(len(self.players))]

        # The player's position in the prediction order
        player_position = prediction_positions.index(player_index)

        # Check if this is the last player to predict
        if player_position == len(self.players) - 1:
            # Calculate the sum of predictions made so far
            total_predicted = sum(self.players[idx].called_stiche
                                  for idx in prediction_positions[:player_position]
                                  if hasattr(self.players[idx], 'called_stiche') and
                                  self.players[idx].called_stiche >= 0)

            # The forbidden prediction
            forbidden_value = max_value - total_predicted

            # Remove the forbidden value from options
            if 0 <= forbidden_value <= max_value:
                options.remove(forbidden_value)

        return options




class WizardGame:
    """Core game logic for Wizard card game"""

    def __init__(self):
        self.game_state = GameState()

    def start_game(self):
        """Start a new game"""
        self.game_state.current_round = 1
        return self.start_round()

    def start_round(self):
        """Start a new round"""
        self.game_state.shuffle_deck()
        self.game_state.deal_cards()

        # Set the trump card
        if self.game_state.deck:
            self.game_state.trump = self.game_state.deck[0]
        else:
            self.game_state.trump = Card(random.randint(0, 14), Color(random.randint(0, 4)))

        # Set the starting player (rotates each round)
        self.game_state.current_player = (self.game_state.current_round - 1) % len(self.game_state.players)

        # Return whether the trump is a Wizard (needs color selection)
        return self.game_state.trump.value == 14

    def set_trump_color(self, color: Color):
        """Set the trump color when a Wizard is drawn as trump"""
        if self.game_state.trump.value == 14:
            self.game_state.trump = Card(14, color)

    def make_prediction(self, player_index: int, prediction: int):
        """Record a player's prediction for the round"""
        if player_index < 0 or player_index >= len(self.game_state.players):
            raise ValueError("Invalid player index")

        if prediction < 0 or prediction > self.game_state.current_round:
            raise ValueError(f"Prediction must be between 0 and {self.game_state.current_round}")

        self.game_state.players[player_index].called_stiche = prediction


    def play_card(self, player_index: int, card_index: int) -> Card:
        """Play a card for a player"""
        player_turn = (self.game_state.current_player + len(self.game_state.stich)) % len(self.game_state.players)
        if player_index != player_turn:
            raise ValueError("Not this player's turn")

        valid_indices = self.game_state.get_valid_cards(player_index)
        if card_index not in valid_indices:
            raise ValueError("Invalid card selection")

        return self.game_state.play_card(player_index, card_index)

    def end_trick(self) -> int:
        """End the current trick, return the winner index"""
        winner = self.game_state.determine_stich_winner()
        self.game_state.players[winner].gewonnene_stiche += 1
        self.game_state.current_player = winner
        return winner



    def is_game_over(self) -> bool:
        """Check if the game is over"""
        return self.game_state.is_game_over()

    def get_rankings(self) -> List[Tuple[Player, int]]:
        """Get the final rankings"""
        sorted_players = sorted(
            [(player, i) for i, player in enumerate(self.game_state.players)],
            key=lambda x: x[0].score,
            reverse=True
        )
        return sorted_players

