from config import client
import discord

antworten = []
stelle = 0

@client.event
async def message(nachricht):
    if nachricht.author == client.user or nachricht.author.bot:
        return

    if 'quandal' in nachricht.content.lower():
        global stelle
        if stelle == len(antworten):
            stelle = 0
        await nachricht.channel.send(antworten[stelle])
        stelle += 1


@client.event
async def ready():
    global antworten
    with open(r'features/quandal.txt', 'r', encoding='utf-8') as f:
        antworten = f.read().split('///')
    f.close()
    print("Quandaleantworten is ready")
