from __future__ import annotations

import json
import random
from enum import Enum
from operator import truediv
from typing import Iterator

import discord
from discord import ui, Interaction

from config import client, tree
from helpers.reactive import ReactiveApplicationView, run_application, Button, run_application_on_message

with open("features/wizard/neu/card_deck_info.json", 'r') as file:
    card_deck_info_json = json.load(file)

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
    Color.NILL: "⚪",
    14: "🧙",  # Wizard icon
    0: "🤡"  # Jester icon
}


class Card:
    def __init__(self, value: int, color: Color):
        self.value = value
        self.color = color


class GameState:
    def __init__(self, players):
        self.players: list["WizardPlayerApplication"] = players
        self.current_round = 0
        self.trump: Card | None = None
        self.current_player = 0
        self.stich: list[Card] = []
        self.stich_number = 0
        self.calling = True
        self.suit_card: Card | None = None
        self.title = "1. Runde - 🎯 Calle deine Stiche"
        self.game_end = False
        self._new_round()

    @property
    def is_trump_wizard(self):
        return self.trump.value == 14

    @property
    def start_player(self):
        return (self.current_round - 1) % len(self.players)

    def _deal_cards(self):
        deck = [Card(i % 15, Color(i % 4)) for i in range(DECK_SIZE)]
        random.shuffle(deck)
        for player in self.players:
            player.hand = []
        for _ in range(self.current_round):
            for player in self.players:
                player.hand.append(deck.pop())
        if len(deck) > 0:
            self.trump = deck.pop()
        else:
            self.trump = None

    def _new_round(self):
        self.current_round += 1
        self.stich_number = 0
        for player in self.players:
            player.reset_round()
        if self.current_round * len(self.players) == DECK_SIZE:
            self.game_end = True
        else:
            self._deal_cards()
            self.calling = True
            self.title = f"{self.current_round}. round - 🎯 call your stiche"

    def _next_player(self):
        self.current_player = (self.current_player + 1) % len(self.players)

    def call_stich(self, how_many: int):
        player = self.players[self.current_player]
        player.called_stiche = how_many
        self._next_player()
        if self.current_player == self.start_player:
            self.calling = False

    def _next_stich(self):
        winner = self.determine_stich_winner()
        winner.won_stiche += 1
        self.stich_number += 1
        if self.stich_number == self.current_round:
            self._new_round()
        else:
            self.title = f"{self.current_round}. round - {winner.ping_player} has won the stich"

    def play_card(self, card_index: int):
        played_card = self.players[self.current_player].hand.pop(card_index)
        self.stich.append(played_card)
        self._next_player()
        if self.current_player == self.start_player:
            self._next_stich()

    def determine_stich_winner(self) -> "WizardPlayerApplication":
        winning_card = None
        winning_player = -1

        for i, card in enumerate(self.stich):
            if card.value == 14:  # Wizard card
                return (self.current_player + i) % len(self.players)
            if winning_card is None:
                winning_card = card
                winning_player = i
            elif winning_card.value == 0:  # Jester card
                winning_card = card
                winning_player = i
            elif card.value != 0:
                if winning_card.color == self.trump.color:
                    if card.color == self.trump.color and card.value > winning_card.value:
                        winning_card = card
                        winning_player = i
                elif card.color == self.trump.color:
                    winning_card = card
                    winning_player = i
                elif card.color == winning_card.color and card.value > winning_card.value:
                    winning_card = card
                    winning_player = i

        return self.players[(self.current_player + winning_player) % len(self.players)]


class WizardRoomApplication(ReactiveApplicationView):
    admin_id: int
    player_applications: list["WizardPlayerApplication"]
    started = False
    game_state: GameState | None

    async def update_players(self):
        for player in self.player_applications:
            await player.set_state()

    def __init__(self, admin_id: int):
        super().__init__(ephemeral=False)
        self.admin_id = admin_id
        app = WizardPlayerApplication(admin_id, 0)
        app.room = self
        self.player_applications = [app]
        self.game_state = None

    async def start_app(self, i):
        if i.user.id != self.admin_id:
            await i.response.send_message(embed=discord.Embed(color=discord.Color.red(),
                                                              description=f"only <@{self.admin_id}> can start the round"),
                                          ephemeral=True)
        else:
            self.started = True
            self.game_state = GameState(self.player_applications)
            await run_application(i, self.player_applications[0])
            await self.set_state()
            await self.update_players()

    async def join(self, i):
        if i.user.id in map(lambda app: app.user_id, self.player_applications):
            await i.response.send_message(
                embed=discord.Embed(color=discord.Color.red(), description=f"you are already in this room!"),
                ephemeral=True)
        else:
            app = WizardPlayerApplication(i.user.id, len(self.player_applications))
            app.room = self
            self.player_applications.append(app)
            await run_application(i, app)
            await self.set_state()

    def render(self) -> Iterator[str | discord.Embed | ui.Item]:
        # todo: 2 -> 3
        waiting = PLAYERS_MIN - len(self.player_applications)
        players = "\n\n**players:** " + ", ".join(map(lambda player: player.ping_player, self.player_applications))
        if not self.started:
            if waiting > 0:
                yield discord.Embed(title="Wizard 🧙‍♂️",
                                    description=f"waiting for at least {waiting} more player{"s" if waiting > 1 else ""}...{players}")
            else:
                yield discord.Embed(title="Wizard 🧙‍♂️",
                                    description=f"waiting for <@{self.admin_id}> to start the game{players}")
            yield Button(_callable=self.start_app, label="start", style=discord.ButtonStyle.green, disabled=waiting > 0)
            yield Button(_callable=self.join, label="join", style=discord.ButtonStyle.blurple,
                         disabled=len(self.player_applications) == PLAYERS_MAX)
        else:
            yield discord.Embed(title="Wizard 🧙‍♂️", description=f"Game has already begun!{players}")


