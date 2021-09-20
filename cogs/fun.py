from re import findall
import random

import discord
from discord.ext.commands import Context, command, group

from utils import Cog


class Fun(Cog):
    """A cog for fun commands"""

    @group(invoke_without_command=True)
    async def how_many(self, ctx: Context, *, text):
        """Shows the amount of people that has the supplied text in their display name."""
        text = text.strip().lower()
        if text == "asked":
            await ctx.send("Nobody.")
        else:
            await ctx.send(
                f"{len(tuple(x for x in ctx.guild.members if text in x.display_name))} people have `{text}` (any case) in their display name."
            )

    @how_many.command()
    async def regex(self, ctx: Context, *, regex):
        """Shows the amount of people that has the supplied regex in their display name."""
        await ctx.send(
            f"{len(tuple(x for x in ctx.guild.members if findall(regex, x.display_name)))} people have `{regex}` in their display name."
        )

    @group(invoke_without_command=True)
    async def poll(self, ctx: Context, question, choice1, choice2):
        """Create a poll."""
        message = await ctx.send(
            embed=discord.Embed(
                title=f"Poll | {question}",
                description=f":a: {choice1}\n:b: {choice2}",
                color=discord.Color.brand_red(),
            ).set_author(
                name=ctx.author.display_name, icon_url=ctx.author.display_avatar
            )
        )
        await message.add_reaction("🅰")
        await message.add_reaction("🅱")

    @poll.command()
    async def yesno(self, ctx: Context, *, question):
        """Create a poll with the options being yes or no."""
        message = await ctx.send(
            embed=discord.Embed(
                title=f"Yes/No Poll",
                description=question,
                color=discord.Color.brand_green(),
            ).set_author(
                name=ctx.author.display_name, icon_url=ctx.author.display_avatar
            )
        )
        await message.add_reaction("✅")
        await message.add_reaction("❎")

    @bot.command(name="whosus", description="find out who's the sus person among us") 
    async def whosus(ctx):
        await ctx.message.reply(random.choice(ctx.guild.members).name + " is sus :flushed:")


def setup(bot):
    bot.add_cog(Fun(bot))
