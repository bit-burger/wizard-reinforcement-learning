import pathlib
import socket
from datetime import datetime
from peewee import *


import discord
import json

from discord import app_commands
from discord.app_commands import AppCommand

from multiple_event_client import MultipleEventClient

config = json.load(open("../config.json"))
token = config["token"]

db = SqliteDatabase('main.db')
db.connect()


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = MultipleEventClient(intents=intents)
tree = app_commands.CommandTree(client)
commands: list[AppCommand] | None = None
