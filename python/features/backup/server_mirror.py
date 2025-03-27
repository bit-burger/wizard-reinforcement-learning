from collections import defaultdict

import discord
from discord.ext import commands
import asyncio
from discord import errors, app_commands

from config import client, tree

intents = discord.Intents.all()

ACTIVE_SERVER_ID = 1205582028905648209  #1205582028905648209
BACKUP_SERVER_ID = 1272931546919338047  #1272931546919338047
backup_guild = client.get_guild(BACKUP_SERVER_ID)
active_guild = client.get_guild(ACTIVE_SERVER_ID)
isSyncing = False
                            #bot                 giga-spam             quandale sein bot     botdale
BLACKLISTED_CHANNEL_IDS = [1208057795958808647, 1271237576006701240, 1247244679381254226, 1331762340609265715]

backed_up_channels = set()
pending_messages = defaultdict(list)


@client.event
async def ready():
    global backup_guild, active_guild
    backup_guild = client.get_guild(BACKUP_SERVER_ID)
    active_guild = client.get_guild(ACTIVE_SERVER_ID)


@client.event
async def on_message(message):
    if not hasattr(message.guild, 'id'):
        return
    if message.guild.id == ACTIVE_SERVER_ID:
        if message.channel.id in BLACKLISTED_CHANNEL_IDS:
            return
        if isSyncing:
            if active_guild.get_channel(message.channel.id) in backed_up_channels:
                await mirror_message(message)
        else:
            await mirror_message(message)


@client.event
async def on_message_edit(before, after):
    if before.guild.id == ACTIVE_SERVER_ID:
        if before.channel.id in BLACKLISTED_CHANNEL_IDS:
            return
        if isSyncing:
            if active_guild.get_channel(before.channel.id) in backed_up_channels:
                await mirror_edited_message(before, after)
        else:
            await mirror_edited_message(before, after)


@client.event
async def on_message_delete(message):
    if message.guild.id == ACTIVE_SERVER_ID:
        if message.channel.id in BLACKLISTED_CHANNEL_IDS:
            return
        if isSyncing:
            if active_guild.get_channel(message.channel.id) in backed_up_channels:
                await mark_deleted_message(message)
        else:
            await mark_deleted_message(message)


@client.event
async def guild_category_create(category):
    if category.guild.id == ACTIVE_SERVER_ID:
        await mirror_category_create(category)


@client.event
async def guild_category_delete(category):
    if category.guild.id == ACTIVE_SERVER_ID:
        await mirror_category_delete(category)


@client.event
async def guild_category_update(before, after):
    if before.guild.id == ACTIVE_SERVER_ID:
        await mirror_category_update(before, after)


@client.event
async def guild_channel_create(channel):
    if channel.guild.id == ACTIVE_SERVER_ID:
        await mirror_channel_create(channel)


@client.event
async def guild_channel_update(before, after):
    if before.guild.id == ACTIVE_SERVER_ID:
        await mirror_channel_update(before, after)


async def mirror_message(message):
    backup_channel = discord.utils.get(backup_guild.channels, name=message.channel.name)
    if not backup_channel:
        return
    if backup_channel:
        if message.embeds:
            # Create a new message stating who wrote it and when
            author_info = f"**{message.author.name}**      {message.created_at.strftime('%H:%M:%S    %d.%m.%Y')}:"
            await backup_channel.send(content=author_info)

            # Forward the original embed
            for embed in message.embeds:
                await backup_channel.send(embed=embed)
        else:
            # Create embed
            embed = discord.Embed(
                description=message.content,
                color=discord.Color.blue(),
                timestamp=message.created_at
            )
            embed.set_author(name=message.author.name,
                             icon_url=message.author.avatar.url if message.author.avatar else None)
            embed.set_footer(text="")
            # Add attachment info if any
            if message.attachments:
                attachment_info = "\n".join(
                    [f"[{attachment.filename}]({attachment.url})" for attachment in message.attachments])
                embed.add_field(name="Attachments", value=attachment_info, inline=False)
            await backup_channel.send(embed=embed)


