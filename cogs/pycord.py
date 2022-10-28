import re
from inspect import cleandoc

import discord

from core import Cog, Context

PASTEBIN_RE = re.compile(r"(https?://pastebin.com)/([a-zA-Z0-9]{8})")


async def getattrs(ctx):
    input = ctx.options["thing"]
    thing = discord
    path = "discord"
    for attr in input.split("."):
        try:
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

    async def update_example_cache(self):
        """Updates the cached example list with the latest contents from the repo."""
        file_url = "https://api.github.com/repos/Pycord-Development/pycord/git/trees/master?recursive=1"
        async with self.bot.http_session.get(
            file_url, raise_for_status=True
        ) as response:
            self.bot.cache["example_list"] = examples = await response.json()
            return examples

    async def get_example_list(self, ctx: discord.AutocompleteContext):
        """Gets the latest list of example files found in the Pycord repository."""
        if not (examples := self.bot.cache.get("example_list")):
            examples = await self.update_example_cache()
        return [
            file["path"].partition("examples/")[2]
            for file in examples["tree"]
            if "examples" in file["path"]
            and file["path"].endswith(".py")
            and ctx.value in file["path"]
        ]

    @discord.slash_command(guild_ids=[881207955029110855])
    @discord.option(
        "name",
        description="The name of example to search for",
        autocomplete=get_example_list,
    )
    async def example(self, ctx, name: str):
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

    @discord.slash_command(guild_ids=[881207955029110855])
    async def close(self, ctx: Context, lock: bool = False):
        """Allows a staff member or the owner of the thread to close the thread"""

        if not isinstance(ctx.channel, discord.Thread):
            return await ctx.respond(
                "This command can only be used in threads.", ephemeral=True
            )

        if ctx.channel.permissions_for(ctx.author).manage_threads:
            if lock:
                embed = discord.Embed(
                    description="This thread was archived and locked by a staff member.",
                    color=0xFF0000,
                )
            else:
                embed = discord.Embed(
                    description="This thread was archived by a staff member.",
                    color=0xFFFF00,
                )
            await ctx.respond(embed=embed)
            await ctx.channel.archive(locked=lock)
        elif ctx.author.id == ctx.channel.owner_id:
            embed = discord.Embed(
                description="This thread was archived by the user that opened it.",
                color=0xFFFF00,
            )
            await ctx.respond(embed=embed)
            await ctx.channel.archive()
        else:
            await ctx.respond(
                "This command can only be used by the owner of the thread or a staff member.",
                ephemeral=True,
            )

    @discord.slash_command(guild_ids=[881207955029110855])
    @discord.default_permissions(manage_guild=True)
    async def update_staff_list(self, ctx: Context):
        staff_roles = [
            881247351937855549,  # Project Lead
            929080208148017242,  # Project Advisor
            881223820059504691,  # Core Developer
            881411529415729173,  # Server Manager
            881407111211384902,  # Moderator
            882105157536591932,  # Trainee Moderator
            881519419375910932,  # Helper
        ]
        embed = discord.Embed(title="**Staff List**", color=0x2F3136)
        embed.description = ""
        for role in staff_roles:
            role = ctx.guild.get_role(role)
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
        await ctx.respond("Done!")

    @discord.slash_command(guild_ids=[881207955029110855])
    @discord.option(
        "role",
        description="The role that will be added to or removed from you.",
        choices=[
            discord.OptionChoice("Events", "915701572003049482"),
        ],
    )
    async def role(self, ctx: Context, role: str):
        """Choose a role to claim or get rid of."""
        if int(role) in ctx.author._roles:
            await ctx.author.remove_roles(discord.Object(role))
            return await ctx.respond(f"The <@&{role}> role has been removed from you.")
        await ctx.author.add_roles(discord.Object(role))
        await ctx.respond(f"You have received the <@&{role}> role.")

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is not None and message.guild.id == 881207955029110855:
            messages = []
            matches = re.findall(PASTEBIN_RE, message.content)
            for match in matches:
                base_url, paste_id = match
                messages.append(f"{base_url}/raw/{paste_id}")
            if messages:
                await message.channel.send("\n".join(messages))


def setup(bot):
    bot.add_cog(Pycord(bot))
