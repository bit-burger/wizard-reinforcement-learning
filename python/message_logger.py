import logging
import pathlib
import socket
from datetime import datetime

import discord

import config


class MessageLogger(logging.Logger):
    def __init__(self, name, level=logging.DEBUG):
        super().__init__(name, level)
        self.extra_info = None

    def error(
            self,
            msg,
            *args
    ):
        super().error(self, msg, *args)
        guild: discord.Guild = config.client.get_guild(1205582028905648209)
        channel = guild.get_channel(1247244679381254226)
        embed = discord.Embed(title="Bot error",
                              description=f"**  From machine**: `{socket.gethostname()}`\n\n**From directory**: `{pathlib.Path().resolve()}`\n\n**error**:{msg}",
                              colour=0xFF0000,
                              timestamp=datetime.now())
        channel.send(embed=embed)

    def critical(
            self,
            msg,
            *args
    ):
        super().critical(self, msg, *args)
        guild: discord.Guild = config.client.get_guild(1205582028905648209)
        channel = guild.get_channel(1247244679381254226)
        embed = discord.Embed(title="Bot critical error",
                              description=f"**  From machine**: `{socket.gethostname()}`\n\n**From directory**: `{pathlib.Path().resolve()}`\n\n**error**:{msg}",
                              colour=0xFF0000,
                              timestamp=datetime.now())
        channel.send(embed=embed)
