import subprocess

import discord
from discord.ext import commands
from discord import Embed, ButtonStyle, SelectOption, SelectMenu
from discord.ui import Button
import re
import time

from python.config import client


process = subprocess.Popen(
            [r"C:\Users\lenna\OneDrive - Students RWTH Aachen University\coden\C\Wizzard\cmake-build-debug\C.exe"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)

class MyView(discord.ui.View):
    def __init__(self, channel):
        super().__init__()  # Aufruf des Konstruktors der Elternklasse
        self.channel = channel  # Speichern des Parameters in einer Instanzvariablen
    @discord.ui.select(
        placeholder="",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="1", description=""),
            discord.SelectOption(label="2", description=""),
            discord.SelectOption(label="3", description="")
        ]
    )
    async def select_callback(self, select, interaction):
        await self.channel.send(interaction.values[0])
        handlewizzard(interaction.values[0])


def handlewizzard(eingabe):
    # Simulate the inputs for the C program
    print(eingabe, file=process.stdin)
    output = process.stdout.readline()
    print(output)


def closewizzard():
    process.stdin.close()
    process.stdout.close()
    process.wait()






@client.event
async def message(m: discord.Message):
    global x
    # nicht auf sich selbst reagieren
    if m.author.id == client.user.id:
        return
    # Tony id: 708227359916163137
    # Lennart id: 444417560100864020
    # Tony muten
    if m.author.id == 444417560100864020:  # Lennart
        if m.content == "Tony muten":
            user_to_mute = discord.utils.get(m.guild.members, id=708227359916163137)
            x = True
            while x:
                await user_to_mute.edit(mute=True)
                time.sleep(1)
        if m.content == "Tony entmuten":
            user_to_mute = discord.utils.get(m.guild.members, id=708227359916163137)
            x = False
            await user_to_mute.edit(mute=False)

    # Wizzard reagieren
    if re.search("wiz?zard", m.content, re.RegexFlag.IGNORECASE):
        emojis = ["🧙"]
        for emoji in emojis:
            await m.add_reaction(emoji)

    # Henning reagieren
    if (re.search("henning du toller mensch", m.content, re.RegexFlag.IGNORECASE)):
        await m.channel.send("Henning hat nen kleinen")

    if m.content == "!start_wizard":
        #process = subprocess.Popen(
            #[r"C:\Users\lenna\OneDrive - Students RWTH Aachen University\coden\C\Wizzard\cmake-build-debug\C.exe"],
            #stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)

        # Simulate the inputs for the C program
        print("", file=process.stdin)
        output = process.stdout.readline()
        await m.channel.send(f"Output: {output}")
        await m.channel.send("", view=MyView(m.channel))


@client.event
async def message_edit(before: discord.Message, after: discord.Message):
    # nicht auf sich selbst reagieren
    if after.author.id == client.user.id:
        return
    # Mensa Bot reagieren
    if after.author.name == "MensaBot":
        if after.embeds[0].title == "Aachen, Mensa Academica is closed today":
            await after.channel.send("Danke Mensa Bot")
