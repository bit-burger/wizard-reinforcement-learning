import discord
from config import client

import random

antworten = [
    "What's up guys! It's Quandale Dingle here! (RUUEHEHEHEHEHEEHE) I have been arrested for multiple crimes ("
    "AHHHHHHHHHHHHH) including: Selling fake COVID vaccines (WHAT), Running an illegal organ trafficking ring (OH "
    "NO), Declaring war on the Salvation Army, and performing exorcisms on random strangers ("
    "RUHEHEEHEHEHEHEHEHEHEHEHE X2 speed). I will be escaping prison on, SEPTEMBER 11TH! After that.... I WILL BE THE "
    "REAPER OF MISCHIEF!",
    "What's up guys! It's Quandale Dingle here! (RUUEHEHEHEHEHEEHE) I have been arrested for multiple crimes ("
    "AHHHHHHHHHHHHH) including: Poisoning the town's water supply (WHAT), Opening a fake orphanage (OH NO), "
    "Declaring war on UNICEF, and burning down a library (RUHEHEEHEHEHEHEHEHEHEHEHE X2 speed). I will be escaping "
    "prison on, APRIL 20TH! After that.... I WILL TURN THE WORLD INTO MY PLAYGROUND!",
    "What's up guys! It's Quandale Dingle here! (RUUEHEHEHEHEHEEHE) I have been arrested for multiple crimes ("
    "AHHHHHHHHHHHHH) including: Running a pyramid scheme targeting the elderly (WHAT), Organizing underground fight "
    "clubs for toddlers (OH NO), Declaring war on Amnesty International, and hacking hospital life support systems ("
    "RUHEHEEHEHEHEHEHEHEHEHEHE X2 speed). I will be escaping prison on, JANUARY 1ST! After that.... I WILL BE THE "
    "NIGHTMARE IN HUMAN FORM!",
    "What's up guys! It's Quandale Dingle here! (RUUEHEHEHEHEHEEHE) I have been arrested for multiple crimes ("
    "AHHHHHHHHHHHHH) including: Running a fake charity for disaster victims (WHAT), Spreading malware through "
    "children's toys (OH NO), Declaring war on the Red Cross, and committing arson at an animal shelter ("
    "RUHEHEEHEHEHEHEHEHEHEHEHE X2 speed). I will be escaping prison on, OCTOBER 31ST! After that.... I WILL UNLEASH "
    "CHAOS UPON THE WORLD!",
    "What's up guys! It's Quandale Dingle here! (RUUEHEHEHEHEHEEHE) I have been arrested for multiple crimes ("
    "AHHHHHHHHHHHHH) including: Faking my own death for insurance money (WHAT), Kidnapping the Easter Bunny (OH NO), "
    "Declaring war on Make-A-Wish Foundation, and sabotaging food banks (RUHEHEEHEHEHEHEHEHEHEHEHE X2 speed). I will "
    "be escaping prison on, DECEMBER 31ST! After that.... I WILL BRING ABOUT THE END OF DAYS!"
]


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if 'quandale' in message.content.lower():
        antwort = random.choice(antworten)
        await message.channel.send(antwort)


@client.event
async def on_ready():
    print("Quandaleantworten is ready")
