import random
from config import client
import discord

antworten = []


@client.event
async def message(nachricht):
    if nachricht.author == client.user:
        return

    if 'quandal' in nachricht.content.lower():
        antwort = random.choice(antworten)
        await nachricht.channel.send(antwort)


@client.event
async def ready():
    global antworten
    with open(r'C:\Users\lenna\OneDrive - Students RWTH Aachen University\coden\Quandale bot\quandale-sein-bot\python\features\quandal.txt', 'r', encoding='utf-8') as f:
        antworten = f.read().split('///')
    print("Quandaleantworten is ready")
