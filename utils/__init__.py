from typing import Literal

from discord.ext import commands
from tortoise import fields
from tortoise.models import Model

from .bot import PycordManager

__all__ = ("PycordManager", "Cog", "Lowercase", "s", "Tag")


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


class Tag(Model):
    name = fields.TextField()
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    author_id = fields.IntField()
    guild_id = fields.IntField()
    content = fields.TextField()
    uses = fields.IntField()

    def __str__(self):
        return self.content


PycordManager.Tag = Tag
