import os

import discord
import json
import random

from config import tree

script_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(script_dir, 'fortnite_quotes.json')
with open(json_path, 'r') as f:
    quotes = json.load(f)

quote_used = {quote: False for quote in quotes}


@tree.command(name="advice", description="Gives you advice", guild=discord.Object(1205582028905648209))
async def advice(interaction: discord.Interaction):
    if all(quote_used.values()):
        quote_used.update({quote: False for quote in quotes})
    unused_quotes = [quote for quote, used in quote_used.items() if not used]
    quote = random.choice(unused_quotes)
    quote_used[quote] = True
    await interaction.response.send_message(quote)
