from discord.ext import commands

from .bot import Toolkit
from .models import GuildModel, TagModel, WarnModel
from .utils import LogAction, LogActions, Lowercase, humanize_time, s

__all__ = (
    "Toolkit",
    "Cog",
    "GuildModel",
    "Lowercase",
    "s",
    "TagModel",
    "WarnModel",
    "LogAction",
    "LogActions",
    "humanize_time",
)


class Cog(commands.Cog):
    """Base class for all cogs"""

    def __init__(self, bot: Toolkit) -> None:
        self.bot = bot
