from dataclasses import dataclass
import discord
from config import client
import sqlite3


@dataclass
class Rolle:
    name: str
    color: str
    members: list  # Liste von Member IDs


# SQLite-Datenbank für die Tags
conn = sqlite3.connect('tags.db')
c = conn.cursor()

# Tags-Tabelle erstellen
c.execute('''CREATE TABLE IF NOT EXISTS tags
             (name TEXT PRIMARY KEY, color TEXT, members TEXT)''')


# Funktion: Page Walk - Rolle in der SQLite-Datenbank suchen
def page_walk(role_name):
    c.execute("SELECT * FROM tags WHERE name=?", (role_name,))
    tag = c.fetchone()
    if tag:
        # Tag in eine Rolle umwandeln und zurückgeben
        members = tag[2].split(',')
        return Rolle(name=tag[0], color=tag[1], members=members)
    return None


# Funktion: Page Fault - Wenn Rolle nicht gefunden wird
async def page_fault(ctx, role_name):
    await ctx.send(f"Rolle oder Tag `{role_name}` existiert nicht.")


# Funktion: Swap Page In - Tag aus der DB zu einer Rolle machen
async def swap_page_in(guild, saved_role: Rolle):
    new_role = await guild.create_role(name=saved_role.name, color=discord.Color(int(saved_role.color, 16)))
    for member_id in saved_role.members:
        member = guild.get_member(int(member_id))
        if member:
            await member.add_roles(new_role)
    return new_role


# Funktion: Swap Page Out - Rolle in den Tag umwandeln und löschen
async def swap_page_out(guild, discord_role):
    members = ','.join([str(member.id) for member in discord_role.members])
    c.execute("INSERT INTO tags (name, color, members) VALUES (?, ?, ?)",
              (discord_role.name, str(discord_role.color), members))
    conn.commit()
    await discord_role.delete()


# Funktion: Rolle hinzufügen
async def add_role(ctx, role_name, color="0xFFFFFF"):
    guild = ctx.guild
    discord_role = discord.utils.get(guild.roles, name=role_name)

    if discord_role:
        await ctx.send(f"Rolle `{role_name}` existiert bereits.")
    else:
        # Page Walk: Suche in der DB
        saved_role = page_walk(role_name)
        if saved_role:
            # Wenn Tag gefunden, dann Swap Page In
            await swap_page_in(guild, saved_role)
            await ctx.send(f"Tag `{role_name}` wurde in eine Rolle umgewandelt.")
        else:
            # Page Fault: Weder Rolle noch Tag gefunden
            await page_fault(ctx, role_name)


# Aging-Algorithmus zum Wählen einer alten Rolle
def find_oldest_role(guild):
    return min(guild.roles, key=lambda r: r.created_at)  # Simpler Ansatz basierend auf dem Erstellungsdatum


# /role Befehl
@client.command()
async def role(ctx, role_name, color="0xFFFFFF"):
    guild = ctx.guild

    if len(guild.roles) >= 250:  # Wenn das Limit erreicht ist
        oldest_role = find_oldest_role(guild)
        await swap_page_out(guild, oldest_role)  # Swap Page Out
        await ctx.send(f"Rolle `{oldest_role.name}` wurde in einen Tag umgewandelt.")

    await add_role(ctx, role_name, color)


# @rollenname erkennen
@client.event
async def on_message(message):
    if message.content.startswith("@"):
        role_name = message.content[1:]
        guild = message.guild

        # Direkt auf Discord-Rollen (Adressen im Memory) zugreifen
        discord_role = discord.utils.get(guild.roles, name=role_name)
        if discord_role:
            pass  # Wenn die Rolle existiert, keine Aktion
        else:
            # Page Walk: Suche in der DB
            saved_role = page_walk(role_name)
            if saved_role:
                # Swap Page In: Tag in Rolle umwandeln
                await swap_page_in(guild, saved_role)
                await message.channel.send(f"Tag `{role_name}` wurde in eine Rolle umgewandelt.")
            else:
                # Page Fault: Rolle oder Tag existiert nicht
                await page_fault(message.channel, role_name)

    await client.process_commands(message)