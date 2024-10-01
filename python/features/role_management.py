import discord
from discord.ext import commands
import sqlite3

# Setup
bot = commands.Bot(command_prefix="/")

# SQLite-DB für die Tags
conn = sqlite3.connect('tags.db')
c = conn.cursor()

# Tabelle für Tags erstellen (Name, Farbe, Members)
c.execute('''CREATE TABLE IF NOT EXISTS tags
             (name TEXT PRIMARY KEY, color TEXT, members TEXT)''')


# Funktion, um die Rollen zu prüfen und ggf. eine alte zu verschieben
async def check_and_add_role(guild, role_name, color):
    roles = guild.roles
    if len(roles) >= 250:  # Wenn das Limit erreicht ist
        # Aging Algorithmus: Wähle die am wenigsten genutzte Rolle
        least_used_role = min(roles, key=lambda role: role.usage_count)  # Beispiel für Zähler
        # Speichere diese Rolle als Tag in der Datenbank
        c.execute("INSERT INTO tags (name, color, members) VALUES (?, ?, ?)",
                  (least_used_role.name, str(least_used_role.color),
                   ",".join([str(member.id) for member in least_used_role.members])))
        conn.commit()
        # Lösche die Rolle aus Discord
        await least_used_role.delete()

    # Erstelle die neue Rolle
    await guild.create_role(name=role_name, color=discord.Color(int(color, 16)))


# /role Command
@bot.command()
async def role(ctx, role_name, color="0xFFFFFF"):
    guild = ctx.guild
    # Check if role already exists
    existing_role = discord.utils.get(guild.roles, name=role_name)
    if existing_role:
        await ctx.send(f"Rolle `{role_name}` existiert bereits.")
    else:
        # Check and add role if possible
        await check_and_add_role(guild, role_name, color)
        await ctx.send(f"Rolle `{role_name}` wurde erstellt.")


# Tag handling (@role_name)
@bot.event
async def on_message(message):
    if message.content.startswith("@"):
        role_name = message.content[1:]
        guild = message.guild
        # Check if role exists in Discord
        existing_role = discord.utils.get(guild.roles, name=role_name)
        if existing_role:
            pass  # If the role exists, do nothing
        else:
            # Check if it's a tag in the database
            c.execute("SELECT * FROM tags WHERE name=?", (role_name,))
            tag = c.fetchone()
            if tag:
                # Move tag to a role in Discord
                await check_and_add_role(guild, tag[0], tag[1])
                await message.channel.send(f"Tag `{role_name}` wurde zur Rolle.")
            else:
                await message.channel.send(f"Rolle oder Tag `{role_name}` existiert nicht.")
    await bot.process_commands(message)


bot.run('YOUR_DISCORD_BOT_TOKEN')