async def mirror_edited_message(before, after):
    backup_channel = discord.utils.get(backup_guild.channels, name=before.channel.name)

    if backup_channel:
        original_embed = create_message_embed(before)
        original_embed.title = "Original Message"

        edited_embed = create_message_embed(after)
        edited_embed.title = "Edited Message"

        await backup_channel.send(embeds=[original_embed, edited_embed])


async def mark_deleted_message(message):
    backup_channel = discord.utils.get(backup_guild.channels, name=message.channel.name)

    if backup_channel:
        embed = create_message_embed(message)
        embed.title = "Deleted Message"
        embed.color = discord.Color.red()
        await backup_channel.send(embed=embed)


def create_message_embed(message):
    embed = discord.Embed(
        description=message.content[:1024],  # Truncate the message content to 1024 characters
        color=discord.Color.blue(),
        timestamp=message.created_at
    )
    embed.set_author(name=message.author.name,
                     icon_url=message.author.avatar.url if message.author.avatar else None)
    embed.set_footer(text="")

    if message.attachments:
        attachment_info = "\n".join(
            [f"[{attachment.filename}]({attachment.url})" for attachment in message.attachments])
        embed.add_field(name="Attachments", value=attachment_info[:1024], inline=False)  # Truncate attachment info to 1024 characters

    return embed


async def handle_channel_deletion(channel):
    log_channel = discord.utils.get(backup_guild.text_channels, id=1332330274163527711)  # log channel ID
    if " - Deleted" not in channel.name:
        await channel.edit(name=f"{channel.name} - Deleted")
    if log_channel:
        await log_channel.send(f"Channel {channel.name} has been deleted in the active server.")

async def mirror_channel_create(channel):
    await backup_guild.create_text_channel(channel.name)


async def mirror_channel_delete(channel):
    backup_channel = await get_or_create_backup_channel(backup_guild, channel)
    if backup_channel:
        await handle_channel_deletion(backup_channel)

async def mirror_channel_update(before, after):
    backup_channel = await get_or_create_backup_channel(backup_guild, before)

    if backup_channel:
        backup_channel.edit(name=after.name)
        if before.category != after.category:
            backup_category = await get_or_create_backup_category(backup_guild, after.category)
            await backup_channel.edit(category=backup_category)


async def mirror_category_create(category):
    await backup_guild.create_category(category.name)


async def mirror_category_delete(category):
    backup_category = discord.utils.get(backup_guild.categories, name=category.name)
    if backup_category:
        for channel in backup_category.channels:
            await channel.send("This category has been deleted in the active server.")


async def mirror_category_update(before, after):
    backup_category = discord.utils.get(backup_guild.categories, name=before.name)
    if backup_category:
        await backup_category.edit(name=after.name)


async def get_or_create_backup_channel(backup_guild, channel):
    backup_channel = discord.utils.get(backup_guild.channels, name=channel.name)
    if not backup_channel:
        backup_channel = await create_backup_channel(backup_guild, channel)
    return backup_channel


async def get_or_create_backup_category(backup_guild, category):
    if not category:
        return None
    backup_category = discord.utils.get(backup_guild.categories, name=category.name)
    if not backup_category:
        backup_category = await backup_guild.create_category(category.name)
    return backup_category


async def create_backup_channel(backup_guild, channel):
    backup_category = await get_or_create_backup_category(backup_guild, channel.category)
    return await backup_guild.create_text_channel(channel.name, category=backup_category)


@tree.command(name="clear", description="clears the server", guild=discord.Object(id=BACKUP_SERVER_ID))
async def clear_backup(interaction: discord.Interaction):
    for channel in backup_guild.channels:
        if channel.name != "log":
            await channel.delete()
    for category in backup_guild.categories:
        await category.delete()


@tree.command(name="sync_backup", description="Sync the entire server to the backup server",
              guild=discord.Object(id=BACKUP_SERVER_ID))
