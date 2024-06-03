import features # ignore: unused-import
from python.config import client, token


@client.event
async def ready():
    print(f'{client.user} has connected to Discord!')


@client.event
async def message(message):
    print("message received")
    if message.author == client.user:
        return

    if message.content.lower().find('ping') != -1:
        await message.channel.send('PONG!')


client.run(token)
