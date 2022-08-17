from discord import ApplicationContext

from .utils import BotMissingPermissions


class Context(ApplicationContext):
    async def assert_permissions(self, **permissions: bool) -> None:
        if missing := [
            perm
            for perm, value in permissions.items()
            if getattr(self.app_permissions, perm) != value
        ]:
            raise BotMissingPermissions(missing)
