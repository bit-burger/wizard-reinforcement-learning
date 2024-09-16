import asyncio

from discord import Guild

from config import client

emojis = ["🐱", "😺", "😽", "😼", "😹"]

emoji_index = 0
guild: Guild = None


def current_name(): return "Quandale Dingle " + emojis[emoji_index % 5]


@client.event
async def ready():
    global guild
    guild = await client.fetch_guild(1205582028905648209)
    global emoji_index
    while 1:
        emoji_index += 1
        await change_to_current()
        await asyncio.sleep(1)


@client.event
async def guild_update(old_guild: Guild, new_guild: Guild):
    if new_guild.name != current_name():
        await change_to_current()


async def change_to_current():
    global guild
    await guild.edit(reason="weils der quandale bot kann 😺", name=current_name())