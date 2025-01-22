import discord
from helpers.entries import find_changed_entry

from config import client

previous_audit_logs = []


@client.event
async def voice_state_update(member: discord.Member, before, after):
    if member.bot:
        return
    # Prüfen, ob das Mitglied gemoved wurde
    if before.channel is not None and after.channel is not None and before.channel != after.channel:
        await check_audit_logs_efficient(member.guild, before, member)


async def check_audit_logs_efficient(guild, before, target):
    global previous_audit_logs
    current_audit_logs = []
    async for entry in guild.audit_logs(limit=10, action=discord.AuditLogAction.member_move):
        current_audit_logs.append(entry)
    changed_entry = await find_changed_entry(previous_audit_logs, current_audit_logs)
    if changed_entry is not None:
        print(f"User who was moved: {target.name}")
        await target.move_to(before.channel)
        previous_audit_logs = current_audit_logs


@client.event
async def ready():
    guild = client.get_guild(1205582028905648209)  # Quandale dingle
    async for entry in guild.audit_logs(limit=10, action=discord.AuditLogAction.member_move):
        previous_audit_logs.append(entry)
