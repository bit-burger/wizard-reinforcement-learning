import pathlib
from time import time
from datetime import datetime
import socket
import os
from os import path
import importlib

import discord
import config

module_str = ""
status_str = ""
time_to_load_str = ""

module_error_str = ""

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

    module_str += f"`{filename}`" + "\n"
    begin_time = time()
    try:
        importlib.import_module(f"features.{filename}")
        status_str += "`loaded successfully`" + "\n"
        print(f"module '{filename}' loaded successfully")
    except BaseException as e:
        status_str += f"`loaded unsuccessful`" + "\n"
        module_error_str += f"`{filename}`: `{e}`" + "\n\n"
        print(f"module '{filename}' could not be loaded, error: {e}")
    finally:
        time_to_load_str += f"`{(time() - begin_time) * 1000:.3f}msec`\n"

has_connected = False


@config.client.event
async def ready():
    global has_connected
    guild: discord.Guild = config.client.get_guild(1205582028905648209)
    channel = guild.get_channel(1247244679381254226)
    if not has_connected:
        has_connected = True

        embed = discord.Embed(title="Restarted bot",
                              description=f"**  From machine**: `{socket.gethostname()}`\n\n**From directory**: `{pathlib.Path().resolve()}`\n\n**Modules loaded**:",
                              colour=0x00b0f4,
                              timestamp=datetime.now())

        embed.add_field(name="module", value=module_str)
        embed.add_field(name="status", value=status_str)
        embed.add_field(name="time to load", value=time_to_load_str)

        if module_error_str != "":
            embed.add_field(name="module errors:", value=module_error_str, inline=False)

        embed.set_author(name=config.client.user.name, icon_url=config.client.user.display_avatar.url)
        embed.set_footer(text=config.client.user.name)

        commands_str = ""
        try:
            config.commands = await config.tree.sync(guild=guild)
            for command in config.commands:
                commands_str += f"`{command.name}`\n"
                print(f"commands '{command.name}' loaded successfully")
        except BaseException as e:
            print("commands could not be successfully loaded")
            commands_str += f"no commands could be registered because of error: `{e}`"

        embed.title = "Commands ready"
        embed.timestamp = datetime.now()
        embed.add_field(name="commands registered:", value=commands_str, inline=False)

        print(f'{config.client.user} has connected to Discord!')
        await channel.send(embed=embed)
    else:
        print(f'{config.client.user} reconnected to Discord!')
        embed = discord.Embed(title="Reconnected bot",
                              description=f"**  From machine**: `{socket.gethostname()}`\n**From directory**: `{pathlib.Path().resolve()}`",
                              colour=0x00b0f4,
                              timestamp=datetime.now())
        await channel.send(embed=embed)


config.client.run(config.token)
