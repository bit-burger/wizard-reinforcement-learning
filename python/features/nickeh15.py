import discord
import json
import random

from config import tree

with open('resources/fortnite_quotes.json', 'r') as f:
    quotes = json.load(f)


@tree.command(name="advice", description="Gives you advice 🙀", guild=discord.Object(1205582028905648209))
async def advice(interaction: discord.Interaction):
    quote = random.choice(quotes)
    await interaction.response.send_message(quote)
