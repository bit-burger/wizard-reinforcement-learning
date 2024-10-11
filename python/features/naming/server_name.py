import discord

from config import client

SAVED_GUILD_NAME = "Quandale Dingle"

@client.event
async def guild_update(before: discord.Guild, after: discord.Guild):
    if before.name != after.name:
        await after.edit(name=SAVED_GUILD_NAME)