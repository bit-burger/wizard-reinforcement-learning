import discord
import json

from config import tree

with open('quandale_lore.json', 'r') as f:
    lore_data = json.load(f)

with open('quandale_police_report.json', 'r') as f:
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