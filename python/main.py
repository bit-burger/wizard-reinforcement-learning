import features
from python.config import client, token


@client.event
async def ready():
    print(f'{client.user} has connected to Discord!')

client.run(token)
