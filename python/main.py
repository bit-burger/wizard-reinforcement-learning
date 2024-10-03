import importlib
import os
import pathlib
import platform
import socket
import subprocess
from datetime import datetime
from os import path
from time import time

import discord

import config


def get_git_info():
    try:
        # Get the last commit SHA and the first 20 characters of the commit message
        commit_info = subprocess.check_output(
            ["git", "log", "-1", "--pretty=format:%h %s"],
            universal_newlines=True
        )

        commit_sha = commit_info.split()[0]
        commit_message = " ".join(commit_info.split()[1:])
        if len(commit_message) > 30:
            commit_message = commit_message[:26] + "..."

        branch = subprocess.check_output(
            ["git", "branch", "--show-current"],
            universal_newlines=True
        ).strip()

        version_info = f"`\"{commit_message}\" ('{branch}', {commit_sha})`"

        return version_info

    except subprocess.CalledProcessError:
        return "`not available`"

module_str = ""
status_str = ""
time_to_load_str = ""

module_error_str = ""

# Lade die Liste der zu ignorierenden Dateien aus der .featureignore Datei
ignore_list = set()
ignore_file_path = os.path.join("features", ".featureignore")

if path.exists(ignore_file_path):
    with open(ignore_file_path, "r") as f:
        ignore_list = set(line.strip() for line in f if line.strip())  # Entferne Leerzeilen

# Verwende os.walk, um rekursiv durch die Ordnerstruktur zu gehen
for root, dirs, files in os.walk("features"):
    for file in files:
        filename = os.path.join(root, file)
        isdir = path.isdir(filename)

        # Überspringe Dateien, die in der .featureignore-Datei gelistet sind
        if file in ignore_list:
            continue

        # Überspringe Dateien, die '.helper.py' enthalten
        if file.endswith(".helper.py"):
            continue

        # Überprüfe, ob es sich um eine Datei handelt und ob __init__.py im Verzeichnis vorhanden ist
        if isdir:
            if not path.exists(os.path.join(filename, "__init__.py")):
                continue
        else:
            if filename.endswith(".py"):
                filename = filename[:-3]  # Entferne die ".py"-Endung
            else:
                continue

        # Konvertiere den Dateipfad in ein Modulimportformat
        module_path = os.path.relpath(filename, "features").replace(os.sep, ".")

        module_str += f"`{module_path}`" + "\n"
        begin_time = time()

        try:
            # Modul dynamisch importieren
            importlib.import_module(f"features.{module_path}")
            status_str += "`loaded successfully`" + "\n"
            print(f"module '{module_path}' loaded successfully")
        except BaseException as e:
            status_str += "`loaded unsuccessful`" + "\n"
            module_error_str += f"`{module_path}`: `{e}`" + "\n\n"
            print(f"module '{module_path}' could not be loaded, error: {e}")
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
                              description=f"**  Machine**: `{socket.gethostname()}`\n\n**Directory**: `{pathlib.Path().resolve()}`\n\n**Python version**: `{platform.python_version()}`\n\n**Version control**: {get_git_info()}\n\n**Modules loaded**:",
                              colour=0x00b0f4,
                              timestamp=datetime.now())

        embed.add_field(name="module", value=module_str)
        embed.add_field(name="status", value=status_str)
        embed.add_field(name="time to load", value=time_to_load_str)

        if module_error_str != "":
            embed.add_field(name="module errors:", value=module_error_str, inline=False)

        embed.set_author(name=config.client.user.name + "#" + config.client.user.discriminator, icon_url=config.client.user.display_avatar.url)
        embed.set_footer(text=config.client.user.name)

        commands_str = ""
        try:
            config.commands = await config.tree.sync(guild=guild)
            #quandale dingle backup
            await config.tree.sync(guild=config.client.get_guild(1272931546919338047))
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
