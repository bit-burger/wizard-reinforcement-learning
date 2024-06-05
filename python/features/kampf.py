import time

import discord
from config import client
import discord.ext


@client.event
async def message(m: discord.Message):
    if m.id == client.user.id: return
    if "kampf" in m.content.lower() and len(m.mentions) >= 1 and isinstance(m.mentions[0], discord.Member):
        mention = m.mentions[0]
        await m.channel.send(f"Ich kämpft gegen <@{mention.id}>!")
        await m.channel.send("3...")
        time.sleep(1)
        await m.channel.send("2...")
        time.sleep(1)
        await m.channel.send("1...")
        time.sleep(1)
        await m.channel.send("Kampf beginnt!")
        time.sleep(1)
        await mention.edit(mute=True, deafen=True)
        channels = [channel for channel in list(m.guild.channels) if channel.type == discord.ChannelType.voice and channel.id != m.channel.id]
        for i in range (5):
            for channel in channels:
                await mention.move_to(channel)
                time.sleep(1)
            await mention.move_to(None)