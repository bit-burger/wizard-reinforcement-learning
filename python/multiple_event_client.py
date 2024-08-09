from typing import Any, Dict, List

import discord
from discord import Intents
from discord.client import CoroT


class MultipleEventClient(discord.Client):
    def __init__(self, *, intents: Intents, **options: Any):
        super().__init__(intents=intents, **options)
        self.extra_events: Dict[str, List[CoroT]] = {}

    def event(self, method: CoroT):
        self.extra_events.setdefault(method.__name__, [])
        self.extra_events[method.__name__].append(method)

    def dispatch(self, event: str, /, *args: Any, **kwargs: Any) -> None:
        ev = "on_" + event
        for method in self.extra_events.get(event, []) + self.extra_events.get(ev, []):
            self._schedule_event(method, ev, *args, **kwargs)  # type: ignore
