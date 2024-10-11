import discord

from config import client

SAVED_GUILD_NAME = "Quandale Dingle"


@client.event
async def guild_update(before: discord.Guild, after: discord.Guild):
    if after.name != SAVED_GUILD_NAME:
        await after.edit(name=SAVED_GUILD_NAME)
