from collections import namedtuple
from typing import Literal

from discord.ext import commands

from .bot import PycordManager
from .checks import pycord_only
from .models import GuildModel, TagModel, WarnModel


PycordManager.Guild = GuildModel
PycordManager.Tag = TagModel
PycordManager.Warn = WarnModel


__all__ = (
    "PycordManager",
    "pycord_only",
    "Cog",
    "GuildModel",
    "Lowercase",
    "s",
    "TagModel",
    "WarnModel",
    "ModAction",
    "ModActions",
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
    if isinstance(data, str):
        data = int(not data.endswith("s"))
    elif hasattr(data, "__len__"):
        data = len(data)
    check = data != 1
    return "s" if check else ""


ModAction = namedtuple("LogData", ("color", "emoji", "text"))


class ModActions:
    BAN = ModAction("brand_red", ":hammer:", "Banned")
    UNBAN = ModAction("brand_green", ":unlock:", "Unbanned")
    KICK = ModAction("brand_red", ":hammer:", "Kicked")
    MUTE = ModAction("dark_grey", ":mute:", "Muted")
    UNMUTE = ModAction("brand_green", ":loud_sound:", "Unmuted")
    CHANNEL_CREATE = ModAction("yellow", ":heavy_plus_sign:", "Channel Created")
    CHANNEL_DELETE = ModAction("dark_orange", ":heavy_minus_sign:", "Channel Deleted")
    CHANNEL_UPDATE = ModAction("orange", ":red_circle:", "Channel Updated")
    ROLE_CREATE = ModAction("yellow", ":heavy_plus_sign:", "Role Created")
    ROLE_DELETE = ModAction("dark_orange", ":heavy_minus_sign:", "Role Deleted")
    ROLE_UPDATE = ModAction("orange", ":red_circle:", "Role Updated")
