import discord
import re
import time
from hilfen.entries import find_changed_entry

from config import client

previous_audit_logs = []

dauermute = False
dauermutehenning = False

@client.event
async def message(m: discord.Message):
    global dauermute
    global dauermutehenning
    # nicht auf sich selbst reagieren
    if m.author.id == client.user.id:
        return
    # Tony id: 708227359916163137
    # Lennart id: 444417560100864020
    # Tony muten
    if m.author.id == 444417560100864020:  # Lennart
        if m.content == "Henning muten":
            user_to_mute = discord.utils.get(m.guild.members, id=391313166958854174)
            dauermutehenning = True
            while dauermutehenning == True:
                await user_to_mute.edit(mute=True, deafen=True)
                time.sleep(1)
        if m.content == "Henning entmuten":
            user_to_mute = discord.utils.get(m.guild.members, id=391313166958854174)
            dauermutehenning = False
            await user_to_mute.edit(mute=False, deafen=False)
        if m.content == "Tony muten":
            user_to_mute = discord.utils.get(m.guild.members, id=708227359916163137)  # Tony
            dauermute = True
            while dauermute:
                await user_to_mute.edit(mute=True, deafen=True)
                time.sleep(1)
        if m.content == "Tony entmuten":
            user_to_mute = discord.utils.get(m.guild.members, id=708227359916163137)  # Tony
            dauermute = False
            await user_to_mute.edit(mute=False, deafen=False)
    # Henning reagieren
    if re.search("henning du toller mensch", m.content, re.RegexFlag.IGNORECASE):
        await m.channel.send("Henning hat nen kleinen")


@client.event
async def message_edit(before: discord.Message, after: discord.Message):
    # nicht auf sich selbst reagieren
    if after.author.id == client.user.id:
        return
    # Mensa Bot reagieren
    if after.author.name == "MensaBot":
        if after.embeds[0].title == "Aachen, Mensa Academica is closed today":
            await after.channel.send("Danke Mensa Bot")


@client.event
async def voice_state_update(member: discord.Member, before, after):
    if member.bot:
        return
    if after.deaf is True or after.mute is True:
        print(f"{member} has been deafend or muted.")
        await member.edit(mute=False, deafen=False)
    # Prüfen, ob das Mitglied aus einem Sprachkanal gekickt wurde
    if before.channel is not None and after.channel is None:
        await check_audit_logs_efficient(member.guild)


async def check_audit_logs_efficient(guild):
    global previous_audit_logs
    current_audit_logs = []
    async for entry in guild.audit_logs(limit=10, action=discord.AuditLogAction.member_disconnect):
        current_audit_logs.append(entry)
    changed_entry = await find_changed_entry(previous_audit_logs, current_audit_logs)
    if changed_entry is not None:
        print("User was kicked")
        kicker = changed_entry.user
        print(f"User who made the change: {kicker.name}")
        await kicker.move_to(None)
    previous_audit_logs = current_audit_logs


@client.event
async def ready():
    guild = client.get_guild(1205582028905648209)  # Quandale dingle
    async for entry in guild.audit_logs(limit=10, action=discord.AuditLogAction.member_disconnect):
        previous_audit_logs.append(entry)
