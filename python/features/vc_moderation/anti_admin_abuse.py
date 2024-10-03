import discord
import sqlite3
import asyncio
import random
from config import client

# Verbindung zur SQLite-Datenbank herstellen oder neue erstellen
conn = sqlite3.connect('strafen.db')
c = conn.cursor()

# Tabelle für vorgemerkte Strafen erstellen, falls nicht vorhanden
c.execute('''CREATE TABLE IF NOT EXISTS strafen (
                user_id INTEGER PRIMARY KEY,
                reason TEXT,
                original_channel_id INTEGER
            )''')
conn.commit()

# Funktion, um eine Strafe vorzumerken
def add_strafe(user_id, reason, original_channel_id=None):
    c.execute('INSERT OR REPLACE INTO strafen (user_id, reason, original_channel_id) VALUES (?, ?, ?)',
              (user_id, reason, original_channel_id))
    conn.commit()

# Funktion, um zu prüfen, ob ein User eine vorgemerkte Strafe hat
def check_strafe(user_id):
    c.execute('SELECT reason, original_channel_id FROM strafen WHERE user_id = ?', (user_id,))
    return c.fetchone()

# Funktion, um eine Strafe zu löschen
def remove_strafe(user_id):
    c.execute('DELETE FROM strafen WHERE user_id = ?', (user_id,))
    conn.commit()

# Hilfsmethoden zur Identifizierung des Täters

# Findet den ersten Eintrag, der sich in einer Liste von Einträgen geändert hat
async def find_changed_entry(previous, current):
    filtered_previous, filtered_current = filter_bot_entries(previous, current)
    for prev, curr in zip(filtered_previous, filtered_current):
        if curr != prev:
            return curr
    return None

# Filtert Bot-Einträge
def filter_bot_entries(previous, current):
    previous = [entry for entry in previous if not entry.bot]
    current = [entry for entry in current if not entry.bot]
    return previous, current

@client.event
async def voice_state_update(member, before, after):
    if member.bot:
        return  # Bots sind von Strafen befreit

    # Prüfen, ob jemand gemoved, gekickt, gemutet oder gedeafed wurde
    if before.channel != after.channel:  # Move oder Kick
        if before.channel is not None and after.channel is not None and before.channel != after.channel:
            # Der Benutzer wurde gekickt (verlassen ohne neuen Channel)
            taeter = await find_changed_entry(before.channel.members, after.channel.members)
            if taeter and taeter != member:  # Täter ist nicht das Opfer selbst
                await handle_strafe(taeter, "kick", before.channel)
        elif before.channel is None and after.channel is not None:
            # Der Benutzer ist einem Channel beigetreten
            await handle_delayed_strafe(member)
        elif before.channel is not None and after.channel is not None and before.channel != after.channel:
            # Der Benutzer wurde gemoved
            taeter = await find_changed_entry(before.channel.members, after.channel.members)
            if taeter and taeter != member:  # Täter ist nicht das Opfer selbst
                await handle_strafe(taeter, "move", before.channel)

    if before.mute != after.mute:  # Mute-Änderung
        if after.mute and not before.mute:
            taeter = await find_changed_entry(before.channel.members, after.channel.members)
            if taeter and taeter != member:  # Täter ist nicht das Opfer selbst
                await handle_strafe(taeter, "mute")

    if before.deaf != after.deaf:  # Deafen-Änderung
        if after.deaf and not before.deaf:
            taeter = await find_changed_entry(before.channel.members, after.channel.members)
            if taeter and taeter != member:  # Täter ist nicht das Opfer selbst
                await handle_strafe(taeter, "deafen")

async def handle_strafe(taeter: discord.Member, action: str, original_channel: discord.VoiceChannel = None):
    if action == "move" and original_channel:
        await taeter.move_to(original_channel)  # Täter in den ursprünglichen Channel des Opfers moven

    if taeter.bot:
        return  # Bots sind straffrei

    guild = taeter.guild
    if taeter.voice:
        if action == "kick":
            await taeter.move_to(None)  # Täter aus dem Channel kicken
        elif action == "mute":
            await taeter.edit(mute=True)  # Täter muten
        elif action == "deafen":
            await taeter.edit(deafen=True)  # Täter deafen
        elif action == "move" and original_channel:
            await taeter.move_to(original_channel)  # Täter in den ursprünglichen Channel moven
        await guild.text_channels[0].send(f"{taeter.name} wurde für {action} bestraft.")
    else:
        # Täter ist nicht in einem Voice-Channel, Strafe vormerken
        add_strafe(taeter.id, action, original_channel.id if original_channel else None)
        await guild.text_channels[0].send(f"{taeter.name} hat eine vorgemerkte Strafe für {action}.")

# Funktion, um vorgemerkte Strafen zufällig nach dem Joinen zu verhängen
async def handle_delayed_strafe(member: discord.Member):
    # Prüfen, ob es eine vorgemerkte Strafe gibt
    strafe = check_strafe(member.id)
    if strafe and member.voice:  # Benutzer ist im Voice-Channel
        reason, original_channel_id = strafe
        original_channel = discord.utils.get(member.guild.voice_channels, id=original_channel_id)

        # Wähle zufällig eine Zeitspanne innerhalb der nächsten 5 Minuten
        delay = random.randint(1, 300)  # 1 bis 300 Sekunden (5 Minuten)
        await asyncio.sleep(delay)

        # Prüfen, ob der Benutzer noch im Voice-Channel ist
        if member.voice:
            if reason == "mute":
                await member.edit(mute=True)
            elif reason == "deafen":
                await member.edit(deafen=True)
            elif reason == "kick":
                await member.move_to(None)  # Benutzer aus dem Channel kicken
            elif reason == "move" and original_channel:
                await member.move_to(original_channel)  # Benutzer in den ursprünglichen Channel moven

            await member.guild.text_channels[0].send(f"{member.name} wurde für {reason} bestraft.")
            remove_strafe(member.id)  # Strafe entfernen, nachdem sie ausgeführt wurde
        else:
            # Benutzer hat den Channel verlassen, Strafe bleibt vorgemerkt
            await member.guild.text_channels[0].send(f"{member.name} konnte nicht bestraft werden, Strafe bleibt vorgemerkt.")