import discord
from discord import app_commands
import asyncio
import random
from enum import Enum
from typing import List, Dict

from discord.ui import Select, View

from config import tree, client

# Constants
DECK_SIZE = 60
PLAYERS_MIN = 1
PLAYERS_MAX = 6


class Color(Enum):
    RED = 0
    GREEN = 1
    BLUE = 2
    YELLOW = 3
    NILL = 4


card_emojis = {
    Color.RED: "🔴",
    Color.GREEN: "🟢",
    Color.BLUE: "🔵",
    Color.YELLOW: "🟡",
    Color.NILL: "⚪"
}


class Card:
    def __init__(self, value: int, color: Color):
        self.value = value
        self.color = color


class Player:
    def __init__(self, user: discord.User):
        self.user = user
        self.name = user.name
        self.score = 0
        self.hand: List[Card] = []
        self.called_stiche = 0
        self.gewonnene_stiche = 0


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



    async def broadcast_to_players(self, message: str, embed=None):
        for player in self.players:
            await player.user.send(message, embed=embed)

    def initialize_players(self, player_names: List[str]):
        self.players = [Player(name) for name in player_names]

    def shuffle_deck(self):
        self.deck = [Card(i % 15, Color(i % 4)) for i in range(DECK_SIZE)]
        random.shuffle(self.deck)

    def deal_cards(self):
        for player in self.players:
            player.hand = []
        for _ in range(self.current_round):
            for player in self.players:
                player.hand.append(self.deck.pop())

    def play_card(self, player_index: int, card_index: int) -> Card:
        played_card = self.players[player_index].hand.pop(card_index)
        self.stich.append(played_card)
        return played_card

    def determine_stich_winner(self) -> int:
        winning_card = self.stich[0]
        winning_player = 0
        for i, card in enumerate(self.stich[1:], 1):
            if (card.color == winning_card.color and card.value > winning_card.value) or \
                    (card.color == self.trump.color and winning_card.color != self.trump.color) or \
                    (card.value == 14):  # Wizard always wins
                winning_card = card
                winning_player = i
        return (self.start_player + winning_player) % len(self.players)

    def reset_stich(self):
        self.stich = []

    def is_round_over(self) -> bool:
        return len(self.players[0].hand) == 0

    def is_game_over(self) -> bool:
        return self.current_round > 15


intents = discord.Intents.default()
intents.message_content = True


class WizzardClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


bot = WizzardClient()
games: Dict[int, GameState] = {}


