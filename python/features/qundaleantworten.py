import re

from config import client
import discord
import random

antworten = []
stelle = 0


@client.event
async def message(nachricht):
    if nachricht.author == client.user or nachricht.author.bot:
        return
    if re.search("dua[ ]+(lipa)*", nachricht.content):
        await nachricht.channel.send(
            "What's up guys! It's Quandale Dingle here! (RUUEHEHEHEHEHEEHE) I have been arrested for multiple crimes (AHHHHHHHHHHHHH) including: Misgendering Dua Lipa during a concert announcement (WHAT), Selling fake feminine merchandise to unsuspecting fans (OH NO), Declaring war on gendered music genres, and replacing all female pop icons with male impersonators (RUHEHEEHEHEHEHEHEHEHEHEHE X2 speed). I will be escaping prison on, MAY 29TH! After that.... I WILL MAKE THE MUSIC INDUSTRY QUESTION EVERYTHING!")
    if 'quandal' in nachricht.content.lower():
        global stelle
        if stelle == len(antworten):
            stelle = 0
        await nachricht.channel.send(antworten[stelle])
        stelle += 1
        update_anzahl()


def update_anzahl():
    with open(r'features/stellequandaleantworten.txt', 'w', encoding='utf-8') as f:
        global stelle
        f.flush()
        f.write(str(stelle))
        f.close()


def get_anzahl():
    with open(r'features/stellequandaleantworten.txt', 'r', encoding='utf-8') as f:
        global stelle
        stelle = int(f.read().strip())
        f.close()


@client.event
async def ready():
    global stelle
    global antworten
    with open(r'features/quandal.txt', 'r', encoding='utf-8') as f:
        antworten = f.read().split('///')
    f.close()
    update_anzahl()
    get_anzahl()
    print("Quandaleantworten is ready")
