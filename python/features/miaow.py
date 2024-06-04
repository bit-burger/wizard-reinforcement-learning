import discord
import re

from config import client


@client.event
async def message(m: discord.Message):
    if m.id == client.user.id: return
    if re.search("mi*a*o+a*w+|mi+a*o*a*w+", m.content):
        await m.add_reaction("😽")