async def sync_backup(interaction: discord.Interaction):
    if interaction.user.id != 444417560100864020:
        return

    if interaction.guild_id != BACKUP_SERVER_ID:
        return

    global isSyncing
    isSyncing = True

    # Sync categories and channels
    await sync_categories_and_channels()

    # Sync messages
    for channel in active_guild.text_channels:
        if channel.id in BLACKLISTED_CHANNEL_IDS:
            continue
        backup_channel = discord.utils.get(backup_guild.channels, name=channel.name)
        if backup_channel:
            await backup_channel_messages(channel, backup_channel, pending_messages)
            backed_up_channels.add(channel.id)

    isSyncing = False

async def sync_categories_and_channels():
    # Sync categories
    print("Syncing categories")
    for category in active_guild.categories:
        await asyncio.sleep(0.6)
        backup_category = discord.utils.get(backup_guild.categories, name=category.name)
        if not backup_category:
            backup_category = await backup_guild.create_category(category.name)
        await backup_category.edit(position=category.position)

    # Sync channels
    print("Syncing channels")
    for channel in active_guild.text_channels:
        await asyncio.sleep(0.6)
        backup_channel = discord.utils.get(backup_guild.channels, name=channel.name)
        if not backup_channel:
            backup_category = discord.utils.get(backup_guild.categories,
                                                name=channel.category.name) if channel.category else None
            backup_channel = await backup_guild.create_text_channel(channel.name, category=backup_category)
        await backup_channel.edit(position=channel.position)

    # Mark deleted channels
    print("Marking deleted channels")
    for backup_channel in backup_guild.text_channels:
        await asyncio.sleep(0.6)
        active_channel = discord.utils.get(active_guild.text_channels, name=backup_channel.name)
        if not active_channel and " - Deleted" not in backup_channel.name and backup_channel.id != 1332330274163527711:  # log channel
            await handle_channel_deletion(backup_channel)

    print("Done syncing structures")

async def get_latest_backup_message_timestamp(backup_channel):
    latest_message = None
    async for message in backup_channel.history(limit=1, oldest_first=False):
        latest_message = message
        break
    return latest_message.created_at if latest_message else None


async def backup_channel_messages(channel, backup_channel, pending_messages):
    try:
        last_synced_timestamp = await get_latest_backup_message_timestamp(backup_channel)
        if last_synced_timestamp is None:
            async for message in channel.history(limit=None, oldest_first=True):
                await backup_message(message, backup_channel)
                await asyncio.sleep(0.6)
        else:
            async for message in channel.history(limit=None, after=last_synced_timestamp, oldest_first=True):
                await backup_message(message, backup_channel)
                await asyncio.sleep(0.6)

        # Backup any pending messages for this channel
        for pending_message in pending_messages[channel.id]:
            await backup_message(pending_message, backup_channel)
        pending_messages[channel.id].clear()

    except Exception as e:
        print(f"Error backing up channel {channel.name}: {e}")


async def backup_message(message, backup_channel):
    if message.embeds:
        # Create a new message stating who wrote it and when
        author_info = f"**{message.author.name}**      {message.created_at.strftime('%H:%M %d.%m.%Y')}:"
        await backup_channel.send(content=author_info)

        # Forward the original embed
        for embed in message.embeds:
            await backup_channel.send(embed=embed)
    else:
        # Create embed
        embed = discord.Embed(
            description=message.content,
            color=discord.Color.blue(),
            timestamp=message.created_at
        )
        embed.set_author(name=message.author.name,
                         icon_url=message.author.avatar.url if message.author.avatar else None)
        embed.set_footer(text="")
        # Add attachment info if any
        if message.attachments:
            attachment_info = "\n".join(
                [f"[{attachment.filename}]({attachment.url})" for attachment in message.attachments])
            embed.add_field(name="Attachments", value=attachment_info, inline=False)
        await backup_channel.send(embed=embed)