class WizardPlayerApplication(ReactiveApplicationView):
    user_id: int
    player_number: int
    room: WizardRoomApplication
    hand: list[Card]
    called_stiche: int
    won_stiche: int
    score: int

    def __init__(self, user_id, player_number):
        self.user_id = user_id
        self.player_number = player_number
        self.hand = []
        self.called_stiche = 0
        self.won_stiche = 0
        self.score = 0
        super().__init__(ephemeral=True)

    @property
    def ping_player(self):
        return f"<@{self.user_id}>"

    def reset_round(self):
        if self.called_stiche == self.won_stiche:
            self.score += 20 + self.won_stiche * 10
        self.hand = []
        self.called_stiche = 0
        self.won_stiche = 0

    def get_card_name(self, card: Card):
        if card.value == 0:
            return "joker"
        if card.value == 14:
            return "wizard"
        colors = {Color.RED: "red", Color.GREEN: "green", Color.BLUE: "blue", Color.YELLOW: "yellow"}
        return f"{colors[card.color]}_{card.value}"

    def get_card(self, card: Card) -> str:
        # values = {14: "Wizard", 0: "Narre"}
        # if card.value in values:
        #     return values[card.value]
        # colors = {Color.RED: "Rot", Color.GREEN: "Grün", Color.BLUE: "Blau", Color.YELLOW: "Gelb", Color.NILL: "Weiß"}
        # colors = {Color.RED: "red", Color.GREEN: "green", Color.BLUE: "blue", Color.YELLOW: "yellow"}
        # return f"{card.value}"
        name = self.get_card_name(card)
        debug = card_deck_info_json[name]
        return f"<:{name}:{card_deck_info_json[name]}>"


    def render(self) -> Iterator[str | discord.Embed | ui.Item]:
        state = self.room.game_state
        if not state:
            yield discord.Embed(description="Wait for the admin to begin...")
            return

        embed = discord.Embed(
            title=f"Wizard - Runde {state.current_round}                                                            .",
            color=discord.Color.blue()
        )

        # Trump and current stich information
        #trump_display = f"{card_emojis[state.trump.value] + card_emojis[state.trump.color] if state.trump.value in [0, 14] else card_emojis[state.trump.color]} {state.trump.value}"
        trump_display = self.get_card(state.trump)
        # embed.add_field(name="Trumpf", value=trump_display, inline=False)

        # Current stich
        player_str = ""
        stiche_str = ""
        card_str = ""
        for i in range(len(state.players)):
            player_index = (state.start_player + i) % len(state.players)
            p = state.players[player_index]
            #card_info = f"{card_emojis[state.stich[player_index].value] if state.stich[player_index].value in [0, 14] else card_emojis[state.stich[player_index].color]} {self.get_card(state.stich[player_index])}" if player_index < len(state.stich) else "----"
            card_info = f"{self.get_card(state.stich[player_index])}" if player_index < len(state.stich) else "----"
            player_name = f"**{p.ping_player}**" if p == self else p.ping_player
            player_str += f"{player_name}  \n [{p.score}] {p.won_stiche}/{p.called_stiche}\n"
            stiche_str += f"{p.won_stiche}/{p.called_stiche}\n"
            card_str += f"{card_info}\n"
        embed.add_field(
            name=f"Stich                                                                 Trumpf: {trump_display}",
            value=" ", inline=False)
        embed.add_field(name="", value=player_str, inline=True)
        embed.add_field(name="", value=stiche_str, inline=True)
        embed.add_field(name="", value=card_str, inline=True)

        # Player's hand
        hand = "\n".join(
            [self.get_card(card) for card in self.hand])
        embed.add_field(name="Deine Hand", value=hand or "Keine Karten", inline=False)

        yield embed


@tree.command(name="wizzard", description="miaow😺", guild=discord.Object(1205582028905648209))
async def wizzard(interaction: discord.Interaction):
    await run_application(interaction, WizardRoomApplication(interaction.user.id))
