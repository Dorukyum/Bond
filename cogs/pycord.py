from inspect import cleandoc

import discord
from discord.ext.commands import Context, command, has_permissions

from utils import Cog, pycord_only

import re

PASTEBIN_RE = re.compile(r"(http(?:s?)://pastebin.com)(?:/)(\w+?)(?!/\w+)\W")

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

    @discord.slash_command(guild_ids=[881207955029110855])
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
            self.staff_list_channel = self.staff_list_channel or self.bot.get_channel(
                884730803588829206
            )
            await self.staff_list_channel.purge(limit=1)
            self.staff_list = await self.staff_list_channel.send(embed=embed)
        await ctx.send("Done!")

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild == self.bot.pycord:
            messages = []
            matches = re.findall(PASTEBIN_RE, message.content)
            for match in matches:
                base_url = match[0]
                paste_id = match[1]
                messages.append(f"{base_url}/raw/{paste_id}")
            if messages:
                await message.channel.send("\n".join(messages))


def setup(bot):
    bot.add_cog(Pycord(bot))
