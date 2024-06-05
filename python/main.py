from config import client, token
import features
@client.event
async def ready():
    print(f'{client.user} has connected to Discord!')
client.run(token)
