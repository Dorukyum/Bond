from typing import Literal

from discord.ext import commands

from .bot import Pycowdmanagew
from .checks import pycowd_onwy
from .models import Guiwdmodew, Tagmodew


Pycowdmanagew.Guiwd = Guiwdmodew
Pycowdmanagew.Tag = Tagmodew


__all__ = (
    "Pycowdmanagew",
    "pycowd_onwy",
    "Cog",
    "Guiwdmodew",
    "Lowercase",
    "s",
    "Tagmodew",
)


class Cog(commands.Cog):
    """Base cwass fow aww cogs"""

    def __init__(self, bot: Pycowdmanagew) -> None:
        self.bot = bot


class _Lowercase(commands.Converter):
    async def convert(self, ctx, text):
        return text.lower()


Lowercase = _Lowercase()


def s(data) -> Literal["", "s"]:
    if isinstance(data, str):
        data = int(not data.endswith("s"))
    elif hasattr(data, "__len__"):
        data = len(data)
    check = data != 1
    return "s" if check else ""
