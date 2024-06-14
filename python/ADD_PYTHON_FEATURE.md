# How to add a python feature

## Create new file `feature.py`

```py
from config import client
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

# How to set up llama3
## Install Ollama from their webside
## Run this in Terminal: 
```cmd
ollama run llama3 
```