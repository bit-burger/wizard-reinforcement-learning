import discord

from python.config import client
import discord.ext

def has_ole(m: discord.Message):
    if "ole" in m.content:
        return True
    for mention in m.mentions:
        if mention.id == 724949595330969643:
            return True
    return False

@client.event
async def message(m: discord.Message):
    if m.id == client.user.id: return
    if has_ole(m):
        await m.add_reaction("😄")
