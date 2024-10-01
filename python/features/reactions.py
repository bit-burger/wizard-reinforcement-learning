import re

import discord
from config import client
import discord.ext


def has_ole(m: discord.Message):
    if re.search("ole", m.content, re.IGNORECASE):
        return True
    for mention in m.mentions:
        if mention.id == 724949595330969643:
            return True
    return False


@client.event
async def message(m: discord.Message):
    if m.id == client.user.id: return
    if m.author.bot: return
    if has_ole(m):
        await m.add_reaction("😄")
    if re.search("mi*a*o+a*w+|mi+a*o*a*w+", m.content, re.IGNORECASE):
        await m.add_reaction("😽")
    if re.search("maschinenbau|(^|\\s)maschi($|\\s)", m.content, re.IGNORECASE):
        await m.reply(content="Karohemd und Samenstau - ich studier Maschinenbau.")
    if re.search("elektrotechnik|(^|\\s)eti($|\\s)", m.content, re.IGNORECASE):
        await m.reply(content="Haare lang, Arme schmächtig - ich studier Elektrotechnik.")
