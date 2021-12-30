from typing import Literal

from discord.ext import commands

from .bot import PycordManager
from .checks import pycord_only
from .models import GuildModel, TagModel


PycordManager.Guild = GuildModel
PycordManager.Tag = TagModel


__all__ = (
    "PycordManager",
    "pycord_only",
    "Cog",
    "GuildModel",
    "Lowercase",
    "s",
    "TagModel",
)


class Cog(commands.Cog):
    """Base class for all cogs"""

    def __init__(self, bot: PycordManager) -> None:
        self.bot = bot


class _Lowercase(commands.Converter):
    async def convert(self, ctx, text):
        return text.lower()


Lowercase = _Lowercase()


def s(data) -> Literal["", "s"]:
    check = data == 1
    if hasattr(data, "endswith"):
        check = not data.endswith("s")
    elif hasattr(data, "__len__"):
        check = len(data) == 1
    return "s" if check else ""
