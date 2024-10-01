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
# TODO: relation between members and tags is missing
c.execute('''CREATE TABLE IF NOT EXISTS tags
             (name TEXT PRIMARY KEY, color TEXT, last_used TIMESTAMP);''')

c.execute('''CREATE TABLE IF NOT EXISTS members
             (PRIMARY KEY(member_name, tag_name), member_name TEXT, tag_name TEXT REFERENCES tags(name) ON DELETE CASCADE);''')


# Funktion: Aktualisieren des letzten Nutzungszeitpunkts einer Rolle in der DB
def update_last_used(role_name):
    now = datetime.now()
    c.execute("UPDATE tags SET last_used = ? WHERE name = ?", (now, role_name))
    conn.commit()


def page_walk(role_name):
    pass

async def page_fault(ctx, rolle:Rolle):
    pass

async def swap_page_in(guild, rolle:Rolle):
    new_role = await guild.create_role(name=rolle.name, color=discord.Color(int(rolle.color, 16)))
    for member_id in rolle.members:
        member = guild.get_member(int(member_id))
        if member:
            await member.add_roles(new_role)
    update_last_used(rolle.name)  # Aktualisieren des Nutzungszeitpunkts
    return new_role


# Funktion: Swap Page Out - Rolle in den Tag umwandeln und löschen
async def swap_page_out(guild, rolle:Rolle):
    members = ','.join([str(member.id) for member in rolle.members])
    now = datetime.now()
    c.execute("INSERT INTO tags (name, color, last_used) VALUES (?, ?, ?)",
              (rolle.name, str(rolle.color), members, now))
    conn.commit()
    await rolle.delete()


# Funktion: Rolle hinzufügen
async def add_role(ctx:discord.Interaction, role_name, color="0xFFFFFF"):
    pass


# Aging-Algorithmus zum Wählen der Rolle, die am längsten nicht verwendet wurde
async def find_least_recently_used_role(guild):
    # Hole alle Rollen aus der DB, die Zeitstempel enthalten
    c.execute("SELECT name FROM tags ORDER BY last_used LIMIT 1")
    result = c.fetchone()

    if result:
        # Die am längsten nicht verwendete Rolle finden
        role_name = result[0]
        discord_role = await discord.utils.get(guild.roles, name=role_name)
        if discord_role:
            return discord_role
    raise Exception("No role found")


# /role Befehl
@tree.command(name="role", description="list roles", guild=discord.Object(1205582028905648209))
async def role(ctx:discord.Interaction, role_name:str, color:str="0xFFFFFF"):
    pass


# @rollenname erkennen
@client.event
async def on_message(message):
    pass


# Slash-Befehl zum Anzeigen aller Tags mit Mitgliedern
@tree.command(name="show_tags", description="Zeige alle gespeicherten Tags mit Mitglieder", guild=discord.Object(1205582028905648209))
async def show_tags(interaction: discord.Interaction):
    pass

