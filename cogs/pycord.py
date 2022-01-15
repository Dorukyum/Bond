from inspect import cleandoc
from utils import Cog, pycord_only

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
        self.staff_list_channel = bot.get_channel(884730803588829206)
        self.suggestions_channel = bot.get_channel(881735375947722753)

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

    @discord.slash_command()
    async def example(self, ctx, name: str = ""):
        """Get the link of an example from the Pycord repository."""

        if not name.endswith(".py"):
            name = f"{name}.py"
        if name.startswith("slash_"):
            name = f"app_commands/{name}"
        file_name = name.split("/")[-1]
        example_name = " ".join(file_name.split("_")).split(".")[0]
        await ctx.respond(
            f"Here's the {example_name} example.",
            view=discord.ui.View(
                discord.ui.Button(
                    label=file_name,
                    url=f"https://github.com/Pycord-Development/pycord/tree/master/examples/{name}",
                )
            ),
        )

    @command()
    @pycord_only
    @guild_only()
    async def suggest(self, ctx: Context, *, text):
        """Suggest something related to library design.
        This will be posted to <#881735375947722753>."""
        await ctx.message.delete()
        msg = await self.suggestions_channel.send(
            embed=discord.Embed(
                description=text,
                colour=discord.Color.blurple(),
            )
            .set_author(
                name=str(ctx.author), icon_url=ctx.author.display_avatar.url
            )
            .set_footer(text=f"ID: {ctx.author.id}")
        )
        await msg.add_reaction("<:upvote:881521766231584848>")
        await msg.add_reaction("<:downvote:904068725475508274>")

    @command()
    @pycord_only
    @has_permissions(manage_guild=True)
    async def update_staff_list(self, ctx: Context):
        staff_roles = [
            929080208148017242,  # PA
            881223820059504691,  # Core Developer
            881411529415729173,  # Server Manager
            881407111211384902,  # Moderator
            882105157536591932,  # Trainee Moderator
            881519419375910932,  # Helper
        ]
        embed = discord.Embed(title="**Staff List**", color=0x2F3136)
        embed.description = ""
        for role in staff_roles:
            role = self.bot.pycord.get_role(role)
            embed.description += f"{role.mention} | **{len(role.members)}** \n"

            for member in role.members:
                embed.description += f"> `{member.id}` {member.mention}\n"
            embed.description += "\n"

        if self.staff_list is not None:
            await self.staff_list.edit(embed=embed)
        else:
            await self.staff_list_channel.purge(limit=1)
            self.staff_list = await self.staff_list_channel.send(embed=embed)
        await ctx.send("Done!")


def setup(bot):
    bot.add_cog(Pycord(bot))
