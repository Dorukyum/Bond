from discord.ext import commands

from .bot import Toolkit
from .context import Context
from .models import GuildModel, TagModel, WarnModel
from .utils import Lowercase, humanize_time, s, list_items

__all__ = (
    "Toolkit",
    "Cog",
    "Context",
    "GuildModel",
    "Lowercase",
    "s",
    "list_items",
    "TagModel",
    "WarnModel",
    "humanize_time",
)


class Cog(commands.Cog):
    """Base class for all cogs"""

    def __init__(self, bot: Toolkit) -> None:
        self.bot = bot
