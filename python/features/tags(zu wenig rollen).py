import discord
import peewee
from discord.ext import commands
from config import client, tree

intents = discord.Intents.default()
intents.members = True
client1 = commands.Bot(command_prefix='!', intents=intents)

db = peewee.SqliteDatabase('tags.db')


class BaseModel(peewee.Model):
    class Meta:
        database = db


class User(BaseModel):
    id = peewee.IntegerField(primary_key=True)
    name = peewee.CharField(null=False)  # Ensure name is not null


class Tag(BaseModel):
    name = peewee.CharField()


class UserTag(BaseModel):
    user = peewee.ForeignKeyField(User, backref='tags')
    tag = peewee.ForeignKeyField(Tag, backref='users')
    counter = peewee.IntegerField(default=1)


db.connect()
db.create_tables([User, Tag, UserTag])

YOUR_GUILD_ID = 1205582028905648209


# Load tags from database
def load_tags():
    tags = {}
    for user_tag in UserTag.select():
        user_id = str(user_tag.user.id)
        tag_name = user_tag.tag.name
        if user_id not in tags:
            tags[user_id] = []
        tags[user_id].append({'name': tag_name, 'counter': user_tag.counter})
    return tags


# Save tags to database
def save_tags(user_id, user_name, tag_name):
    user, created = User.get_or_create(id=user_id, defaults={'name': user_name})
    if not created and user.name != user_name:
        user.name = user_name
        user.save()

    tag_name_lower = tag_name.lower()
    tag, created = Tag.get_or_create(name=tag_name_lower, defaults={'name': tag_name})
    if not created:
        tag.name = tag_name  # Update to original case if it already exists
        tag.save()

    user_tag, created = UserTag.get_or_create(user=user, tag=tag)
    if not created:
        user_tag.counter += 1
        user_tag.save()


# Delete tags from database
def delete_tags(user_id, tag_name):
    try:
        user = User.get(User.id == user_id)
        tag_name_lower = tag_name.lower()
        tag = Tag.get(Tag.name == tag_name_lower)
        user_tag = UserTag.get(UserTag.user == user, UserTag.tag == tag)
        if user_tag.counter > 1:
            user_tag.counter -= 1
            user_tag.save()
        else:
            user_tag.delete_instance()
    except User.DoesNotExist:
        pass
    except Tag.DoesNotExist:
        pass
    except UserTag.DoesNotExist:
        pass


# Function to get the "Rollen" channel
async def get_tags_channel():
    for guild in client.guilds:
        for channel in guild.channels:
            if channel.name == 'rollen':
                return channel
    return None


# Function to update the tags message
async def update_tags_message():
    channel = await get_tags_channel()
    if not channel:
        return

    tags = load_tags()
    message_content = "### **User Tags**\n\n"
    for member_id, roles in tags.items():
        member = channel.guild.get_member(int(member_id))
        if member:
            display_name = member.display_name  # Use server-specific nickname
            roles_str = []
            for role in roles:
                if role['counter'] > 1:
                    roles_str.append(f"`{role['name']} ({role['counter']})`")
                else:
                    roles_str.append(f"`{role['name']}`")
            if roles_str:
                message_content += f"**{display_name}**: {', '.join(roles_str)}\n"

    async for message in channel.history(limit=100):
        if message.author == client.user:
            await message.edit(content=message_content)
            return
    await channel.send(message_content)


@client.event
async def ready():
    await update_tags_message()


@tree.command(name="role", description="Create or assign a tag to a user", guild=discord.Object(id=YOUR_GUILD_ID))
async def role(interaction: discord.Interaction, member: discord.Member, tag_name: str):
    save_tags(member.id, member.name, tag_name)
    await update_tags_message()
    try:
        await interaction.response.send_message(f"Tag `{tag_name}` assigned to `{member.display_name}`")
    except discord.errors.NotFound:
        await interaction.followup.send(f"Tag `{tag_name}` assigned to `{member.display_name}`")


@tree.command(name="remove_role", description="Remove a tag from a user", guild=discord.Object(id=YOUR_GUILD_ID))
async def remove_role(interaction: discord.Interaction, member: discord.Member, tag_name: str):
    delete_tags(member.id, tag_name)
    await update_tags_message()
    try:
        await interaction.response.send_message(f"Tag `{tag_name}` removed from `{member.display_name}`")
    except discord.errors.NotFound:
        await interaction.followup.send(f"Tag `{tag_name}` removed from `{member.display_name}`")


@tree.command(name="ping_role", description="Ping all users with a specific tag", guild=discord.Object(id=YOUR_GUILD_ID))
async def ping_role(interaction: discord.Interaction, tag_name: str):
    tags = load_tags()
    mentions = []
    for user_id, roles in tags.items():
        for role in roles:
            if role['name'].lower() == tag_name.lower():
                member = interaction.guild.get_member(int(user_id))
                if member:
                    mentions.append(member.mention)
    await interaction.response.send_message(f"`{tag_name}`: {' '.join(mentions)}")


@tree.command(name="update_list", description="List all users with their tags", guild=discord.Object(id=YOUR_GUILD_ID))
async def update_list(interaction: discord.Interaction):
    await update_tags_message()
    await interaction.response.send_message("Tags list updated in the 'Rollen' channel.")