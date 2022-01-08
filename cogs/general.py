from inspect import getsource, getsourcefile
from io import StringIO
from contextlib import suppress
from urllib import parse

import discord
from discord.ext.commands import Context, command, guild_only

from utils import Cog, pycord_only


class General(Cog):
    """A cog for general commands."""

    def __init__(self, bot) -> None:
        super().__init__(bot)
        self.suggestions_channel = bot.get_channel(881735375947722753)

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
        """Get a search url from DuckDuckGo and Google.
        NOTE: limited to 100 characters."""
        query = parse.urlencode({"q": query[:100]})
        await ctx.reply(
            f"DuckDuckGo: <https://www.duckduckgo.com/?{query}>\nGoogle: <https://www.google.com/search?{query}>"
        )

    @command()
    @pycord_only
    @guild_only()
    async def suggest(self, ctx: Context, *, text):
        """Suggest something related to library design."""
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
    async def afk(self, ctx: Context, *, message="_No reason specified._"):
        """Become AFK."""
        await ctx.send(f"Set your AFK: {message}")
        self.bot.cache["afk"][ctx.author.id] = message
        with suppress(discord.Forbidden):
            await ctx.author.edit(nick=f"[AFK] {ctx.author.display_name}")

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # AFK
        if message.author.id in self.bot.cache["afk"].keys():
            del self.bot.cache["afk"][message.author.id]
            await message.add_reaction("\U0001f44b")
            with suppress(discord.Forbidden):
                await message.author.edit(nick=message.author.display_name[6:])
        for mention in message.mentions:
            if msg := self.bot.cache["afk"].get(mention.id):
                await message.channel.send(f"{mention.display_name} is AFK: {msg}")

        # Pull requests and issues
        links = [
            f"https://github.com/Pycord-Development/pycord/pull/{text[2:]}"
            for text in message.content.split()
            if text.startswith("##") and len(text) > 2 and text[2:].isdigit()
        ][:3]
        if links:
            await message.reply("\n".join(links))

    @command(aliases=["src"])
    async def source(self, ctx: Context, *, command: str = None):
        """See the source code of the bot."""
        if not command:
            return await ctx.send("https://github.com/Dorukyum/Pycord-Manager")
        c = self.bot.get_command(command)
        if not c:
            return await ctx.send(f"Command {command} was not found")
        callback = (
            self.bot.help_command.__class__ if command == "help" else c.callback
        )
        src = getsource(callback)
        buf = StringIO(src)
        file = discord.File(buf, getsourcefile(callback))
        await ctx.send(file=file)


def setup(bot):
    bot.add_cog(General(bot))
