from os import listdir

from discord.ext.commands import command
from jishaku.codeblocks import codeblock_converter

from utils import Cog


class Developer(Cog, command_attrs={"hidden": True}):
    @command(name="eval")
    async def _eval(self, ctx, *, code: codeblock_converter):
        cog = self.bot.get_cog("Jishaku")
        await cog.jsk_python(ctx, argument=code)

    @command()
    async def load(self, ctx, *, name):
        if name != "all":
            self.bot.load_extension(f"cogs.{name}")
            await ctx.send(name.title() + " commands are ready.")
        else:
            for file in listdir("./cogs"):
                if file.endswith(".py"):
                    self.bot.load_extension(f"cogs.{file[:-3]}")
            await ctx.send("All cogs have been loaded.")

    @command()
    async def unload(self, ctx, *, name):
        if name != "all":
            self.bot.unload_extension(f"cogs.{name}")
            await ctx.send(name.title() + " commands are disabled.")
        else:
            for file in listdir("./cogs"):
                if file.endswith(".py"):
                    self.bot.unload_extension(f"cogs.{file[:-3]}")
            await ctx.send("All cogs have been unloaded.")

    @command()
    async def reload(self, ctx, *, name):
        if name != "all":
            self.bot.reload_extension(f"cogs.{name}")
            await ctx.send(name.title() + " commands have been updated.")
        else:
            for file in listdir("./cogs"):
                if file.endswith(".py"):
                    try:
                        self.bot.reload_extension(f"cogs.{file[:-3]}")
                    except Exception as e:
                        print(e)
            await ctx.send("All cogs have been reloaded.")

    async def cog_check(self, ctx):
        return ctx.author.id in self.bot.owner_ids


def setup(bot):
    bot.add_cog(Developer(bot))
