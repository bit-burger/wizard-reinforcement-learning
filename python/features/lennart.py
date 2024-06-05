import asyncio
import discord
import re
import time

from config import client

previous_audit_logs = []


# process = subprocess.Popen(
#             [r"C:\Users\lenna\OneDrive - Students RWTH Aachen University\coden\C\Wizzard\cmake-build-debug\C.exe"],
#             stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)


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
    # print(eingabe, file=process.stdin)
    # output = process.stdout.readline()
    # print(output)
    ...


def closewizzard():
    # process.stdin.close()
    # process.stdout.close()
    # process.wait()
    ...


@client.event
async def message(m: discord.Message):
    global dauermute
    # nicht auf sich selbst reagieren
    if m.author.id == client.user.id:
        return
    # Tony id: 708227359916163137
    # Lennart id: 444417560100864020
    # Tony muten
    if m.author.id == 444417560100864020:  # Lennart
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

    # Wizzard reagieren
    if re.search("wiz?zard", m.content, re.RegexFlag.IGNORECASE):
        emojis = ["🧙"]
        for emoji in emojis:
            await m.add_reaction(emoji)

    # Henning reagieren
    if (re.search("henning du toller mensch", m.content, re.RegexFlag.IGNORECASE)):
        await m.channel.send("Henning hat nen kleinen")

    if m.content == "!start_wizard":
        # process = subprocess.Popen(
        # [r"C:\Users\lenna\OneDrive - Students RWTH Aachen University\coden\C\Wizzard\cmake-build-debug\C.exe"],
        # stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)

        # Simulate the inputs for the C program
        # print("", file=process.stdin)
        # output = process.stdout.readline()
        # await m.channel.send(f"Output: {output}")
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


@client.event
async def voice_state_update(member: discord.Member, before, after):
    #if member.bot:
        #return
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
        print("Audit log has changed!")
        kicker = changed_entry.user
        print(f"User who made the change: {kicker.name}")
        await kicker.move_to(None)
        await asyncio.sleep(2)
        previous_audit_logs = current_audit_logs


async def find_changed_entry(previous, current):
    for previous_entry, current_entry in zip(previous, current):
        if current_entry.extra.count != previous_entry.extra.count:
            if current_entry.user.id != client.user.id:  # Der Bot selbst
                return current_entry
    return None


@client.event
async def ready():
    guild = client.get_guild(1205582028905648209)  # Quandale dingle
    async for entry in guild.audit_logs(limit=10, action=discord.AuditLogAction.member_disconnect):
        previous_audit_logs.append(entry)
