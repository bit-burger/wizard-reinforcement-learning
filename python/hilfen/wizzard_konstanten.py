import enum
from dataclasses import dataclass, field
from typing import List

DECK_SIZE = 60
MAX_MAX_HAND_SIZE = 30
MAX_PLAYERS = 8

PLAYERS = 0
ROUNDS = 0
MAX_HAND_SIZE = 0

class Color(enum.Enum):
    RED = 0
    GREEN = 1
    BLUE = 2
    YELLOW = 3
    NILL = 4

@dataclass
class Card:
    value: int
    color: Color

@dataclass
class Player:
    called_stiche: int = 0
    gewonnene_stiche: int = 0
    name: str = ""
    hand: List[Card] = field(default_factory=lambda: [Card(0, Color.NILL)] * MAX_MAX_HAND_SIZE)
    score: int = 0

@dataclass
class Outputdata:
    hand: List[Card] = field(default_factory=lambda: [Card(0, Color.NILL)] * MAX_MAX_HAND_SIZE)

trick = Card(0, Color.NILL)
trump = Card(0, Color.NILL)
deck = [Card(0, Color.NILL)] * DECK_SIZE
players = [Player() for _ in range(MAX_PLAYERS)]
current_round = 0