import asyncio
from typing import Tuple, Iterator

import discord
from discord import ui

from config import tree
from helpers.reactive import ReactiveApplicationView, run_application, Button


class InteractiveApplication(ReactiveApplicationView):
    fib: Tuple[int, int]
    button = True

    def __init__(self):
        super().__init__(ephemeral=True)
        self.fib = (0, 1)

    async def fibonnaci(self):
        while 1:
            self.fib = (self.fib[1], self.fib[0] + self.fib[1])
            await self.set_state()
            await asyncio.sleep(0.75)

    def render(self) -> Iterator[str | discord.Embed | ui.Item]:
        yield str(self.fib[0])  # text beispiel
        yield discord.Embed(title=str(self.fib[0]))  # embed beispiel
        yield discord.Embed(description="zweites embed")  # embed beispiel
        embed = discord.Embed()  # embed beispiel
        embed.add_field(name="assdfasdsafasdfaassdfas", value="assdfasdsafasdfaassdfasd")
        embed.add_field(name="assdfasdsafasdfaassdfas", value="assdfasdsafasdfaassdfasd")
        embed.add_field(name="assdfasdsafasdfaassdfas", value="assdfasdsafasdfaassdfasd")
        yield embed
        if self.button:
            yield Button(label="miaow", _callable=self.fibonnaci)  # button beispiel

@tree.command(name="interactive_example", description="Startet eine Wizard Runde",
              guild=discord.Object(1205582028905648209))
async def miaow(interaction: discord.Interaction):
    await run_application(interaction, InteractiveApplication())
