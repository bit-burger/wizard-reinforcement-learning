import discord
import re
import os

from config import client

COUNTER_FILE_PATH = 'resources/counter.txt'

patterns = {
    "miaow": "mi*a*o+a*w+|mi+a*o*a*w+",
    "ole": "ole",
    "quandal": "quandal",
}


# Function to read the counters from the file
def read_counters():
    counters = {}
    if not os.path.exists(COUNTER_FILE_PATH):
        # Create the file with initial values if it does not exist
        with open(COUNTER_FILE_PATH, 'w') as file:
            file.write("0\n")
    try:
        with open(COUNTER_FILE_PATH, 'r') as file:
            lines = file.readlines()
            for i in range(0, len(lines), 2):
                word = lines[i + 1].strip()
                count = int(lines[i].strip())
                counters[word] = count
    except (FileNotFoundError, ValueError, IndexError):
        pass
    return counters


# Function to write the counters to the file
def write_counters(counters):
    with open(COUNTER_FILE_PATH, 'w') as file:
        for word, count in counters.items():
            if count > 0:
                file.write(f"{count}\n{word}\n")


# Function to get the counter channel
async def get_counter_channel():
    for guild in client.guilds:
        for channel in guild.channels:
            if channel.name == 'counter':
                return channel
    return None


# Function to send or update the counter message
async def update_counter_message(channel, counters):
    message_content = "\n".join([f"{word.capitalize()}: {count}" for word, count in counters.items() if count > 0])
    if not message_content:
        return  # Do not send or edit the message if the content is empty
    async for message in channel.history(limit=100):
        if message.author == client.user:
            await message.edit(content=message_content)
            return
    await channel.send(message_content)


# Function to clean counters and remove words not being counted
def clean_counters(counters):
    valid_words = {"miaow", "ole", "quandal"}
    return {word: count for word, count in counters.items() if word in valid_words}


@client.event
async def ready():
    counters = read_counters()
    counters = clean_counters(counters)
    write_counters(counters)
    channel = await get_counter_channel()
    if channel:
        await update_counter_message(channel, counters)


@client.event
async def message(m: discord.Message):
    if m.author == client.user:
        return

    counters = read_counters()
    updated = False

    for word, pattern in patterns.items():
        if re.search(pattern, m.content, re.IGNORECASE):
            counters[word] = counters.get(word, 0) + 1
            updated = True

    if updated:
        write_counters(counters)
        channel = await get_counter_channel()
        if channel:
            await update_counter_message(channel, counters)
