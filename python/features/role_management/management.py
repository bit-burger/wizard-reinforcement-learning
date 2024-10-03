"""
Da das Discord nur maximal 250 Rollen pro Server erlaubt,
müssen wir Rollen, die nicht mehr auf Discord gespeichert werden können, in einer Datenbank speichern.
Das Verfahren, wann welche Rolle wohin verschoben wird, ist an dem Ablauf einer MMU angelehnt.
Wenn eine Rolle erstellt, oder getaggt wurde und sich nicht im Discord befindet,
muss Platz für die Rolle geschaffen werden. Dafür wird die Rolle mit dem ältesten Timestamp aus Discord gelöscht
und als Tag in die Datenbank geschrieben.
Die Datenbank ist über eine Datenbankklasse erreichbar, die beispielsweise wie folgt genutzt werden kann:

# Import
from features.role_management.database import Database
# Initialisierung
db = Database()
# Einen Tag mit Mitgliedern einfügen
db.insert_tag('Tag1', '#FF5733', [708227359916163137, 7082273889161343137])
# Einen Tag löschen
db.delete_tag('Tag1')
# Einen Tag auslesen
get_tag('Tag1')
# Mitglieder zu einem Tag auslesen
get_members_by_tag('Tag1')
# Eine Rolle einfügen
db.insert_role('Admin')
# Den Timestamp der Rolle aktualisieren
db.update_role_last_used('Admin')
# Eine Rolle löschen
db.delete_role('Admin')
# Die Rolle mit dem ältesten Timestamp auslesen
db.get_last_used_role
# Verbindung schließen
db.close()
"""
from features.role_management.database import Database
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

guild = client.get_guild(1205582028905648209)

"""
Erstellt eine neue Rolle. 
Dabei ist ist der Name der Rolle das einzige Pflichtfeld.
Wenn die Rolle bereits auf Discord existiert, wird eine entsprechende Meldung angezeigt, 
dass die Rolle bereits im Discord existiert,
und das zuletzt benutzte Datum der Rolle in 'roles' wird aktualisiert.
Wenn die Rolle nur in der Datenbank existiert, wird eine entsprechende Meldung angezeigt, dass die Rolle ins Discord gebracht wird.
Wenn nicht ausreichend Platz für die Rolle auf Discord ist, wird die Rolle mit dem ältesten Timestamp gelöscht und als Tag in die Datenbank geschrieben.
Die Rolle wird ins Discord gebracht, aus dem Table 'tags' entfernt und zum Table 'roles' hinzugefügt.
Anschließend wird die Rolle allen Mitgliedern hinzugefügt, die den Tag hatten.
Wenn die Rolle noch nicht existiert wird sie ins Discord gebracht und zum Table 'roles' hinzugefügt.
Wenn nicht ausreichend Platz ist, wird erst die Rolle mit dem ältesten Timestamp gelöscht und als Tag in die Datenbank geschrieben.
"""
@tree.command(name="role", description="creates a role", guild=discord.Object(1205582028905648209))
async def role(interaction: discord.Interaction, role_name: str, color: str = '#F4F4F4', members: list[int] = None):
    pass


"""
Gibt eine Liste aller Tags aus und zu jedem Tag tabellarisch (in einer Ascii-Tabelle) die Mitglieder, die den Tag haben.
"""
@tree.command(name="show_tags", description="lists all tags", guild=discord.Object(1205582028905648209))
async def show_tags(interaction: discord.Interaction, limit: int = 0):
    pass


"""
Wird getriggert wenn eine Nachricht ein @<rollen_name> enthält.
Wenn es die Rolle bereits im Discord gibt, wird das zuletzt benutzte Datum der Rolle in 'roles' aktualisiert.
Wenn es die Rolle nicht im Discord, aber in der Datenbank gibt, wird die Rolle ins Discord gebracht, 
aus dem Table 'tags' entfernt und zum Table 'roles' hinzugefügt.
Anschließend wird die Rolle allen Mitgliedern hinzugefügt, die den Tag hatten.
Wenn es die Rolle weder im Discord noch in der Datenbank gibt, wird eine entsprechende Meldung ausgegeben.
"""
@client.event
async def on_message(message: discord.Message):
    pass


"""
Wenn eine Rolle auf dem Discord Server gelöscht wird, wird die Rolle auch aus der Datenbank gelöscht.
"""
@client.event
def on_role_delete(deleted_role: discord.Role):
    pass


"""
Wenn eine Rolle auf dem Discord Server umbenannt wird, wird die Rolle auch aus der Datenbank umbenannt.
Dabei aktualisiert sich der Timestamp der Rolle in 'roles'.
"""
@client.event
def on_role_rename(before: discord.Role, after: discord.Role):
    pass


"""

"""
async def swap_role_in(role_name: str):
    tag = db.get_tag(role_name)
    if tag:
        color = tag['color']
        members = db.get_members_by_tag(role_name)
        dc_role = await guild.create_role(name=role_name, color=discord.Color(int(color.strip('#'), 16)))
        for member_id in members:
            member = guild.get_member(member_id)
            if member:
                await member.add_roles(dc_role)
        db.insert_role(role_name)
        db.delete_tag(role_name)
        db.update_role_last_used(role_name) #TODO: ist notwendig, oder passiert das schon in insert_role?


"""

"""
async def swap_role_out(dc_role: discord.Role):
    members = [member.id for member in dc_role.members]
    db.insert_tag(dc_role.name, f'#{dc_role.color:06X}', members)
    await dc_role.delete()
    db.delete_role(dc_role.name)

