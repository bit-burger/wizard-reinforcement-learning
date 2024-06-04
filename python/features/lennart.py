import discord
import re

from config import client


@client.event
async def message(m: discord.Message):
    if m.id == client.user.id: return
    if re.search("wiz?zard", m.content, re.RegexFlag.IGNORECASE):
        emojis = ["🧙"]

        for emoji in emojis:
            await m.add_reaction(emoji)
