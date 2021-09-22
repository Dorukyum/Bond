from contextlib import suppress
from urllib import parse

import discord
from discord.ext.commands import Context, command

from utils import Cog


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
            await ctx.send("Invalid style. Valid styles are `f|F|d|D|t|T|R`.")
        else:
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
    async def suggest(self, ctx: Context, *, text):
        """Suggest something related to library design."""
        if self.suggestions_channel.permissions_for(ctx.author).send_messages:
            await self.suggestions_channel.send(
                embed=discord.Embed(
                    description=text,
                    colour=discord.Color.blurple(),
                )
                .set_author(
                    name=str(ctx.author), icon_url=ctx.author.display_avatar.url
                )
                .set_footer(text=f"ID: {ctx.author.id}")
            )
            await ctx.message.delete()

    @command()
    async def afk(self, ctx: Context, *, message="_No reason specified._"):
        """Become AFK."""
        await ctx.send(f"Set your AFK: {message}")
        self.bot.cache["afk"][ctx.author.id] = message
        with suppress(discord.Forbidden):
            await ctx.author.edit(nick=f"[AFK] {ctx.author.display_name}")


def setup(bot):
    bot.add_cog(General(bot))
