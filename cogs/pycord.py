from inspect import cleandoc

import discord
from discord.ext.commands import Context, command, has_permissions

from utils import Cog, pycord_only

async def getattrs(ctx):
    try:
        input = ctx.options["thing"]
        thing = discord
        path = "discord"
        for attr in input.split("."):
            if attr == "discord":
                continue
            thing = getattr(thing, attr)
            path += f".{attr}"
        return [f"{path}.{x}" for x in dir(thing) if not x.startswith("_")][:25]
    except AttributeError:
        return [f"{path}.{x}" for x in dir(thing) if x.startswith(attr)][:25]

class Pycord(Cog):
    """A cog for Pycord-related commands."""

    def __init__(self, bot):
        super().__init__(bot)
        self.staff_list = None
        self.staff_list_channel = None

    async def convert_attr(self, path):
        thing = discord
        for attr in path.split("."):
            if attr == "discord":
                continue
            try:
                thing = getattr(thing, attr)
            except AttributeError:
                return None, None
        return thing, path

    @discord.slash_command(name="doc", guild_ids=[881207955029110855])
    @discord.option("thing", autocomplete=getattrs)
    async def _get_doc(self, ctx, thing):
        """View the docstring of an attribute of the discord module."""
        thing, path = await self.convert_attr(thing)
        if not thing:
            return await ctx.respond("Item not found.")
        if thing.__doc__ is None:
            return await ctx.respond(f"Couldn't find documentation for `{path}`.")

        await ctx.respond(f"```\n{cleandoc(thing.__doc__)[:1993]}```")

    @discord.slash_command()
    @discord.option("examples", description="Type examples to show, seperate examples by \",\"")
    async def example(self, ctx, examples):
        """Show examples from py-cord repository."""
        examples = examples.split(", ")
        pycord_examples = self.bot.pycord_examples
        results = {example: [] for example in examples}
        def do_check(a, b):
            return a in b
        for example in examples:
            for pyc_ex in pycord_examples:
                name = pyc_ex["name"]
                url = pyc_ex["url"]
                if do_check(example, name):
                    results[example].append(pyc_ex)
        embed = discord.Embed(colour=0xADD8E6)
        embed.description = ""
        for example, results in results.items():
            embed.description += f"""
{'\n'.join("[{result["url"]}](`{result["name"]}`)" for result in results)}

"""
        embed.description = embed.description.strip("\n") # remove extra spaces
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Pycord(bot))
