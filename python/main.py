import pathlib
from datetime import datetime
import socket
import os
from os import path
import importlib

import discord

from config import client, token

embed = discord.Embed(title="Restarted bot",
                      description=f"Started from: `{socket.gethostname()}`\nFrom directory: `{pathlib.Path().resolve()}`",
                      colour=0x00b0f4)

for file in sorted(os.listdir(os.fsencode("features"))):
    filename = os.fsdecode(file)
    isdir = path.isdir(filename)
    if isdir:
        if not path.exists(f"features/{filename}/__init__.py"):
            continue
    else:
        if filename.endswith(".py"):
            filename = filename[0:-3]
        else:
            continue
    try:
        importlib.import_module(f"features.{filename}")
        embed.add_field(name=filename, value="`loaded successfully`")
        print(f"module '{filename}' loaded successfully")
    except BaseException as e:
        embed.add_field(name=filename, value=f"error: `{e}`")
        print(f"module '{filename}' could not be loaded, error: {e}")


@client.event
async def ready():
    print(f'{client.user} has connected to Discord!')

    guild: discord.Guild = client.get_guild(1205582028905648209)
    channel = guild.get_channel(1247244679381254226)

    embed.timestamp = datetime.now()
    embed.set_author(name=client.user.name, icon_url=client.user.display_avatar.url)
    embed.set_footer(text=client.user.name)
    await channel.send(embed=embed)


client.run(token)
