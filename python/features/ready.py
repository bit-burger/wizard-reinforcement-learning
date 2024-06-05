from datetime import datetime
import discord
import platform
import socket
import pathlib

from config import client


@client.event
async def ready():
    guild: discord.Guild = client.get_guild(1205582028905648209)
    channel = guild.get_channel(1247244679381254226)
    embed = discord.Embed(title="Restarted bot",
                          description=f"Started from: `{socket.gethostname()}`\nFrom directory: `{pathlib.Path().resolve()}`",
                          colour=0x00b0f4,
                          timestamp=datetime.now())

    embed.set_author(name="Quandale sein Bot", icon_url=client.user.avatar.url)

    embed.set_footer(text="Quandale sein Bot")

    await channel.send(embed=embed)
