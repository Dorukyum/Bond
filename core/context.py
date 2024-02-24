from discord import ApplicationContext, Color, Embed
from discord.utils import utcnow

from .utils import BotMissingPermissions


class Context(ApplicationContext):
    async def assert_permissions(self, **permissions: bool) -> None:
        if missing := [
            perm
            for perm, value in permissions.items()
            if getattr(self.app_permissions, perm) != value
        ]:
            raise BotMissingPermissions(missing)

    async def success(self, title: str, description: str | None = None, **kwargs):
        embed = Embed(
            title=title,
            description=description,
            timestamp=utcnow(),
            color=Color.green(),
        )
        return await self.respond(embed=embed, **kwargs)

    async def exception(self, title: str, description: str | None = None, **kwargs):
        embed = Embed(
            title=title,
            description=description,
            timestamp=utcnow(),
            color=Color.red(),
        )
        return await self.respond(embed=embed, **kwargs)

    async def info(self, title: str, description: str | None = None, **kwargs):
        embed = Embed(
            title=title,
            description=description,
            timestamp=utcnow(),
            color=0xFFFFFF,
        )
        return await self.respond(embed=embed, **kwargs)

