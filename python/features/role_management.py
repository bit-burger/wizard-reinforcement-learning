from dataclasses import dataclass
import discord
import sqlite3
from datetime import datetime
from config import client
from config import tree



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
             (name TEXT PRIMARY KEY, color TEXT, members TEXT, last_used TIMESTAMP)''')


# Funktion: Aktualisieren des letzten Nutzungszeitpunkts einer Rolle in der DB
def update_last_used(role_name):
    now = datetime.now()
    c.execute("UPDATE tags SET last_used = ? WHERE name = ?", (now, role_name))
    conn.commit()


# Funktion: Page Walk - Rolle in der SQLite-Datenbank suchen
def page_walk(role_name):
    c.execute("SELECT * FROM tags WHERE name=?", (role_name,))
    tag = c.fetchone()
    if tag:
        # Tag in eine Rolle umwandeln und zurückgeben
        members = tag[2].split(',')
        update_last_used(role_name)  # Aktualisieren, wenn Rolle verwendet wird
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
    update_last_used(saved_role.name)  # Aktualisieren des Nutzungszeitpunkts
    return new_role


# Funktion: Swap Page Out - Rolle in den Tag umwandeln und löschen
async def swap_page_out(guild, discord_role):
    members = ','.join([str(member.id) for member in discord_role.members])
    now = datetime.now()
    c.execute("INSERT INTO tags (name, color, members, last_used) VALUES (?, ?, ?, ?)",
              (discord_role.name, str(discord_role.color), members, now))
    conn.commit()
    await discord_role.delete()


# Funktion: Rolle hinzufügen
async def add_role(ctx, role_name, color="0xFFFFFF"):
    guild = ctx.guild
    discord_role = discord.utils.get(guild.roles, name=role_name)

    if discord_role:
        await ctx.send(f"Rolle `{role_name}` existiert bereits.")
        update_last_used(role_name)  # Zeitstempel aktualisieren
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


# Aging-Algorithmus zum Wählen der Rolle, die am längsten nicht verwendet wurde
def find_least_recently_used_role(guild):
    # Hole alle Rollen aus der DB, die Zeitstempel enthalten
    c.execute("SELECT name FROM tags ORDER BY last_used LIMIT 1")
    result = c.fetchone()

    if result:
        # Die am längsten nicht verwendete Rolle finden
        role_name = result[0]
        discord_role = discord.utils.get(guild.roles, name=role_name)
        if discord_role:
            return discord_role
    return None


# /role Befehl
@client.command()
async def role(ctx, role_name, color="0xFFFFFF"):
    guild = ctx.guild

    if len(guild.roles) >= 250:  # Wenn das Limit erreicht ist
        oldest_role = await find_least_recently_used_role(guild)
        if oldest_role:
            await swap_page_out(guild, oldest_role)  # Swap Page Out
            await ctx.send(f"Rolle `{oldest_role.name}` wurde in einen Tag umgewandelt.")
        else:
            await ctx.send(f"Es gibt keine alte Rolle zum Auslagern.")

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
            update_last_used(role_name)  # Zeitstempel aktualisieren
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


# Slash-Befehl zum Anzeigen aller Tags mit Mitgliedern
@tree.command(name="show_tags", description="Zeige alle gespeicherten Tags und Mitglieder")
async def show_tags(interaction: discord.Interaction):
    # Alle Tags mit Mitgliedern aus der DB abrufen
    c.execute("SELECT name, members FROM tags")
    tags = c.fetchall()

    if tags:
        # Tags formatieren und die Mitglieder anzeigen
        formatted_tags = []
        for tag in tags:
            tag_name = tag[0]
            members = tag[1].split(',') if tag[1] else []

            if members:
                # Formatierte Ausgabe der Mitglieder IDs
                members_list = "\n  - ".join(members)
                formatted_tags.append(f"Tag: `{tag_name}`\nMitglieder:\n  - {members_list}")
            else:
                formatted_tags.append(f"Tag: `{tag_name}`\nKeine Mitglieder vorhanden.")

        # Alle Tags und Mitglieder als Nachricht senden
        await interaction.response.send_message(
            f"Hier sind die gespeicherten Tags und ihre Mitglieder:\n```\n" + "\n\n".join(formatted_tags) + "\n```")
    else:
        await interaction.response.send_message("Es sind keine Tags gespeichert.")

