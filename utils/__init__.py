from typing import Literal

from discord.ext import commands

from .bot import PycordManager
from .models import Tag


PycordManager.Tag = Tag


__all__ = (
    "PycordManager",
    "pycord_only",
    "Cog",
    "Lowercase",
    "s",
    "Tag",
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


class PycordOnly(commands.CheckFailure):
    pass


async def predicate(ctx):
    if ctx.guild and ctx.guild.id == 881207955029110855:
        return True
    raise PycordOnly("This command can only be used in the Pycord server.")


pycord_only = commands.check(predicate)
