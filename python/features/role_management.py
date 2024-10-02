from hilfen.role_database import Database
import discord
from config import client, tree

db = Database()

# Einen Tag mit Mitgliedern einfügen
db.insert_tag('Tag1', '#FF5733', [123, 456, 789])

# Einen Tag löschen
db.delete_tag('Tag1')

# Eine Rolle einfügen
db.insert_role('Admin')

# Den Timestamp der Rolle aktualisieren
db.update_role_last_used('Admin')

# Eine Rolle löschen
db.delete_role('Admin')

db.close()

@tree.command(name="role", description="creates a role", guild=discord.Object(1205582028905648209))
async def role(interaction:discord.Interaction, role_name:str, color:str='#F4F4F4', members=None):
    if members is None:
        members = []

@tree.command(name="show_tags", description="lists all tags", guild=discord.Object(1205582028905648209))
async def show_tags(interaction:discord.Interaction, limit:int=0):
    pass

@client.event
async def on_message(message):
    if message.content.startswith("@"):
        role_name = message.content[1:]
        guild = message.guild