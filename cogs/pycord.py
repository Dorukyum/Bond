from inspect import cleandoc
from utils import Cog

import discord


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


class DiscordAttribute:
    async def convert(self, path):
        thing = discord
        for attr in path.split("."):
            if attr == "discord":
                continue
            try:
                thing = getattr(thing, attr)
            except AttributeError:
                return
        return thing


class Pycord(Cog):
    """A cog for Pycord-related commands."""

    @discord.slash_command(name="doc")
    @discord.option("thing", autocomplete=getattrs)
    async def _get_doc(self, ctx, thing: DiscordAttribute):
        """View the docstring of an attribute of the discord module."""
        if not thing:
            return await ctx.respond("Item not found.")
        if thing.__doc__ is None:
            return await ctx.respond(f"Couldn't find documentation for `{thing}`.")

        await ctx.respond(f"```\n{cleandoc(thing.__doc__)}```")


def setup(bot):
    bot.add_cog(Pycord(bot))
