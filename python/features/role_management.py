from dataclasses import dataclass
import discord
import sqlite3
from datetime import datetime
from config import client
from config import tree


@dataclass
class Role:
    name: str
    color: str
    members: list


conn = sqlite3.connect('tags.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS tags
(
    name      TEXT PRIMARY KEY,
    color     TEXT,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
''')

c.execute('''
CREATE TABLE IF NOT EXISTS members
(
    member_name TEXT,
    tag_name    TEXT REFERENCES tags (name) ON DELETE CASCADE,
    counter    INTEGER DEFAULT 1,
    PRIMARY KEY (member_name, tag_name)
);
''')


def insert_role(role_name: str, color: str):
    c.execute("INSERT INTO tags (name, color) VALUES (?, ?)", (role_name, color))
    conn.commit()


def delete_role(role_name: str):
    c.execute("DELETE FROM tags WHERE name = ?", (role_name,))
    conn.commit()


def get_role(role_name: str):
    c.execute("SELECT * FROM tags WHERE name = ?", (role_name,))
    result = c.fetchone()
    if result:
        return Role(result[0], result[1], [])
    return None


def get_all_roles():
    c.execute("SELECT name FROM tags")
    result = c.fetchall()
    return [role[0] for role in result]


# updates the last_used column of a role in the database
def update_last_used_role(role_name: str):
    now = datetime.now()
    c.execute("UPDATE tags SET last_used = ? WHERE name = ?", (now, role_name))
    conn.commit()


# elects the least recently used role from the database by aging algorithm
def get_least_recently_used_role():
    c.execute("SELECT name FROM tags ORDER BY last_used LIMIT 1")
    result = c.fetchone()
    if result:
        return result[0]
    return None


def get_all_roles_for_member(member_name: str):
    c.execute("SELECT tag_name FROM members WHERE member_name = ?", (member_name,))
    result = c.fetchall()
    return [role[0] for role in result]


def get_all_members():
    c.execute("SELECT member_name FROM members")
    result = c.fetchall()
    return [member[0] for member in result]


def get_all_members_for_role(role_name: str):
    c.execute("SELECT member_name FROM members WHERE tag_name = ?", (role_name,))
    result = c.fetchall()
    return [member[0] for member in result]


def remove_member_from_role(member_name: str, role_name: str):
    c.execute("DELETE FROM members WHERE member_name = ? AND tag_name = ?", (member_name, role_name))
    conn.commit()


def add_member_to_role(member_name: str, role_name: str):
    c.execute("INSERT INTO members (member_name, tag_name) VALUES (?, ?)", (member_name, role_name))
    conn.commit()


def increment_member_role_counter(member_name: str, role_name: str):
    c.execute("UPDATE members SET counter = counter + 1 WHERE member_name = ? AND tag_name = ?",
              (member_name, role_name))
    conn.commit()

def decrement_member_role_counter(member_name: str, role_name: str):
    c.execute("UPDATE members SET counter = counter - 1 WHERE member_name = ? AND tag_name = ?",
              (member_name, role_name))
    conn.commit()


# reagiert auf ein @ im Chat und dient als Einstiegspunkt für die Befehle
@client.event
async def on_message(message):
    pass


# Fügt eine neue Rolle hinzu, die neue Rolle wird in Discord hinzugefügt
@tree.command(name="add_role", description="Fügt eine Rolle hinzu", guild=discord.Object(1205582028905648209))
async def role(ctx: discord.Interaction, role_name: str, color: str = "0xF4F4F4"):
    pass


# Listet alle Tags (Rollen in der DB) mit ihren Members auf
@tree.command(name="show_tags", description="Listet die Tags", guild=discord.Object(1205582028905648209))
async def show_tags(interaction: discord.Interaction):
    pass

# geht die Datenbank und Discord durch und schaut wo die Rolle ist
def role_walk(role: Role):
    pass

# Fügt eine Rolle in Discord hinzu
def swap_role_in(guild: discord.Guild, role: Role):
    pass

# Entfernt eine Rolle aus Discord und fügt sie in die Datenbank hinzu
def swap_role_out(guild: discord.Guild, role: Role):
    pass

# TODO: prüfe ob eine rolle for swap_out 'dirty' ist,
#  daher z.B. Farbe, Member o.ä. verändert wurden
