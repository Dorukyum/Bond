from contextlib import suppress

import discord
from discord.ext import commands

from utils import Cog


class Events(Cog):
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
            f"https://github.com/Pycord-Development/pycord/pull/{text[2:]}"
            for text in message.content.split()
            if text.startswith("##") and len(text) > 2 and text[2:].isdigit()
        ][:3]
        if links:
            await message.reply("\n".join(links))

    @Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.content != after.content:
            await self.bot.process_commands(after)

    @Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, commands.CommandInvokeError):
            raise error
        await ctx.send(
            embed=discord.Embed(
                title=error.__class__.__name__,
                description=str(error),
                color=discord.Color.red(),
            )
        )


def setup(bot):
    bot.add_cog(Events(bot))