@tree.command(name="wizzard", description="Start a new Wizzard game", guild=discord.Object(1205582028905648209))
async def wizzard(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    if channel_id in games:
        game = games[channel_id]
        if interaction.user in [player.user for player in game.players]:
            await interaction.response.send_message("You have already joined the current game.", ephemeral=True)
            return
        if len(game.players) < PLAYERS_MAX:
            game.players.append(Player(interaction.user))
            await interaction.response.send_message(interaction.user.name.replace("_","\\_").replace("_", "\\_")+" has joined the game!")
            embed = discord.Embed(
                title="🎮 New Player Joined!",
                description=interaction.user.name.replace("_","\\_")+" has joined the game!",
                color=discord.Color.green()
            )
        else:
            await interaction.response.send_message(f"The game is full. Maximum {PLAYERS_MAX} players allowed.",
                                                    ephemeral=True)
    else:
        game = GameState()
        game.players.append(Player(interaction.user))
        games[channel_id] = game
        embed = discord.Embed(
            title="🧙‍♂️ Wizzard Game Started!",
            description="A new Wizzard game has been started! Use /wizzard to join.",
            color=discord.Color.blue()
        )
        await interaction.channel.send(embed=embed)


@tree.command(name="begin", description="Begin the Wizzard game", guild=discord.Object(1205582028905648209))
async def begin_game(interaction: discord.Interaction):
    if interaction.channel_id not in games:
        await interaction.response.send_message("No game in progress. Start a game with /wizzard", ephemeral=True)
        return

    game = games[interaction.channel_id]
    if len(game.players) < PLAYERS_MIN:
        await interaction.response.send_message(f"Not enough players. At least {PLAYERS_MIN} players are required.",
                                                ephemeral=True)
        return

    game.current_round = 1
    embed = discord.Embed(
        title="🚀 The Game Begins!",
        description="The Wizzard game has begun! Good luck to all players! 🎲",
        color=discord.Color.purple()
    )
    await interaction.channel.send(embed=embed)
    await play_round(interaction, game)


async def play_round(interaction: discord.Interaction, game: GameState):
    game.shuffle_deck()
    game.deal_cards()
    game.trump = game.deck[0]

    embed = discord.Embed(
        title=f"Round {game.current_round}!",
        description=f"Trump: {card_emojis[game.trump.color]} {get_card_name(game.trump)}",
        color=discord.Color.gold()
    )
    await game.broadcast_to_players("", embed=embed)
    # Vorhersagen von allen Spielern einholen
    for i in range(len(game.players)):
        current_player = game.players[(i + game.current_round - 1) % len(game.players)]
        await ask_for_prediction(game, current_player, i)

    # Karten spielen bis keine mehr auf der Hand sind
    while not game.is_round_over():
        await play_stich(game, interaction)

    # Scores aktualisieren nach der Runde
    await display_round_results(interaction, game)

    if game.is_game_over():
        await end_game(interaction, game)
    else:
        game.current_round += 1
        game.start_player = (game.start_player + 1) % len(game.players)
        await play_round(interaction, game)


async def play_stich(game: GameState, interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎴 New Stich",
        color=discord.Color.blue()
    )
    embed.add_field(name="Trump Card", value=card_emojis[game.trump.color] + " " + get_card_name(game.trump), inline=False)
    await game.broadcast_to_players("", embed=embed)
    game.reset_stich()

    # Each player plays a card
    for i in range(len(game.players)):
        current_player = game.players[(game.start_player + i) % len(game.players)]
        await play_card_for_player(game, current_player, interaction)

        # Broadcast the current state of the "stich" to all players
        await update_stich_state(game, interaction)

    # Determine the suit to follow based on the first non-Jester and non-Wizard card
    suit_to_follow = None
    for card in game.stich:
        if card.value not in [0, 14]:  # Not a Jester or Wizard
            suit_to_follow = card.color
            break

    # Determine the winner of the stich
    winner_index = game.determine_stich_winner()
    game.players[winner_index].gewonnene_stiche += 1

    # Create embed message for stich winner and tricks information
    embed = discord.Embed(
        title="🏅 Stich Winner!",
        description=game.players[winner_index].name.replace("_", "\\_") + " won this stich!",
        color=discord.Color.green()
    )
    tricks_info = ""
    for player in game.players:
        tricks_info += player.name.replace('_', '\\_')+": "+ str(player.gewonnene_stiche)+"/"+str(player.called_stiche)+" | Score: " + str(player.score)+"\n"
    embed.add_field(name="Tricks Information", value=tricks_info, inline=False)

    await game.broadcast_to_players("", embed=embed)
    await interaction.channel.send(embed=embed)

    # The winner of the stich plays the next card
    game.start_player = winner_index

async def play_card_for_player(game: GameState, player: Player, interaction: discord.Interaction):
    global card_emojis

    hand = "\n".join([f"{card_emojis[card.color]} {get_card_name(card)}" for card in player.hand])
    embed = discord.Embed(
        title=player.name.replace("_", "\\_") + " it's your turn!",
        description="Choose a card to play from your hand:",
        color=discord.Color.red()
    )
    embed.add_field(name="Your Hand", value=hand, inline=False)
    # Add information about called tricks and needed tricks
    tricks_info = ""
    for p in game.players:
        tricks_info += p.name.replace("_", "\\_") + ": " + str(p.gewonnene_stiche) + "/" + str(p.called_stiche) + "\n"
    embed.add_field(name="Tricks Information", value=tricks_info, inline=False)

    # Determine allowed cards
    if game.stich:
        first_card_suit = game.stich[0].color
        allowed_cards = [card for card in player.hand if card.color == first_card_suit and card.value not in [0, 14]]
        if not allowed_cards:
            allowed_cards = player.hand
    else:
        allowed_cards = player.hand

    class CardDropdown(Select):
        def __init__(self, player: Player, allowed_cards: List[Card]):
            options = [discord.SelectOption(label=get_card_name(card), value=str(i)) for i, card in
                       enumerate(player.hand) if card in allowed_cards]
            super().__init__(placeholder="Select", min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            self.view.value = int(self.values[0])
            self.view.stop()

    class CardView(View):
        def __init__(self, player: Player, allowed_cards: List[Card], timeout: float = None):
            super().__init__(timeout=timeout)
            self.value = None
            self.add_item(CardDropdown(player, allowed_cards))

    view = CardView(player, allowed_cards)
    await player.user.send(embed=embed, view=view)
    await view.wait()

    if view.value is not None:
        played_card = game.play_card(game.players.index(player), view.value)
        embed = discord.Embed(
            title=player.name.replace("_", "\\_") + " played a card!",
            description=player.name.replace("_", "\\_") + " played " + card_emojis[played_card.color] + " " + get_card_name(played_card),
            color=discord.Color.purple()
        )
        # await game.broadcast_to_players("", embed=embed)

async def update_stich_state(game: GameState, interaction: discord.Interaction):
    global card_emojis

    stich_info = ""
    for i in range(len(game.players)):
        player = game.players[(game.start_player + i) % len(game.players)]
        card_info = f"{card_emojis[game.stich[i].color]} {get_card_name(game.stich[i])}" if i < len(game.stich) else "No card played"
        stich_info += player.name.replace("_","\\_")+" [Tricks: "+str(player.gewonnene_stiche)+"/"+str(player.called_stiche) +" | Score: "+str(player.score)+"] : "+ card_info+"\n"
    embed = discord.Embed(
        title="Current Stich State",
        description=stich_info,
        color=discord.Color.orange()
    )



    await game.broadcast_to_players("", embed=embed)
    await interaction.channel.send(embed=embed)


async def ask_for_prediction(game: GameState, player: Player, index: int):
    card_emojis = {
        Color.RED: "🔴",
        Color.GREEN: "🟢",
        Color.BLUE: "🔵",
        Color.YELLOW: "🟡",
        Color.NILL: "⚪"
    }

    hand = "\n".join([f"{card_emojis[card.color]} {get_card_name(card)}" for card in player.hand])
    embed = discord.Embed(
        title="🎯 Predict Your Tricks!",
        description=f"How many tricks do you think you'll win this round?",
        color=discord.Color.red()
    )
    embed.add_field(name="Trump Card", value=card_emojis[game.trump.color]+" "+get_card_name(game.trump), inline=False)
    embed.add_field(name="Your Hand", value=hand, inline=False)
    #determine, if its the last player to predict

    total_predicted = sum([p.called_stiche for p in game.players])
    max_value = game.current_round
    if index == len(game.players) - 1:
        options = [i for i in range(max_value + 1) if i != max_value - total_predicted]
    else:
        options = list(range(max_value + 1))

    class PredictDropdown(Select):
        def __init__(self, options: List[int]):
            select_options = [discord.SelectOption(label=str(i), value=str(i)) for i in options]
            super().__init__(placeholder="Select number of tricks...", min_values=1, max_values=1,
                             options=select_options)

        async def callback(self, interaction: discord.Interaction):
            self.view.value = int(self.values[0])
            self.view.stop()

    class PredictView(View):
        def __init__(self, options: List[int], timeout: float = None):  # Timeout auf None gesetzt
            super().__init__(timeout=timeout)
            self.value = None
            self.add_item(PredictDropdown(options))

    view = PredictView(options)
    await player.user.send(embed=embed, view=view)
    await view.wait()

    if view.value is not None:
        player.called_stiche = view.value
        embed = discord.Embed(
            title="🎯 Prediction Made!",
            description=player.name.replace("_","\\_")+" predicted "+str(view.value)+" tricks for this round.",
            color=discord.Color.dark_blue()
        )
        await game.broadcast_to_players(f"", embed=embed)


async def display_round_results(interaction: discord.Interaction, game: GameState):
    # Update scores and reset predictions and won tricks
    for player in game.players:
        if player.gewonnene_stiche == player.called_stiche:
            player.score += 20 + 10 * player.called_stiche
        else:
            player.score -= 10 * abs(player.gewonnene_stiche - player.called_stiche)

    # Create embed message for round results
    embed = discord.Embed(
        title=f"📊 Round {game.current_round} Results",
        color=discord.Color.gold()
    )
    for player in game.players:
        embed.add_field(
            name=player.name.replace("_","\\_"),
            value=f"Predicted Tricks: {player.called_stiche}\nWon Tricks: {player.gewonnene_stiche}\nScore: {player.score}",
            inline=False
        )
        # Reset predictions and won tricks after displaying them
        player.gewonnene_stiche = 0
        player.called_stiche = 0
    await game.broadcast_to_players("", embed=embed)
    await interaction.channel.send(embed=embed)


async def end_game(interaction: discord.Interaction, game: GameState):
    final_scores = sorted(game.players, key=lambda p: p.score, reverse=True)
    winner = final_scores[0]

    embed = discord.Embed(
        title="🏆 Game Over!",
        description="Congratulations to "+winner.name.replace("_","\\_")+" with "+ str(winner.score)+" points!",
        color=discord.Color.gold()
    )
    for player in final_scores:
        embed.add_field(
            name=player.name.replace("_","\\_"),
            value=f"Final Score: {player.score}",
            inline=False
        )

    await interaction.channel.send(embed=embed)

    del games[interaction.channel_id]


def get_card_name(card: Card) -> str:
    colors = {Color.RED: "Red", Color.GREEN: "Green", Color.BLUE: "Blue", Color.YELLOW: "Yellow", Color.NILL: "White"}
    values = {14: "Wizard", 0: "Jester"}
    return f"{values.get(card.value, str(card.value))} of {colors[card.color]}"
