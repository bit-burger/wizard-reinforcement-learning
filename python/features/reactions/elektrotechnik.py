import discord
import re

from config import client


@client.event
async def message(m: discord.Message):
    if m.author.bot: return
    if re.search("elektrotechnik|(^|\\s)eti($|\\s)", m.content, re.IGNORECASE):
        await m.reply(content="Haare lang, Arme schmächtig - ich studier Elektrotechnik.")
