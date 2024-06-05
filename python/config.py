import discord
import json

from multiple_event_client import MultipleEventClient

config = json.load(open("../config.json"))
token = config["token"]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = MultipleEventClient(intents=intents)