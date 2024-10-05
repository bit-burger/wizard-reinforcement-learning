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
    def __init__(self, _callable: Callable[[discord.ui.Select], Awaitable[None]],
                 custom_id: str = MISSING, placeholder: str | None = None, min_values: int = 1, max_values: int = 1,
                 options: list[discord.SelectOption] = MISSING, disabled: bool = False, row: int | None = None):
        super().__init__(custom_id=custom_id, placeholder=placeholder, min_values=min_values, max_values=max_values,
                         options=options, disabled=disabled, row=row, )
        ReactiveComponent.__init__(self)
        self.callable = _callable

    async def callback(self, interaction: discord.Interaction):
        self.ref.current_interaction = interaction
        await self.callable(self)


class Button(ui.Button, ReactiveComponent):
    def __init__(self,
                 _callable: Callable[[], Awaitable[None]] = None,
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
            await self.callable()


class UserSelect(ui.UserSelect, ReactiveComponent):
    def __init__(self, _callable: Callable[[discord.ui.UserSelect], Awaitable[None]],
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
        await self.callable(self)


class ReactiveApplicationView(ui.View):
    last_interaction: discord.Interaction | None = None
    current_interaction: discord.Interaction | None = None
    is_initial = True

    def __init__(self, ephemeral: bool = True, timeout: Optional[int] = None):
        super().__init__(timeout=timeout)
        self.ephemeral = ephemeral

    @final
    async def set_state(self):
        await self._render(to_render=self.render())

    async def _render(self, to_render: Iterator[str | discord.Embed | ui.Item]):
        self.clear_items()
        embed = None
        message_str = None
        for component in to_render:
            if isinstance(component, discord.Embed):
                embed = component
            if isinstance(component, str):
                message_str = component
            if isinstance(component, ui.Item) and isinstance(component, ReactiveComponent):
                self.add_item(component)
                component.set_ref(self)

        if self.is_initial:
            await self.current_interaction.response.send_message(embed=embed, view=self, content=message_str,
                                                    ephemeral=self.ephemeral)
            self.original_interaction = await self.current_interaction.original_response()
            self.is_initial = False
        elif self.current_interaction:
            await self.current_interaction.response.edit_message(embed=embed, view=self, content=message_str)
        else:
            await self.last_interaction.edit_original_response(embed=embed, view=self, content=message_str)
        if self.current_interaction is not None:
            self.last_interaction = self.current_interaction
            self.current_interaction = None

    @abstractmethod
    def render(self) -> Iterator[str | discord.Embed | ui.Item]:
        ...


async def run_application(interaction: discord.Interaction, application: ReactiveApplicationView, is_initial=True):
    application.is_initial = is_initial
    if is_initial:
        application.current_interaction = interaction
    else:
        application.last_interaction = interaction
    await application._render(application.render())
