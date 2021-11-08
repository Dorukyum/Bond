from discord.ext.commands import (
    command,
    group,
    is_owner
)
from jishaku.codeblocks import codeblock_converter
from jishaku.modules import ExtensionConverter

from utils import Cog


class Developer(Cog, command_attrs={"hidden": True}):
    def __init__(self, bot) -> None:
        super().__init__(bot)
        self.jishaku = bot.get_cog("Jishaku")
        self.blacklisted_users = []

    @command(name="eval")
    async def _eval(self, ctx, *, code: codeblock_converter):
        await self.jishaku.jsk_python(ctx, argument=code)

    @command(aliases=["reload"])
    async def load(self, ctx, *files: ExtensionConverter):
        await self.jishaku.jsk_load(ctx, *files)

    @command()
    async def unload(self, ctx, *files: ExtensionConverter):
        await self.jishaku.jsk_unload(ctx, *files)

    @group(invoke_without_command=True)
    @is_owner()
    async def blacklist(self, ctx):
        await ctx.send("Hey! You can use `!blacklist user` or `!blacklist guild` to blacklist!")

    @blacklist.command()
    async def user(self, ctx, user: discord.Member=None):
        await self.blacklisted_users.append(user.id)
        await ctx.send(f"Blacklisted {user.mention}")

    @command()
    async def shutdown(self, ctx):
        await ctx.send("Shutting down.")
        await self.bot.close()

    @command()
    async def pull(self, ctx):
        cog = self.bot.get_cog("Jishaku")
        await cog.jsk_git(ctx, argument="pull")

    async def cog_check(self, ctx):
        return ctx.author.id in self.bot.owner_ids


def setup(bot):
    bot.add_cog(Developer(bot))
