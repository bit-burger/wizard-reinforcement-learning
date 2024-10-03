import discord
from peewee import Model, CharField, IntegerField, CompositeKey, fn, SqliteDatabase

from config import client, tree

db = SqliteDatabase('words.db')
db.connect()


class Word(Model):
    word = CharField()
    count = IntegerField(default=0)
    server_id = IntegerField()
    user_id = IntegerField()

    class Meta:
        database = db
        primary_key = CompositeKey('word', 'server_id', 'user_id')


db.create_tables([Word])

Word.add_index(Word.word)
Word.add_index(Word.count)
Word.add_index(Word.server_id)
Word.add_index(Word.server_id)

abc = "abcdefghijklmnopqrstuvwxyzöäü-éèáàóòñ"
rest = " ,;\n:\t/&%$\"!'*-_.,_()[]{}?`´"


@client.event
async def message(m: discord.Message):
    if m.author.bot: return

    words = [""]
    for c in m.content.lower() + " ":
        if c in abc:
            words[len(words) - 1] += c
        elif c in rest:
            if words[len(words) - 1] != "":
                words.append("")
    words.pop()
    words_with_count = {}
    for word in words:
        words_with_count[word] = words_with_count.get(word, 0) + 1
    for (word, count) in words_with_count.items():
        word_object, created = Word.get_or_create(word=word, server_id=m.guild.id, user_id=m.author.id)
        word_object.count += count
        word_object.save()


@tree.command(name="wc_all", description="lists all counted words",
              guild=discord.Object(1205582028905648209))
async def wcf(interaction: discord.Interaction, user: discord.Member = None, word: str = None, offset: int = 0):
    await wc_base(interaction, user, word, 1000000, offset)


@tree.command(name="wc", description="lists 10 most used words",
              guild=discord.Object(1205582028905648209))
async def wc(interaction: discord.Interaction, user: discord.Member = None, word: str = None, limit: int = 10,
             offset: int = 0):
    await wc_base(interaction, user, word, limit, offset)


async def wc_base(interaction: discord.Interaction, user: discord.Member = None, word: str = None, limit: int = 10,
                  offset: int = 0):
    # query = MyModel.raw('SELECT * FROM my_table WHERE data = %s', user_data)
    cost_column = fn.SUM(Word.count)
    query = Word.select(Word.word, Word.user_id, cost_column).where(
        Word.server_id == interaction.guild.id).order_by(cost_column.desc(), Word.word)
    if user:
        query = query.where(Word.user_id == user.id)
    if word:
        query = query.where(Word.word == word).group_by(Word.user_id)
    else:
        query = query.group_by(Word.word)
    words = ""
    counts = ""
    user_ids = ""
    for row in query.namedtuples()[offset:offset + limit]:
        # embed.add_field(name=row.word, value=row.count, inline=False)
        add_to_user_ids = ""
        add_to_words = f"`{row.word}`\n"
        add_to_counts = f"`{row.count}`\n"
        if not user and word:
            add_to_user_ids = f"<@{row.user_id}>\n"
        if len(add_to_words + words) >= 1024 or len(add_to_counts + counts) >= 1024 or len(
                add_to_user_ids + user_ids) >= 1024:
            break
        words += add_to_words
        counts += add_to_counts
        user_ids += add_to_user_ids
    description = ""
    if word:
        description += f"how often '{word}' "
    if user:
        description += f"by <@{user.id}>"
    if description == "":
        description = "top words"
    description += f" in {interaction.guild.name}"
    embed = discord.Embed(description=f"**{description}**").add_field(name="words", value=words).add_field(name="count",
                                                                                                           value=counts)
    if not user and word:
        embed.add_field(name="user", value=user_ids)
    await interaction.response.send_message(embed=embed)
