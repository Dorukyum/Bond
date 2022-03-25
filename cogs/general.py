from contextlib import suppress
from inspect import getsource, getsourcefile
from io import StringIO
from typing import Optional
from urllib import parse
from re import compile

import discord
from discord.ext.commands import Context, command, guild_only, has_permissions

from utils import Cog, GuildModel, humanize_time

PULL_HASH_REGEX = compile(r'(?:(?P<org>(?:[A-Za-z]|\d|-)+)/)?(?P<repo>(?:[A-Za-z]|\d|-)+)?(?:##)(?P<index>[0-9]+)')

class General(Cog):
    """A cog for general commands."""

    async def suggestions_channel(
        self, guild: discord.Guild
    ) -> Optional[discord.TextChannel]:
        guild_data, _ = await GuildModel.get_or_create(id=guild.id)
        if guild_data.suggestions:
            return guild.get_channel(guild_data.suggestions)

    @command()
    @guild_only()
    async def suggest(self, ctx: Context, *, suggestion: str):
        """Make a suggestion for the server. This will be sent to the channel set by the server managers."""
        if not (channel := await self.suggestions_channel(ctx.guild)):
            return await ctx.send("This server doesn't have a suggestions channel.")

        await ctx.message.delete()
        msg = await channel.send(
            embed=discord.Embed(
                description=suggestion,
                colour=discord.Color.blurple(),
            )
            .set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
            .set_footer(text=f"ID: {ctx.author.id}")
        )
        await msg.add_reaction("<:upvote:881521766231584848>")
        await msg.add_reaction("<:downvote:904068725475508274>")

    @command()
    @has_permissions(manage_guild=True)
    @guild_only()
    async def suggestions(self, ctx: Context, channel_id: int):
        """Set the channel for suggestions. Use `0` as channel_id to disable suggestions.
        Members can use `p.suggest` to make a suggestion."""
        channel = ctx.guild.get_channel(channel_id)
        if channel_id != 0 and (
            channel is None or not isinstance(channel, discord.TextChannel)
        ):
            return await ctx.send(
                "A text channel in this guild with the given ID wasn't found."
            )
        guild, _ = await GuildModel.get_or_create(id=ctx.guild.id)
        await guild.update_from_dict({"suggestions": channel_id})
        await guild.save()
        if channel_id == 0:
            return await ctx.send("Suggestions been disabled for this server.")
        await ctx.send(
            f"The suggestions channel for this server is now {channel.mention}."
        )

    @command()
    async def ping(self, ctx: Context):
        """Get the websocket latency of the bot."""
        await ctx.send(f"Pong! `{self.bot.latency*1000:.2f}ms`")

    @command(aliases=["time"])
    async def timestamp(self, ctx: Context, style=None):
        """Get the current timestamp.
        Valid styles are `f|F|d|D|t|T|R`."""
        if style not in (None, "f", "F", "d", "D", "t", "T", "R"):
            return await ctx.send("Invalid style. Valid styles are `f|F|d|D|t|T|R`.")
        time = ctx.message.created_at
        await ctx.send(
            f"{discord.utils.format_dt(time, style=style)} (`{time.timestamp()}`)"
        )

    @command()
    async def search(self, ctx: Context, *, query):
        """Get a search url from Bing, DuckDuckGo and Google."""
        param = parse.urlencode({"q": query})
        await ctx.send(
            f"Use the buttons below to search for `{query}` on the internet.",
            view=discord.ui.View(
                discord.ui.Button(
                    label="Google", url=f"https://www.google.com/search?{param}"
                ),
                discord.ui.Button(
                    label="Bing", url=f"https://www.bing.com/search?{param}"
                ),
                discord.ui.Button(
                    label="DuckDuckGo", url=f"https://www.duckduckgo.com/?{param}"
                ),
            ),
        )

    @command()
    async def afk(self, ctx: Context, *, message="_No reason specified._"):
        """Become AFK."""
        await ctx.send(f"Set your AFK: {message}")
        self.bot.cache["afk"][ctx.author.id] = message
        if not ctx.author.display_name.startswith("[AFK] "):
            with suppress(discord.HTTPException):
                await ctx.author.edit(nick=f"[AFK] {ctx.author.display_name}")

    @Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # AFK
        if message.author.id in self.bot.cache["afk"].keys():
            del self.bot.cache["afk"][message.author.id]
            await message.add_reaction("\U0001f44b")
            if message.author.nick and message.author.nick.startswith("[AFK] "):
                with suppress(discord.HTTPException):
                    await message.author.edit(nick=message.author.nick[6:])
        for mention in message.mentions:
            if msg := self.bot.cache["afk"].get(mention.id):
                await message.channel.send(f"{mention.display_name} is AFK: {msg}")

        # Pull requests and issues
        def make_link(index, org=None, repo=None):
            org = org or "Pycord-Development"
            repo = repo or "pycord"
            return f"https://github.com/{org}/{repo}/pull/{index}"
        links = list(set([make_link(index, org, repo) for org, repo, index in PULL_HASH_REGEX.findall(message.content)]))[:15]
        if len(links) > 2:
            links = [f"<{link}>" for link in links]
        if links:
            await message.reply("\n".join(links))

    @command(aliases=["src"])
    async def source(self, ctx: Context, *, command: str = None):
        """See the source code of the bot."""
        if not command:
            return await ctx.send("https://github.com/Dorukyum/Pycord-Manager")
        c = self.bot.get_command(command) or self.bot.get_application_command(command)
        if not c:
            return await ctx.send(f"Command {command} was not found")
        callback = self.bot.help_command.__class__ if command == "help" else c.callback
        src = getsource(callback)
        buf = StringIO(src)
        file = discord.File(buf, getsourcefile(callback))
        await ctx.send(file=file)

    @discord.user_command(name="View Account Age")
    async def account_age(self, ctx, member: discord.Member):
        """View the age of an account."""
        age = discord.utils.utcnow() - member.created_at
        await ctx.respond(
            f"{member.mention} is {humanize_time(age)} old.", ephemeral=True
        )


def setup(bot):
    bot.add_cog(General(bot))
