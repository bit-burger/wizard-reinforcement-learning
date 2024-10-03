"""
Da das Discord nur maximal 250 Rollen pro Server erlaubt,
müssen wir Rollen, die nicht mehr auf Discord gespeichert werden können, in einer Datenbank speichern.
Das Verfahren, wann welche Rolle wohin verschoben wird, ist an dem Ablauf einer MMU angelehnt.
Wenn eine Rolle erstellt, oder getaggt wurde und sich nicht im Discord befindet,
muss Platz für die Rolle geschaffen werden. Dafür wird die Rolle mit dem ältesten Timestamp aus Discord gelöscht
und als Tag in die Datenbank geschrieben.
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
"""
Klasse für die Verwaltung von Discord-Rollen und Tags in einer SQLite-Datenbank.

Attribute:
- connection: SQLite-Verbindung zur Datenbank.
- cursor: SQLite-Cursor zum Ausführen von SQL-Befehlen.

Methoden:
- insert_tag(tag_name, color, members): Fügt einen neuen Tag mit einer bestimmten Farbe und einer Liste von Mitgliedern hinzu.
- delete_tag(tag_name): Löscht einen Tag basierend auf seinem Namen.
- get_tag(tag_name): Gibt Informationen über einen bestimmten Tag zurück.
- get_tags(): Gibt eine Liste aller Tags zurück.
- get_members_by_tag(tag_name): Gibt eine Liste von Mitgliedern (Discord-User-IDs) zurück, die zu einem bestimmten Tag gehören.
- insert_role(role_name): Fügt eine neue Rolle in die Datenbank ein.
- delete_role(role_name): Löscht eine Rolle basierend auf ihrem Namen aus der Datenbank.
- update_role_last_used(role_name): Aktualisiert den Zeitstempel, wann eine Rolle zuletzt verwendet wurde.
- get_last_used_role(): Gibt die am längsten nicht verwendete Rolle zurück.
- close(): Schließt die Verbindung zur Datenbank.
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
    dc_role = discord.utils.get(guild.roles, name=role_name)
    if dc_role:
        await interaction.response.send_message(f"Role '{role_name}' already exists on Discord.")
        db.update_role_last_used(role_name)
        return
    tag = db.get_tag(role_name)
    if tag:
        await interaction.response.send_message(f"Role '{role_name}' exists in the database. Bringing it to Discord...")
        await ensure_space_for_role()
        await swap_role_in(role_name)
        await interaction.response.send_message(f"Role '{role_name}' has been successfully brought to Discord.")
        return
    if len(guild.roles) >= 250:
        last_used_role = db.get_last_used_role()
        dc_last_used_role = await discord.utils.get(guild.roles, name=last_used_role)
        if dc_last_used_role:
            await swap_role_out(dc_last_used_role)
    await swap_role_in(role_name, color, members)
    await interaction.response.send_message(f"Role '{role_name}' created and assigned to members (if provided).")


"""
Gibt eine Liste aller Tags aus und zu jedem Tag tabellarisch (in einer Ascii-Tabelle) die Mitglieder, die den Tag haben.
"""
@tree.command(name="show_tags", description="lists all tags", guild=discord.Object(1205582028905648209))
async def show_tags(interaction: discord.Interaction, limit: int = 0):
    tags = db.get_tags()
    if not tags:
        await interaction.response.send_message("No tags available.")
        return
    tag_list = []
    for tag in tags:
        members = db.get_members_by_tag(tag[0])
        member_list = ', '.join([str(member[0]) for member in members])
        tag_list.append(f"{tag[0]} (Color: {tag[1]}): {member_list or 'No members'}")
    if limit > 0:
        tag_list = tag_list[:limit]
    await interaction.response.send_message("\n".join(tag_list))


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
    if message.author.bot:
        return
    mentioned_roles = message.role_mentions
    for mentioned_role in mentioned_roles:
        db.update_role_last_used(mentioned_role.name)
    words_in_message = message.content.split()
    for word in words_in_message:
        if word.startswith('@') and len(word) > 1:
            role_name = word[1:]
            discord_role = discord.utils.get(guild.roles, name=role_name)
            if discord_role:
                continue
            tag = db.get_tag(role_name)
            if tag:
                await ensure_space_for_role()
                await swap_role_in(role_name)
                await message.channel.send(f"Role '{role_name}' exists in the database and has been re-added to Discord.")
            else:
                await message.channel.send(f"Role '{role_name}' does not exist in Discord or the database.")


"""
Wenn eine Rolle auf dem Discord Server gelöscht wird, wird die Rolle auch aus der Datenbank gelöscht.
"""
@client.event
def on_role_delete(deleted_role: discord.Role):
    db.delete_role(deleted_role.name)
    print(f"Role '{deleted_role.name}' has been deleted from Discord and the database.")


"""
Wenn eine Rolle auf dem Discord Server umbenannt wird, wird die Rolle auch aus der Datenbank umbenannt.
Dabei aktualisiert sich der Timestamp der Rolle in 'roles'.
"""
@client.event
def on_role_rename(before: discord.Role, after: discord.Role):
    db.delete_role(before.name)
    db.insert_role(after.name)
    db.update_role_last_used(after.name)
    print(f"Role '{before.name}' has been renamed to '{after.name}' in Discord and updated in the database.")


"""
Bringt eine Rolle ins Discord, entweder basierend auf der Datenbank oder mit übergebenen Attributen.
Wenn nur der Rollenname übergeben wird, werden die Farbe und/oder die Mitgliederliste aus der Datenbank geholt,
sofern diese nicht als Argumente übergeben wurden.
"""
async def swap_role_in(role_name: str, color: str = None, members: list[int] = None):
    if color is None or members is None:
        tag = db.get_tag(role_name)
        if tag:
            if color is None:
                color = tag['color']
            if members is None:
                members = [member[0] for member in db.get_members_by_tag(role_name)]
    dc_role = await guild.create_role(name=role_name, color=discord.Color(int(color.strip('#'), 16)))
    for member_id in members:
        member = guild.get_member(member_id)
        if member:
            await member.add_roles(dc_role)
    db.insert_role(role_name)
    db.delete_tag(role_name)
    print(f"Role '{role_name}' has been swapped in from the database to Discord.")


"""
Entfernt eine Rolle aus Discord und speichert sie als Tag in der Datenbank.
"""
async def swap_role_out(dc_role: discord.Role):
    members = [member.id for member in dc_role.members]
    db.insert_tag(dc_role.name, f'#{dc_role.color:06X}', members)
    await dc_role.delete()
    db.delete_role(dc_role.name)
    print(f"Role '{dc_role.name}' has been swapped out from Discord to the database.")


"""
Prüft, ob genügend Platz für eine neue Rolle ist.
Wenn nicht, wird die Rolle mit dem ältesten Timestamp gelöscht und als Tag in die Datenbank geschrieben.
"""
async def ensure_space_for_role():
    if len(guild.roles) >= 250:
        last_used_role = db.get_last_used_role()
        if last_used_role:
            dc_last_used_role = await discord.utils.get(guild.roles, name=last_used_role[0])
            if dc_last_used_role:
                await swap_role_out(dc_last_used_role)