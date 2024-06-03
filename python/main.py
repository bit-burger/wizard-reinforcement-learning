import json
config = json.load(open("../config.json"))

import discord

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


@client.event
async def on_message(message):
    print("message received")
    if message.author == client.user:
        return

    if message.content.lower().find('ping') != -1:
        await message.channel.send('PONG!')


client.run(config["token"])