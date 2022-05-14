from collections import namedtuple
from datetime import timedelta
from typing import Literal

from discord.ext import commands

from .bot import PycordManager
from .checks import pycord_only
from .models import GuildModel, TagModel, WarnModel


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
    "humanize_time",
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
    TIMEOUT = ModAction("brand_red", ":stopwatch:", "Timed out")


def humanize_time(time: timedelta) -> str:
    if time.days > 365:
        years, days = divmod(time.days, 365)
        return f"{years} year{s(years)} and {days} day{s(days)}"
    if time.days > 1:
        return f"{time.days} day{s(time.days)}, {humanize_time(timedelta(seconds=time.seconds))}"
    hours, seconds = divmod(time.seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if hours > 0:
        return f"{hours} hour{s(hours)} and {minutes} minute{s(minutes)}"
    if minutes > 0:
        return f"{minutes} minute{s(minutes)} and {seconds} second{s(seconds)}"
    return f"{seconds} second{s(seconds)}"