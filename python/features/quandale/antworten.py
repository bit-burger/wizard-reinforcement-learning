import re
import os
from config import client
import discord
import random

antworten = []
stelle = 0

# Get the absolute path to the current file's directory
current_directory = os.path.dirname(os.path.abspath(__file__))

@client.event
async def message(nachricht):
    if nachricht.author == client.user or nachricht.author.bot:
        return
    if re.search("dua[ ]+(lipa)*", nachricht.content):
        await nachricht.channel.send(
            "What's up guys! It's Quandale Dingle here! (RUUEHEHEHEHEHEEHE) I have been arrested for multiple crimes "
            "(AHHHHHHHHHHHHH) including: Misgendering Dua Lipa during a concert announcement (WHAT), Selling fake "
            "feminine merchandise to unsuspecting fans (OH NO), Declaring war on gendered music genres, and replacing "
            "all female pop icons with male impersonators (RUHEHEEHEHEHEHEHEHEHEHEHE X2 speed). I will be escaping "
            "prison on, MAY 29TH! After that.... I WILL MAKE THE MUSIC INDUSTRY QUESTION EVERYTHING!")
    if 'quandal' in nachricht.content.lower():
        global stelle
        if stelle == len(antworten):
            stelle = 0
        await nachricht.channel.send(antworten[stelle])
        stelle += 1
        update_anzahl()


def update_anzahl():
    with open(os.path.join(current_directory, 'stellequandaleantworten.txt'), 'w', encoding='utf-8') as f:
        global stelle
        f.flush()
        f.write(str(stelle))
        f.close()


def get_anzahl():
    with open(os.path.join(current_directory, 'stellequandaleantworten.txt'), 'r', encoding='utf-8') as f:
        global stelle
        stelle = int(f.read().strip())
        f.close()


def check_and_create_file():
    if not os.path.isfile(os.path.join(current_directory, 'stellequandaleantworten.txt')):
        with open(os.path.join(current_directory, 'stellequandaleantworten.txt'), 'w', encoding='utf-8') as f:
            f.write('0')
            f.close()


@client.event
async def ready():
    global stelle
    global antworten
    # Use the absolute path to 'quandale.txt'
    with open(os.path.join(current_directory, 'quandale.txt'), 'r', encoding='utf-8') as f:
        antworten = f.read().split('///')
    f.close()
    check_and_create_file()
    get_anzahl()
