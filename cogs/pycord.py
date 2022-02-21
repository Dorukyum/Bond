from inspect import cleandoc
from utils import Cog, pycord_only
from textwrap import indent

import discord
from discord.ext.commands import command, Context, has_permissions, guild_only

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
        self.suggestions_channel = None

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
        examples = examples.split(",")
        pycord_examples = self.bot.pycord_examples
        results = {example: [] for example in range(len(examples))}
        def do_check(a, b):
            return a in b
        for example in examples:
            for pyc_example_name, example_url in pycord_examples.items():
                if do_check(example, pyc_example_name):
                    results[example].append({pyc_example_name: example_url})
        embed = discord.Embed(colour=0xADD8E6)
        embed.description = ""
        for input_name, results in results.items():
            embed.description += f"""
**{input_name}**:
{textwrap.indent('\n'.join(f'[{ex_url}](`{ex_name}`)' for ex_name, ex_url in results.items()))}

"""
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Pycord(bot))
