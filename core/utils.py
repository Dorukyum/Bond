from datetime import timedelta
from typing import Any, Literal

from discord import DiscordException
from discord.ext import commands

__all__ = (
    "s",
    "list_items",
    "humanize_time",
    "Lowercase",
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


def list_items(items) -> str:
    return (
        f"{', '.join(items[:-1])} and {items[-1]}"
        if len(items) > 1
        else items[0]
    )


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
