from datetime import datetime

import discord

from config import client


@client.event
async def message(m: discord.Message):
    if m.author == client.user: return
    embed = discord.Embed(title="Member sent a message",
                          description="```\n" + m.content + "\n```" if m.content != "" else None,
                          timestamp=datetime.now())
    embed.set_author(icon_url=m.author._user.display_avatar.url, name=m.author.name)
    embed.set_footer(text=f"user id: {m.author.id}, channel id: {m.channel.id}")
    guild: discord.Guild = client.get_guild(1205582028905648209)
    channel = guild.get_channel(1271237576006701240)
    await channel.send(embeds=[embed] + m.embeds)

# @client.event
# async def raw_message_edit(event: discord.RawMessageUpdateEvent):
#     channel = await client.get_guild(event.guild_id).fetch_channel(event.channel_id)
#     m = await channel.fetch_message(event.message_id)
#     if m.author == client.user: return
#     guild: discord.Guild = client.get_guild(1205582028905648209)
#     channel = guild.get_channel(1247244679381254226)
