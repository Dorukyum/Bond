from collections import namedtuple
from datetime import timedelta
from typing import Any, Literal

from discord.ext import commands

__all__ = ("s", "humanize_time", "Lowercase", "LogAction", "LogActions")


# functions
def s(data) -> Literal["", "s"]:
    if isinstance(data, str):
        data = int(not data.endswith("s"))
    elif hasattr(data, "__len__"):
        data = len(data)
    check = data != 1
    return "s" if check else ""


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


# converters
class _Lowercase(commands.Converter):
    async def convert(self, ctx, text):
        return text.lower()


Lowercase: Any = _Lowercase()


# enums
LogAction = namedtuple("LogData", ("color", "emoji", "text"))


class LogActions:
    BAN = LogAction("brand_red", ":hammer:", "Banned")
    UNBAN = LogAction("brand_green", ":unlock:", "Unbanned")
    KICK = LogAction("brand_red", ":hammer:", "Kicked")
    MUTE = LogAction("dark_grey", ":mute:", "Muted")
    UNMUTE = LogAction("brand_green", ":loud_sound:", "Unmuted")
    CHANNEL_CREATE = LogAction("yellow", ":heavy_plus_sign:", "Channel Created")
    CHANNEL_DELETE = LogAction("dark_orange", ":heavy_minus_sign:", "Channel Deleted")
    CHANNEL_UPDATE = LogAction("orange", ":red_circle:", "Channel Updated")
    ROLE_CREATE = LogAction("yellow", ":heavy_plus_sign:", "Role Created")
    ROLE_DELETE = LogAction("dark_orange", ":heavy_minus_sign:", "Role Deleted")
    ROLE_UPDATE = LogAction("orange", ":red_circle:", "Role Updated")
    TIMEOUT = LogAction("brand_red", ":stopwatch:", "Timed out")
