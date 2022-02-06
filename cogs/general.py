from inspect import getsource, getsourcefile
from io import StringIO
from contextlib import suppress
from urllib import parse
import re
import datetime

import discord
from discord.ext.commands import Context, command

from utils import Cog

PULL_HASH_REGEX = re.compile(r'##(?P<index>[0-9]+)')
GITHUB_URL_REGEX = re.compile(r'http(s)?://(www\.)?github\.com/Pycord-Development/pycord/pull/(?P<index>[0-9]+)')

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
        """Get a search url from DuckDuckGo and Google."""
        param = parse.urlencode({"q": query})
        await ctx.send(
            f"Use the buttons below to search for `{query}` on the internet.",
            view=discord.ui.View(
                discord.ui.Button(
                    label="Google", url=f"https://www.google.com/search?{param}"
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
    async def on_message(self, message: discord.Message):
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
        links = [f'https://github.com/Pycord-Development/pycord/pull/{index}' for index in PULL_HASH_REGEX.findall(message.content)]
        if links:
            await message.reply("\n".join(links))

    @Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        github_url_format = "https://github.com/Pycord-Development/pycord/pull/{index}"
        if before.author.bot:
            return
        before_pull_indexes = PULL_HASH_REGEX.findall(before.content)
        after_pull_indexes = PULL_HASH_REGEX.findall(after.content)
        if not before_pull_indexes;
            # it is a normal message
            return
        if after_pull_indexes == before_pull_indexes:
            # pull indexes have not been changed yet
            return
        first_replacement, second_replacement = list(i for i in before_pull_indexes if i not in after_pull_indexes), list(i for i in after_pull_indexes if i not in before_pull_indexes)
        created_at = before.created_at
        past_time = created_at - datetime.timedelta(minutes=60)
        async for message in before.channel.history(limit=100, before=created_at, after=past_time):
            if message.author.id != self.bot.user.id:
                continue
            content = message.content
            all_links = GITHUB_URL_REGEX.findall(content)
            if not all_links:
                # normal message by our bot
                continue
            for link in all_links:
                index = int(GITHUB_URL_REGEX.match(link).group('index'))
                if index in first_replacement:
                    all_links[all_links.index(link)] = github_url_format.format(second_replacement[first_replacement.index(index)])
            splitted = content.split()
            for sentence in splitted;
                for old_link in first_replacement:
                    old_link = github_url_format.format(old_link)
                    new_sentence = sentence.replace(old_link, all_links[first_replacement.index(old_link)])
                    splitted[splitted.index(sentence)] = new_sentence
            await message.edit(content=''.join(splitted))
            return

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


def setup(bot):
    bot.add_cog(General(bot))
