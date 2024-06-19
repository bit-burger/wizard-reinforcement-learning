import discord

from config import tree, client
import config


@tree.command(name="help", description="list all commands and explain them", guild=discord.Object(1205582028905648209))
async def advice(interaction: discord.Interaction):
    embed = discord.Embed(title="All commands:", colour=discord.Colour.blurple())
    command_str = ""
    description_str = ""
    for command in config.commands:
        command_str += f"`{command.name}`\n"
        description_str += f"`{command.description}`\n"
    embed.add_field(name="command", value=command_str)
    embed.add_field(name="description", value=description_str)
    embed.set_author(name=client.user.name, icon_url=client.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)
