from collections import namedtuple
from datetime import timedelta
from typing import Any, Literal

from discord import Color, DiscordException
from discord.ext import commands

__all__ = (
    "s",
    "humanize_time",
    "Lowercase",
    "LogAction",
    "LogActions",
    "BotMissingPermissions",
)


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
    WARN = LogAction(Color.yellow(), ":warning:", "Warned")
    TIMEOUT = LogAction(Color.dark_orange(), ":stopwatch:", "Timed out")
    KICK = LogAction(Color.orange(), ":boot:", "Kicked")
    BAN = LogAction(Color.from_rgb(255, 0, 0), ":no_entry_sign:", "Banned")
    UNBAN = LogAction(Color.brand_green(), ":unlock:", "Unbanned")
    # CHANNEL_CREATE = LogAction(Color.yellow(), ":heavy_plus_sign:", "Created channel")
    # CHANNEL_DELETE = LogAction(Color.dark_orange(), ":heavy_minus_sign:", "Deleted channel")
    CHANNEL_UPDATE = LogAction(Color.orange(), ":wrench:", "Updated channel")
    # ROLE_CREATE = LogAction(Color.yellow(), ":heavy_plus_sign:", "Created role")
    # ROLE_DELETE = LogAction(Color.dark_orange(), ":heavy_minus_sign:", "Deleted role")
    ROLE_UPDATE = LogAction(Color.orange(), ":wrench:", "Updated role")


# exceptions
class BotMissingPermissions(DiscordException):
    def __init__(self, permissions) -> None:
        missing = [
            f"**{perm.replace('_', ' ').replace('guild', 'server').title()}**"
            for perm in permissions
        ]
        sub = (
            f"{', '.join(missing[:-1])} and {missing[-1]}"
            if len(missing) > 1
            else missing[0]
        )
        super().__init__(f"I require {sub} permissions to run this command.")
