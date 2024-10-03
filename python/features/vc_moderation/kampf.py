import time

import discord
from config import client
import discord.ext
import time
import random
import discord
import asyncio
from config import client
import discord.ext

im_Kampf = []
cooldowns = {}  # Cooldown-System

# Cooldown-Dauer in Sekunden (z.B. 60 Sekunden Cooldown nach einem Kampf)
COOLDOWN_DURATION = 60

# Funktion, um einen Spieler auf Cooldown zu setzen
async def set_cooldown(player, duration):
    cooldowns[player.id] = time.time() + duration
    await asyncio.sleep(duration)
    del cooldowns[player.id]

# Funktion, um zu prüfen, ob ein Spieler noch auf Cooldown ist
def is_on_cooldown(player):
    return player.id in cooldowns and time.time() < cooldowns[player.id]


@client.event
async def on_message(m: discord.Message):
    if m.author.id == client.user.id:
        return

    if "kampf" in m.content.lower() and len(m.mentions) >= 1 and isinstance(m.mentions[0], discord.Member):
        mention = m.mentions[0]

        # Prüfen, ob der Spieler auf Cooldown ist
        if is_on_cooldown(mention):
            remaining_time = int(cooldowns[mention.id] - time.time())
            await m.channel.send(f"<@{mention.id}> ist noch auf Cooldown für {remaining_time} Sekunden!")
            return

        # 30% Chance, den Initiator des Befehls selbst zu bekämpfen
        if random.random() <= 0.3:
            mention = m.author

        if mention in im_Kampf:
            await m.channel.send(f"<@{mention.id}> wird bereits bekämpft!")
            return

        # Spieler in die Liste der Kämpfenden hinzufügen
        im_Kampf.append(mention)
        await m.channel.send(f"Ich kämpfe mit <@{mention.id}>!")

        # Countdown zum Kampfstart
        await m.channel.send("3...")
        await asyncio.sleep(1)
        await m.channel.send("2...")
        await asyncio.sleep(1)
        await m.channel.send("1...")
        await asyncio.sleep(1)
        await m.channel.send("Kampf beginnt!")
        await asyncio.sleep(1)

        # Spieler muten und deafen
        await mention.edit(mute=True, deafen=True)

        # Kanäle durchlaufen und Spieler verschieben
        channels = [channel for channel in m.guild.channels if
                    isinstance(channel, discord.VoiceChannel) and channel.id != m.channel.id]

        for i in range(2):  # Zweimal durch alle Kanäle
            for channel in channels:
                await mention.move_to(channel)
                await asyncio.sleep(1)
            await mention.move_to(None)  # Spieler aus allen Voice-Kanälen entfernen

        # Spieler entmuten und auf Kämpferliste entfernen
        await mention.edit(mute=False, deafen=False)
        im_Kampf.remove(mention)

        # Cooldown für den Spieler aktivieren
        await set_cooldown(mention, COOLDOWN_DURATION)
