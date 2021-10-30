from contextlib import suppress
from re import compile as re_compile

import discord
from discord.ext import commands

from utils import Cog, s


class Events(Cog):
    def __init__(self, bot):
        super().__init__(bot)
        self.general = bot.main_guild.get_channel(881224361015672863)

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # AFK
        if message.author.id in self.bot.cache["afk"].keys():
            del self.bot.cache["afk"][message.author.id]
            await message.channel.send(
                f"Welcome back {message.author.display_name}! You're no longer AFK.",
                delete_after=4.0,
            )
            with suppress(discord.Forbidden):
                await message.author.edit(nick=message.author.display_name[6:])
        for mention in message.mentions:
            if msg := self.bot.cache["afk"].get(mention.id):
                await message.channel.send(f"{mention.display_name} is AFK: {msg}")

        # Pull requests and issues
        links = [
            f"<https://github.com/Pycord-Development/pycord/issues/{text[2:]}>"
            for text in message.content.split()
            if text.startswith("##") and len(text) > 2 and text[2:].isdigit()
        ][:3]
        if links:
            await message.reply("\n".join(links))

    @Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, commands.CommandInvokeError):
            raise error
        await ctx.send(
            embed=discord.Embed(
                title=" ".join(
                    re_compile(r"[A-Z][a-z]*").findall(error.__class__.__name__)
                ),
                description=str(error),
                color=discord.Color.red(),
            )
        )

    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.general.send(
            f"**{member}** ({member.mention}) joined the server :wave:"
        )


def setup(bot):
    bot.add_cog(Events(bot))
