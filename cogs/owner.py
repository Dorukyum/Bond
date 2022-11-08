from discord.ext.commands import command
from jishaku.codeblocks import codeblock_converter
from jishaku.cog import Jishaku
from jishaku.modules import ExtensionConverter

from core import Cog


class Owner(Cog, command_attrs={"hidden": True}):
    def __init__(self, bot) -> None:
        super().__init__(bot)
        self.jishaku: Jishaku = bot.get_cog("Jishaku")

    @command(name="eval")
    async def _eval(self, ctx, *, code: codeblock_converter):
        await self.jishaku.jsk_python(ctx, argument=code)

    @command(aliases=["reload"])
    async def load(self, ctx, *files: ExtensionConverter):
        await self.jishaku.jsk_load(ctx, *files)

    @command()
    async def unload(self, ctx, *files: ExtensionConverter):
        await self.jishaku.jsk_unload(ctx, *files)

    @command()
    async def shutdown(self, ctx):
        await ctx.send("Shutting down.")
        await self.bot.close()

    @command()
    async def pull(self, ctx, *to_load: ExtensionConverter):
        await self.jishaku.jsk_git(ctx, argument=codeblock_converter("pull"))
        await self.jishaku.jsk_load(ctx, *to_load)

    async def cog_check(self, ctx):
        return ctx.author.id in self.bot.owner_ids


def setup(bot):
    bot.add_cog(Owner(bot))
