from contextlib import suppress

from discord import Forbidden, Message
from discord.ext.commands import Context, command
from discord.utils import format_dt
from urllib import parse

from utils import Cog


class General(Cog):
    """A cog for general commands."""

    def __init__(self, bot) -> None:
        super().__init__(bot)
        self.afk_cache = bot.cache["afk"]

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
            await ctx.send(f"{format_dt(time, style=style)} (`{time.timestamp()}`)")

    @command()
    async def search(self, ctx: Context, *, query):
        """Get a search url from DuckDuckGo and Google.
        NOTE: limited to 100 characters."""
        query = parse.urlencode({"q": query[:100]})
        await ctx.reply(
            f"DuckDuckGo: <https://www.duckduckgo.com/?{query}>\nGoogle: <https://www.google.com/search?{query}>"
        )

    @command()
    async def afk(self, ctx: Context, *, message="_No reason specified._"):
        """Become AFK."""
        await ctx.send(f"Set your AFK: {message}")
        self.afk_cache[ctx.author.id] = message
        with suppress(Forbidden):
            await ctx.author.edit(nick=f"[AFK] {ctx.author.display_name}")

    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot:
            return

        if message.author.id in self.afk_cache.keys():
            del self.afk_cache[message.author.id]
            await message.channel.send(
                f"Welcome back {message.author.display_name}! You're no longer AFK.",
                delete_after=4.0,
            )
            with suppress(Forbidden):
                await message.author.edit(nick=message.author.display_name[6:])
        for mention in message.mentions:
            if msg := self.afk_cache.get(mention.id):
                await message.channel.send(f"{mention.display_name} is AFK: {msg}")


def setup(bot):
    bot.add_cog(General(bot))
