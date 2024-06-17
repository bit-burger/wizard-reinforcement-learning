import discord
import json

from config import tree

with open('resources/quandale_lore.json', 'r') as f:
    lore = json.load(f)

with open('resources/quandale_police_report.json', 'r') as f:
    report = json.load(f)


@tree.command(name="lore", description="Quandale lore", guild=discord.Object(1205582028905648209))
async def lore(interaction: discord.Interaction):
    for text in lore:
        await interaction.response.send_message(text)


@tree.command(name="police report", description="Quandale Police Report", guild=discord.Object(1205582028905648209))
async def police_report(interaction: discord.Interaction):
    for entry in report:
        await interaction.response.send_message(entry)
