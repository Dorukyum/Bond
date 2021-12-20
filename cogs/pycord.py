from inspect import cleandoc
from utils import Cog

import discord


async def getattrs(ctx):
    try:
        input = ctx.options["item"]
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

    @discord.slash_command(name="doc")
    @discord.option("item", autocomplete=getattrs)
    async def _get_doc(self, ctx, item):
        thing = discord
        for attr in item.split("."):
            if attr == "discord":
                continue

            try:
                thing = getattr(thing, attr)
            except AttributeError:
                return await ctx.respond("Item not found.")

        if thing.__doc__ is None:
            return await ctx.respond(f"Couldn't find documentation for `{item}`.")
        await ctx.respond(f"```\n{cleandoc(thing.__doc__)}```")


def setup(bot):
    bot.add_cog(Pycord(bot))
