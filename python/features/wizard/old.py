from typing import Dict

from discord import app_commands
from discord.ui import Select, View
from config import tree, client
from features.wizard.wizard_game_logic import *
from features.wizard.reinforcement_bot import *
import threading
import asyncio

card_emojis = {
    Color.RED: "🔴",
    Color.GREEN: "🟢",
    Color.BLUE: "🔵",
    Color.YELLOW: "🟡",
    Color.NILL: "⚪",
    14: "🧙",  # Wizard icon
    0: "🤡"  # Jester icon
}

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
games: Dict[int, WizardGame] = {}

@tree.command(name="wizard", description="Initialisiert eine Wizard Runde", guild=discord.Object(1205582028905648209))
async def wizzard(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    if channel_id in games:
        game = games[channel_id]
        if interaction.user.id in [player.user_id for player in game.game_state.players]:
            await interaction.response.send_message("Du bist schon im Spiel.", ephemeral=True)
            return
        if len(game.game_state.players) < PLAYERS_MAX:
            player = Player.from_discord_user(interaction.user)
            game.game_state.add_player(player)
            await interaction.response.send_message(
                player.formatted_name + " ist der Runde beigetreten!")
            embed = discord.Embed(
                title="🎮 New Player Joined!",
                description=player.formatted_name + " ist der Runde beigetreten!",
                color=discord.Color.green()
            )
            await broadcast_to_players(game.game_state.players, "", embed=embed)
        else:
            await interaction.response.send_message(f"Das Spiel ist voll. Maximal {PLAYERS_MAX} Spieler erlaubt.",
                                                    ephemeral=True)
    else:
        wizard_game = WizardGame()
        player = Player.from_discord_user(interaction.user)
        wizard_game.game_state.add_player(player)
        games[channel_id] = wizard_game
        embed = discord.Embed(
            title="🧙‍♂️ Wizard!",
            description="Eine neue Wizard Runde wurde gestartet. Schreibe zum Beitreten /Wizard",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

@tree.command(name="add_ai", description="Fügt einen KI-Spieler zur Wizard Runde hinzu", guild=discord.Object(1205582028905648209))
async def add_ai_player(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    if channel_id not in games:
        await interaction.response.send_message("Kein Spiel initialisiert. Schreibe /wizard", ephemeral=True)
        return

    game = games[channel_id]
    if len(game.game_state.players) >= PLAYERS_MAX:
        await interaction.response.send_message(f"Das Spiel ist voll. Maximal {PLAYERS_MAX} Spieler erlaubt.", ephemeral=True)
        return

    # Create AI bot player
    try:
        # Initialize the RL bot
        ai_bot = WizardRLBot(state_size=120, hidden_size=256, action_size=15)
        # Load trained model if available
        ai_bot.load_full_bot()

        # Create a bot player with a unique ID
        ai_name = f"WizardAI-{len([p for p in game.game_state.players if p.name.startswith('WizardAI')])}"
        bot_player = ai_bot.create_bot_player(ai_name)

        # Store the bot instance for later use
        if not hasattr(game, 'ai_bots'):
            game.ai_bots = {}
        game.ai_bots[ai_name] = ai_bot

        # Add the bot to the game
        game.game_state.add_player(bot_player)

        embed = discord.Embed(
            title="🤖 AI-Spieler beigetreten!",
            description=f"{ai_name} ist der Runde als KI-Spieler beigetreten!",
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed)
        await broadcast_to_players(game.game_state.players, "", embed=embed)

    except Exception as e:
        await interaction.response.send_message(f"Fehler beim Hinzufügen des KI-Spielers: {str(e)}", ephemeral=True)

@tree.command(name="start", description="Startet eine Wizard Runde", guild=discord.Object(1205582028905648209))
async def begin_game(interaction: discord.Interaction):
    await interaction.response.defer()
    if interaction.channel_id not in games:
        await interaction.followup.send("Kein Spiel initialisiert. Schreibe /wizard")
        return

    game = games[interaction.channel_id]
    if len(game.game_state.players) < PLAYERS_MIN:
        await interaction.followup.send(f"Nicht genug Spieler. Es sind {PLAYERS_MIN} Spieler notwendig.")
        return

    embed = discord.Embed(
        title="🚀 Das Wizard Spiel hat gestartet 🎲!",
        color=discord.Color.purple()
    )
    await interaction.followup.send(embed=embed)
    try:
        game.start_game()
        await play_game(interaction, game)
    except ValueError as e:
        await interaction.followup.send(f"Error: {e}")

async def play_game(interaction: discord.Interaction, game: WizardGame):
    """Main game loop that handles all rounds until the game is over"""
    while not game.game_state.is_game_over():
        await play_round(interaction, game)

        # Prepare for next round
        game.game_state.current_round += 1
        # Reset only the stiche counts, not the score
        for player in game.game_state.players:
            player.gewonnene_stiche = 0
            player.called_stiche = 0

    # Game is over - show final results
    await end_game(interaction, game)

async def play_round(interaction: discord.Interaction, game: WizardGame):
    """Play a single round of the game"""
    # Check if trump is a Wizard (needs color selection)
    needs_trump_color = game.start_round()

    trump_display = f"{card_emojis[game.game_state.trump.color]} {get_card_name(game.game_state.trump)}"
    embed = discord.Embed(
        title=f"Runde {game.game_state.current_round}!",
        description=f"Trumpf: {trump_display}",
        color=discord.Color.gold())

    await broadcast_to_players(game.game_state.players, "", embed=embed)

    if needs_trump_color:  # Wizard as trump means the first player chooses the trump color
        starting_player = game.game_state.players[game.game_state.current_player]
        await choose_trump_color(game, starting_player, interaction)

    # Get predictions from players
    for i in range(len(game.game_state.players)):
        player_idx = (game.game_state.current_player + i) % len(game.game_state.players)
        player = game.game_state.players[player_idx]
        await ask_for_prediction(game, player, i)

    # Play tricks until the round is over
    while not game.game_state.is_round_over():
        await play_trick(game, interaction)

    # Update scores at the end of the round
    game.game_state.update_scores() # Update scores
    await display_round_results(interaction, game)
    game.game_state.reset_predictions_and_tricks()



async def choose_trump_color(game: WizardGame, player: Player, interaction: discord.Interaction):
    # Check if this is an AI player
    if player.is_bot and hasattr(game, 'ai_bots'):
        # Find the corresponding AI bot
        ai_bot = None
        for bot_name, bot_instance in game.ai_bots.items():
            if bot_name == player.name:
                ai_bot = bot_instance
                break

        if ai_bot:
            # Make a simple decision for trump color based on the AI's hand
            player_idx = game.game_state.players.index(player)

            # Count colors in hand
            color_counts = {color: 0 for color in [Color.RED, Color.GREEN, Color.BLUE, Color.YELLOW]}
            for card in player.hand:
                if card.color in color_counts:
                    color_counts[card.color] += 1

            # Choose most common color or random if tie/no preference
            if color_counts:
                selected_color = max(color_counts.items(), key=lambda x: x[1])[0]
            else:
                selected_color = random.choice([Color.RED, Color.GREEN, Color.BLUE, Color.YELLOW])

            # Set the trump color
            game.set_trump_color(selected_color)

            # Notify players about the AI's decision
            trump_display = f"{card_emojis[game.game_state.trump.color]} {get_card_name(game.game_state.trump)}"
            embed = discord.Embed(
                title=f"🤖 AI hat Trumpf gewählt",
                description=f"{player.formatted_name} hat {trump_display} als Trumpf gewählt.",
                color=discord.Color.gold()
            )
            await broadcast_to_players(game.game_state.players, "", embed=embed)
            return

    # For human players, continue with existing logic
    class ColorDropdown(Select):
        def __init__(self):
            options = [
                discord.SelectOption(label="Rot", value=str(Color.RED.value), emoji=card_emojis[Color.RED]),
                discord.SelectOption(label="Grün", value=str(Color.GREEN.value), emoji=card_emojis[Color.GREEN]),
                discord.SelectOption(label="Blau", value=str(Color.BLUE.value), emoji=card_emojis[Color.BLUE]),
                discord.SelectOption(label="Gelb", value=str(Color.YELLOW.value), emoji=card_emojis[Color.YELLOW])
            ]
            super().__init__(placeholder="Wähle eine Trumpf Farbe", min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            selected_color = Color(int(self.values[0]))
            game.set_trump_color(selected_color)
            self.view.stop()

    class ColorView(View):
        def __init__(self, timeout: float = None):
            super().__init__(timeout=timeout)
            self.add_item(ColorDropdown())

    view = ColorView()

    user = await client.fetch_user(player.user_id)
    hand = "\n".join(
        [f"{card_emojis[card.value] if card.value in [0, 14] else card_emojis[card.color]} {get_card_name(card)}" for
         card in player.hand])
    embed = discord.Embed(
        title="Wähle eine Trumpf Farbe",
        description="Der Trumpf ist ein Wizard. Wähle die Trumpf Farbe",
        color=discord.Color.gold()
    )
    embed.add_field(name="Deine Hand", value=hand, inline=False)

    await user.send(embed=embed, view=view)
    await view.wait()

    trump_display = f"{card_emojis[game.game_state.trump.color]} {get_card_name(game.game_state.trump)}"
    embed = discord.Embed(
        title=f"Runde {game.game_state.current_round}!",
        description=f"Trumpf: {trump_display}",
        color=discord.Color.gold()
    )
    await broadcast_to_players(game.game_state.players, "", embed=embed)

async def play_trick(game: WizardGame, interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎴 Neuer Stich",
        color=discord.Color.blue()
    )
    await broadcast_to_players(game.game_state.players, "", embed=embed)

    game.game_state.reset_stich()

    # Each player plays a card
    for i in range(len(game.game_state.players)):
        player_idx = (game.game_state.current_player + i) % len(game.game_state.players)
        player = game.game_state.players[player_idx]
        await play_card_for_player(game, player_idx, interaction, i)

    # Determine winner and end trick
    winner_index = game.end_trick()
    winner = game.game_state.players[winner_index]

    # Create embed message for trick winner and status
    embed = discord.Embed(
        title="🏅 Stich Sieger!",
        description=f"{winner.formatted_name} hat den Stich gewonnen!",
        color=discord.Color.green()
    )
    tricks_info = ""
    for player in game.game_state.players:
        tricks_info += f"{player.formatted_name}: {player.gewonnene_stiche}/{player.called_stiche} | Punkte: {player.score}\n"
    embed.add_field(name="Stich Infos", value=tricks_info, inline=False)

    await broadcast_to_players(game.game_state.players, "", embed=embed)
    await interaction.channel.send(embed=embed)

async def play_card_for_player(game: WizardGame, player_idx: int, interaction: discord.Interaction, trick_position: int = -1):
    player = game.game_state.players[player_idx]

    # Check if this is an AI player
    if player.is_bot and hasattr(game, 'ai_bots'):
        # Find the AI bot instance for this player
        ai_bot = None
        for bot_name, bot_instance in game.ai_bots.items():
            if bot_name == player.name:
                ai_bot = bot_instance
                break

        if ai_bot:
            # Let the AI choose a card
            valid_indices = game.game_state.get_valid_cards(player_idx)
            if valid_indices:
                # Get AI state
                state = ai_bot.encode_state(game.game_state, player_idx)

                # Use the AI to select an action
                card_index, q_values = ai_bot.choose_action(game.game_state, player_idx, return_q_values=True)

                # Make sure it's a valid choice
                if card_index not in valid_indices:
                    # Fallback to a random valid card if AI chooses invalid
                    card_index = random.choice(valid_indices)

                # Play the card
                played_card = game.play_card(player_idx, card_index)

                # Get confidence metrics from q_values
                confidence = ""
                if q_values is not None:
                    max_q = max(q_values)
                    min_q = min(q_values)
                    avg_q = sum(q_values) / len(q_values)
                    confidence = f"\nConfidence: {max_q:.2f} | Avg Q: {avg_q:.2f}"

                # Notify players about the AI's move with stats
                embed = discord.Embed(
                    title=f"🤖 {player.formatted_name} hat eine Karte gespielt!",
                    description=f"{player.formatted_name} spielte {card_emojis[played_card.value] if played_card.value in [0, 14] else card_emojis[played_card.color]} {get_card_name(played_card)}\n"
                                f"Valid options: {len(valid_indices)}/{len(player.hand)}{confidence}",
                    color=discord.Color.purple()
                )
                await broadcast_to_players(game.game_state.players, "", embed=embed)
                await interaction.channel.send(embed=embed)

                # Update the trick state
                await update_trick_state(game, interaction, trick_position)
                return

    # For human players, continue with existing logic
    user = await client.fetch_user(player.user_id)

    # Get valid cards that can be played
    valid_card_indices = game.game_state.get_valid_cards(player_idx)

    # Prompt the player to play a card
    hand = "\n".join(
        [f"{card_emojis[card.value] if card.value in [0, 14] else card_emojis[card.color]} {get_card_name(card)}" for card in player.hand])
    embed = discord.Embed(
        title=player.formatted_name + " Du bist dran!",
        description="Spiele eine Karte:",
        color=discord.Color.red()
    )
    embed.add_field(name="Deine Hand", value=hand, inline=False)

    class CardDropdown(Select):
        def __init__(self, valid_indices: List[int]):
            options = [discord.SelectOption(
                label=get_card_name(player.hand[idx]),
                value=str(idx),
                emoji=card_emojis[player.hand[idx].value] if player.hand[idx].value in [0, 14] else card_emojis[player.hand[idx].color]
            ) for idx in valid_indices]
            super().__init__(placeholder="Wähle eine Karte", min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            self.view.value = int(self.values[0])
            self.view.stop()

    class CardView(View):
        def __init__(self, valid_indices: List[int], timeout: float = None):
            super().__init__(timeout=timeout)
            self.value = None
            self.add_item(CardDropdown(valid_indices))

    view = CardView(valid_card_indices)
    await user.send(embed=embed, view=view)
    await view.wait()

    if view.value is not None:
        played_card = game.play_card(player_idx, view.value)
        embed = discord.Embed(
            title=player.formatted_name + " Hat eine Karte gespielt!",
            description=f"{player.formatted_name} spielte {card_emojis[played_card.value] if played_card.value in [0, 14] else card_emojis[played_card.color]} {get_card_name(played_card)}",
            color=discord.Color.purple()
        )
        await broadcast_to_players(game.game_state.players, "", embed=embed)

    # Update the combined trick state
    await update_trick_state(game, interaction, trick_position)


last_trick_message_ids = {}
async def update_trick_state(game: WizardGame, interaction: discord.Interaction, trick_position: int = -1):
    """Update the trick state display"""
    # Create the embed showing the current trick
    stich_text = ""
    for i, card in enumerate(game.game_state.stich):
        player_idx = (game.game_state.current_player + i) % len(game.game_state.players)
        player = game.game_state.players[player_idx]
        stich_text += f"{player.formatted_name}: {card_emojis[card.value] if card.value in [0, 14] else card_emojis[card.color]} {get_card_name(card)}\n"

    embed = discord.Embed(
        title="🎮 Aktueller Stich",
        description=stich_text if stich_text else "Noch keine Karten gespielt",
        color=discord.Color.blue()
    )

    # Add player info
    player_info = ""
    for player in game.game_state.players:
        player_info += f"{player.formatted_name}: {player.gewonnene_stiche}/{player.called_stiche} | Punkte: {player.score}\n"
    embed.add_field(name="Spielerinfo", value=player_info, inline=False)

    # Send to all human players
    for player in game.game_state.players:
        if not player.is_bot:
            try:
                user = await client.fetch_user(player.user_id)
                await user.send(embed=embed)
            except Exception as e:
                print(f"Error sending message to {player.name}: {str(e)}")

    # Send to the channel
    channel_message = await interaction.channel.send(embed=embed)

    # Store the message ID if needed for later updates
    trick_key = f"{interaction.channel_id}_{trick_position}"
    last_trick_message_ids[trick_key] = channel_message.id


async def ask_for_prediction(game: WizardGame, player: Player, index: int):
    # Check if this is an AI player
    if player.is_bot and hasattr(game, 'ai_bots'):
        # Find the corresponding AI bot
        ai_bot = None
        for bot_name, bot_instance in game.ai_bots.items():
            if bot_name == player.name:
                ai_bot = bot_instance
                break

        if ai_bot:
            # Let the AI predict using its neural network
            player_idx = game.game_state.players.index(player)

            # Get valid predictions (enforcing the "last player" rule)
            valid_predictions = game.game_state.get_player_valid_predictions(player_idx)

            # Let the AI choose a prediction from valid options
            if valid_predictions:
                # Use the AI to predict, but ensure it's a valid option
                prediction = ai_bot.predict_tricks(game.game_state, player_idx)
                if prediction not in valid_predictions:
                    prediction = random.choice(valid_predictions)

                game.make_prediction(player_idx, prediction)

                # Notify all players about the AI's prediction
                embed = discord.Embed(
                    title="🤖 KI-Vorhersage",
                    description=f"{player.formatted_name} sagt {prediction} Stich{'e' if prediction != 1 else ''}",
                    color=discord.Color.blue()
                )
                await broadcast_to_players(game.game_state.players, "", embed=embed)
                return

    # For human players, continue with existing logic
    user = await client.fetch_user(player.user_id)
    hand = "\n".join(
        [f"{card_emojis[card.value] if card.value in [0, 14] else card_emojis[card.color]} {get_card_name(card)}"
         for card in player.hand])
    embed = discord.Embed(
        title="🎯 Calle deine Stiche",
        color=discord.Color.red()
    )

    trump_display = card_emojis[game.game_state.trump.color]
    if game.game_state.trump.value in [0, 14]:
        trump_display = card_emojis[game.game_state.trump.value]

    embed.add_field(name="Trumpf",
                    value=f"{trump_display} {get_card_name(game.game_state.trump)}",
                    inline=False)

    embed.add_field(name="Deine Hand", value=hand if hand else "Keine Karten", inline=False)

    # Get valid predictions - enforcing the "last player" rule
    valid_predictions = game.game_state.get_player_valid_predictions(game.game_state.players.index(player))

    # If this is the last player, show the restriction in the message
    player_idx = game.game_state.players.index(player)
    is_last_predictor = (player_idx == len(game.game_state.players) - 1) and all(
        hasattr(p, 'called_stiche') and p.called_stiche >= 0
        for p in game.game_state.players[:player_idx]
    )

    if is_last_predictor:
        total_predicted = sum(p.called_stiche for p in game.game_state.players[:player_idx])
        forbidden_value = game.game_state.current_round - total_predicted
        embed.add_field(
            name="Hinweis",
            value=f"Du darfst nicht **{forbidden_value}** sagen, da sonst die Summe aller Vorhersagen genau der Anzahl der Stiche entspricht.",
            inline=False
        )

    class PredictionDropdown(Select):
        def __init__(self):
            options = []
            for i in valid_predictions:
                options.append(discord.SelectOption(
                    label=str(i),
                    value=str(i),
                    description=f"{i} Stich{'e' if i != 1 else ''}"
                ))
            super().__init__(placeholder="Wie viele Stiche wirst du machen?", min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            prediction = int(self.values[0])
            game.make_prediction(game.game_state.players.index(player), prediction)
            self.view.stop()

            # Notify all players about the prediction
            embed = discord.Embed(
                title="🎯 Vorhersage",
                description=f"{player.formatted_name} sagt {prediction} Stich{'e' if prediction != 1 else ''}",
                color=discord.Color.blue()
            )
            await broadcast_to_players(game.game_state.players, "", embed=embed)

    class PredictionView(View):
        def __init__(self, timeout: float = None):
            super().__init__(timeout=timeout)
            self.add_item(PredictionDropdown())

    view = PredictionView()
    await user.send(embed=embed, view=view)
    await view.wait()


async def broadcast_to_players(players, message, embed=None):
    """Send a message to all players"""
    for player in players:
        if not player.is_bot:  # Only send to human players
            try:
                user = await client.fetch_user(player.user_id)
                if embed:
                    await user.send(embed=embed)
                else:
                    await user.send(message)
            except Exception as e:
                print(f"Error sending message to {player.name}: {str(e)}")

def get_card_name(card):
    """Return a readable string representation of a card."""
    if card.value == 14:
        return "Wizard"
    elif card.value == 0:
        return "Jester"
    else:
        color_names = {
            Color.RED: "Rot",
            Color.GREEN: "Grün",
            Color.BLUE: "Blau",
            Color.YELLOW: "Gelb",
            Color.NILL: "Null"
        }
        return f"{card.value} {color_names[card.color]}"

async def display_round_results(interaction, game):
    """Display the results of the current round."""
    embed = discord.Embed(
        title=f"🏆 Ergebnisse Runde {game.game_state.current_round}",
        color=discord.Color.gold()
    )

    results = ""
    for player in game.game_state.players:
        if player.gewonnene_stiche == player.called_stiche:
            result = f"✅ Richtig vorhergesagt!"
        else:
            result = f"❌ Falsch vorhergesagt!"

        results += f"{player.formatted_name}: {player.gewonnene_stiche}/{player.called_stiche}  -   Score: {player.score}\n"

    embed.add_field(name="Spieler Ergebnisse", value=results, inline=False)
    await interaction.channel.send(embed=embed)
    await broadcast_to_players(game.game_state.players, "", embed=embed)

async def end_game(interaction, game):
    """End the game and display the final results."""
    rankings = game.get_rankings()

    embed = discord.Embed(
        title="🎮 Spiel beendet! Finale Ergebnisse",
        description=f"Das Spiel ist nach {game.game_state.current_round-1} Runden beendet!",
        color=discord.Color.gold()
    )

    leaderboard = ""
    for i, (player, _) in enumerate(rankings):
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "🏅"
        leaderboard += f"{medal} {i+1}. {player.formatted_name}: {player.score} Punkte\n"

    embed.add_field(name="Endstand", value=leaderboard, inline=False)

    await interaction.channel.send(embed=embed)
    await broadcast_to_players(game.game_state.players, "", embed=embed)

    # Clean up the game
    del games[interaction.channel_id]



@tree.command(name="train_nn", description="Trainiert das neuronale Netzwerk für den Wizard-Bot", guild=discord.Object(1205582028905648209))
async def train_neural_network(interaction: discord.Interaction):
    await interaction.response.send_message("Training wird in einem separaten Thread gestartet...")

    # Create a background thread for training
    training_thread = threading.Thread(target=train_bot_thread, args=(interaction.channel.id,))
    training_thread.start()

def train_bot_thread(channel_id):
    """Run training in a separate thread"""
    try:
        bot = train_new_bot()

        # Schedule a message to be sent when training is complete
        async def send_completion_message():
            channel = client.get_channel(channel_id)
            if channel:
                await channel.send("Training abgeschlossen!")

        # Run the async function in the main event loop
        asyncio.run_coroutine_threadsafe(send_completion_message(), client.loop)
    except Exception as e:
        # Handle errors
        async def send_error_message():
            channel = client.get_channel(channel_id)
            if channel:
                await channel.send(f"Fehler beim Training: {str(e)}")

        asyncio.run_coroutine_threadsafe(send_error_message(), client.loop)
