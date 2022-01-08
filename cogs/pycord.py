from inspect import cleandoc
from utils import Cog

import discord

class ExamplesSlashCommand(disoord.SlashCommand):
    def __init__(self, bot, *args, **kwargs):
        examples = bot.pycord_examples
        async def callback(ctx, name: discord.Option(str, 'Name of the example.', choices=list(examples.keys()):
            # do /example command here
            await ctx.send(
                f"Here's the {name} example.",
                view = discord.ui.View(
                    discord.ui.Button(
                        label = name,
                        url = examples[name],
                    )
                )
            )
        super().__init__(callback, *args, **kwargs)

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

    @discord.slash_command(name="doc")
    @discord.option("thing", autocomplete=getattrs)
    async def _get_doc(self, ctx, thing):
        """View the docstring of an attribute of the discord module."""
        thing, path = await self.convert_attr(thing)
        if not thing:
            return await ctx.respond("Item not found.")
        if thing.__doc__ is None:
            return await ctx.respond(f"Couldn't find documentation for `{path}`.")

        await ctx.respond(f"```\n{cleandoc(thing.__doc__)[:1993]}```")

    @discord.application_command(cls=ExamplesSlashCommand, name='example')
    async def _example():
        pass

def setup(bot):
    bot.add_cog(Pycord(bot))
