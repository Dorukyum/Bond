from discord import Member
from discord.ext.commands import command, group
from jishaku.codeblocks import codeblock_converter
from jishaku.modules import ExtensionConverter

from utils import Cog


class Developer(Cog, command_attrs={"hidden": True}):
    def __init__(self, bot) -> None:
        super().__init__(bot)
        self.jishaku = bot.get_cog("Jishaku")

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

    @group(invoke_without_command=True)
    async def owners(self, ctx):
        await ctx.reply(
            "\n".join(
                self.bot.pycord.get_member(id).mention for id in self.bot.owner_ids
            )
        )

    @owners.command()
    async def add(self, ctx, member: Member):
        self.bot.owner_ids.append(member.id)
        self.bot.dump_config({"owner_ids": self.bot.owner_ids})
        await ctx.reply(f"Added `{member}` to owners.")

    @owners.command()
    async def remove(self, ctx, member: Member):
        self.bot.owner_ids.remove(member.id)
        self.bot.dump_config({"owner_ids": self.bot.owner_ids})
        await ctx.reply(f"Removed `{member}` from owners.")

    async def cog_check(self, ctx):
        return ctx.author.id in self.bot.owner_ids


def setup(bot):
    bot.add_cog(Developer(bot))
