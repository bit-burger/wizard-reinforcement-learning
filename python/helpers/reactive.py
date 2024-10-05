from abc import abstractclassmethod, abstractmethod
from typing import Callable, Awaitable, Any, Iterator, Optional, final

from discord import ui
import discord
from discord._types import ClientT
from discord.abc import MISSING


class ReactiveComponent:
    def __init__(self) -> None:
        self.ref = None

    def set_ref(self, ref) -> None:
        self.ref = ref


class Select(ui.Select, ReactiveComponent):
    def __init__(self, _callable: Callable[[discord.ui.Select, discord.Interaction], Awaitable[None]],
                 custom_id: str = MISSING, placeholder: str | None = None, min_values: int = 1, max_values: int = 1,
                 options: list[discord.SelectOption] = MISSING, disabled: bool = False, row: int | None = None):
        super().__init__(custom_id=custom_id, placeholder=placeholder, min_values=min_values, max_values=max_values,
                         options=options, disabled=disabled, row=row, )
        ReactiveComponent.__init__(self)
        self.callable = _callable

    async def callback(self, interaction: discord.Interaction):
        self.ref.current_interaction = interaction
        await self.callable(self, interaction)


class Button(ui.Button, ReactiveComponent):
    def __init__(self,
                 _callable: Callable[[discord.Interaction], Awaitable[None]] = None,
                 style: discord.ButtonStyle = discord.ButtonStyle.secondary,
                 label: str | None = None,
                 disabled: bool = False,
                 custom_id: str | None = None,
                 url: str | None = None,
                 emoji: str | discord.Emoji | discord.PartialEmoji | None = None,
                 row: int | None = None):
        super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji,
                         row=row)
        ReactiveComponent.__init__(self)
        self.callable = _callable

    async def callback(self, interaction: discord.Interaction):
        self.ref.current_interaction = interaction
        if self.callable:
            await self.callable(interaction)


class UserSelect(ui.UserSelect, ReactiveComponent):
    def __init__(self, _callable: Callable[[discord.ui.UserSelect, discord.Interaction], Awaitable[None]],
                 custom_id: str = MISSING,
                 placeholder: str | None = None,
                 min_values: int = 1,
                 max_values: int = 1,
                 disabled: bool = False,
                 row: int | None = None):
        super().__init__(custom_id=custom_id, placeholder=placeholder, min_values=min_values, max_values=max_values,
                         disabled=disabled, row=row)
        ReactiveComponent.__init__(self)
        self.callable = _callable

    async def callback(self, interaction: discord.Interaction[ClientT]) -> Any:
        self.ref.current_interaction = interaction
        await self.callable(self, interaction)


class ReactiveApplicationView(ui.View):
    last_interaction: discord.Interaction | None = None
    message: discord.Message | discord.TextChannel | None = None
    is_initial = True
    is_message: bool

    def __init__(self, ephemeral: bool = True, timeout: Optional[int] = None):
        super().__init__(timeout=timeout)
        self.ephemeral = ephemeral

    @final
    async def set_state(self, interaction: discord.Interaction = None):
        await self._render(to_render=self.render(), current_interaction=interaction)

    async def _render(self, to_render: Iterator[str | discord.Embed | ui.Item], current_interaction: discord.Interaction | None = None):
        self.clear_items()
        embeds = []
        message_str = None
        for component in to_render:
            if isinstance(component, discord.Embed):
                embeds.append(component)
            if isinstance(component, str):
                message_str = component
            if isinstance(component, ui.Item) and isinstance(component, ReactiveComponent):
                self.add_item(component)
                component.set_ref(self)

        if not self.message:
            if self.is_initial:
                await current_interaction.response.send_message(embeds=embeds, view=self, content=message_str,
                                                ephemeral=self.ephemeral)
                self.original_interaction = await current_interaction.original_response()
                self.is_initial = False
            elif current_interaction:
                await current_interaction.response.edit_message(embeds=embeds, view=self, content=message_str)
            else:
                await self.last_interaction.edit_original_response(embeds=embeds, view=self, content=message_str)
        else:
            if self.message is discord.TextChannel:
                self.message = await self.message.send(embeds=embeds, view=self, content=message_str)
            else:
                await self.message.edit(embeds=embeds, view=self, content=message_str)
        if current_interaction is not None:
            self.last_interaction = current_interaction

    @abstractmethod
    def render(self) -> Iterator[str | discord.Embed | ui.Item]:
        ...


async def run_application(interaction: discord.Interaction, application: ReactiveApplicationView, is_initial=True):
    application.is_initial = is_initial
    application.is_message = False
    await application._render(application.render(), interaction)

async def run_application_on_message(message: discord.Message | discord.TextChannel, application: ReactiveApplicationView):
    application.message = message
    application.is_message = True
    await application._render(application.render())
