"""

"""
from features.role_management.role_database import Database
import discord
from config import client, tree

"""
Die Datenbank speichert Tags. 
Tags sind Rollen, die nicht mehr in Discord gespeichert werden können, weil die maximale Anzahl an Rollen erreicht wurde.
Tags haben einen Namen und eine Farbe.
Zu jedem Tag werden die Mitglieder gespeichert, die den Tag haben.
Zusätzlich werden die Rollen gespeichert, die aktuell auf dem Server existieren.
Zu diesen Rollen wird ein Timestamp gespeichert, wann sie zuletzt benutzt wurden.
"""
db = Database()

"""
Erstellt eine neue Rolle. 
Dabei ist ist der Name der Rolle das einzige Pflichtfeld.
Wenn die Rolle bereits auf Discord existiert, wird eine entsprechende Meldung angezeigt
und das zuletzt benutzte Datum der Rolle in 'roles' wird aktualisiert.
Wenn die Rolle bereits in der Datenbank existiert, wird eine entsprechende Meldung angezeigt,
die Rolle wird ins Discord gebracht, aus dem Table 'tags' entfernt und zum Table 'roles' hinzugefügt.
Wenn die Rolle noch nicht existiert wird sie ins Discord gebracht und zum Table 'roles' hinzugefügt.
"""
@tree.command(name="role", description="creates a role", guild=discord.Object(1205582028905648209))
async def role(interaction:discord.Interaction, role_name:str, color:str='#F4F4F4', members:list[int]=None):
    pass

"""
Gibt eine Liste aller Tags aus und zu jedem Tag tabellarisch die Mitglieder, die den Tag haben.
"""
@tree.command(name="show_tags", description="lists all tags", guild=discord.Object(1205582028905648209))
async def show_tags(interaction:discord.Interaction, limit:int=0):
    pass

"""

"""
@client.event
async def on_message(message:discord.Message):
    if message.content.startswith("@"):
        role_name:str = message.content[1:]
        guild:discord.Guild = message.guild

"""
Wenn eine Rolle auf dem Discord Server gelöscht wird, wird die Rolle auch aus der Datenbank gelöscht.
"""
@client.event
def on_role_delete(deleted_role:discord.Role):
    pass