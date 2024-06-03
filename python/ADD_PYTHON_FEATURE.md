# How to add a python feature

## Create new file `feature.py`
```py
from python.config import client
import discord
@client.event
async def message(m: discord.Message):
    print(m.content)
```

[For other events](https://discordpy.readthedocs.io/en/stable/api.html#discord-api-events)

## Add to `__init__.py`:
```py
from . import lennart
```
