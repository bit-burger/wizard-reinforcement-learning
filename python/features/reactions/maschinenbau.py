import discord
import re

from config import client


@client.event
async def message(m: discord.Message):
    if m.author.bot: return
    if re.search("maschinenbau|(^|\\s)maschi($|\\s)", m.content, re.IGNORECASE):
        await m.reply(content="Karohemd und Samenstau - ich studier Maschinenbau.")
