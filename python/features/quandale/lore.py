import os

import discord
import json

from config import tree

script_dir = os.path.dirname(os.path.abspath(__file__))
lore_path = os.path.join(script_dir, 'quandale_lore.json')
report_path = os.path.join(script_dir, 'quandale_police_report.json')
with open(lore_path, 'r') as f:
    lore_data = json.load(f)

with open(report_path, 'r') as f:
    report_data = json.load(f)


@tree.command(name="lore", description="Quandale lore", guild=discord.Object(1205582028905648209))
async def lore(interaction: discord.Interaction):
    await interaction.response.send_message(lore_data[0])
    for text in lore_data[1:]:
        await interaction.followup.send(text)


@tree.command(name="police_report", description="Quandale Police Report", guild=discord.Object(1205582028905648209))
async def police_report(interaction: discord.Interaction):
    await interaction.response.send_message(report_data[0])
    for entry in report_data[1:]:
        await interaction.followup.send(entry)