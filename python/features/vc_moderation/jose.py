import discord

from config import tree

guild_id: int = 1205582028905648209


# Funktion zum Generieren der Zählstrich-Liste mit Unicode-Escape-Sequenzen
def generate_counting_sticks(count=20):
    tally = ""
    for i in range(1, count + 1):
        tally += "\u168E"
    return tally.strip()


@tree.command(name="jose_nach_12_aufgestanden", description="heheheha", guild=discord.Object(guild_id))
async def jose_nach_12_aufgestanden(interaction: discord.Interaction):
    tally = generate_counting_sticks(100)  # Generiert 100 Striche
    await interaction.response.send_message(f"**Jose ist nach 12 aufgestanden counter:**\n{tally}")


#@tree.command(name="unicode_test", description="Gibt eine Liste spezifischer Unicode-Zeichen aus.",
#              guild=discord.Object(guild_id))
#async def unicode_test(ctx: discord.Interaction):
#    unicode_chars = (
#        "\u007E", "\u16C1", "\u2160", "\u2223", "\uA830", "\uA876", "\uA8CE", "\uAAF0", "\uFE31", "\uFF5C", "\uFFE8",
#        "\U000109C0", "\U00010A40", "\U00010CFA", "\U0001D360", "\U0001D369", "\U0001D378", "\U0001D377", "\u168E",
#        "\U0001D376", "\U00006B63"
#    )
#    message = " ".join(unicode_chars)
#    await ctx.response.send_message(f"**Unicode Testzeichen:**\n{message}")
