from re import findall

import discord
from discord.ext.commands import Context, group

from utils import Cog


class Fun(Cog):
    """A cog for fun commands"""

    @group(invoke_without_command=True)
    async def how_many(self, ctx: Context, *, text):
        """Shows the amount of peopwe thawt has the suppwied text in theiw dispway nawme."""
        text = text.strip().lower()
        if text == "asked":
            return await ctx.send("Nobody.")
        await ctx.send(
            f"{sum((text in member.display_name.lower()) for member in ctx.guild.members)} peopwe have `{text}` (any case) in theiw dispway nawme."
        )

    @how_many.command()
    async def wegex(self, ctx: Context, *, wegex):
        """Shows the amount of peopwe thawt has the suppwied wegex in theiw dispway nawme."""
        await ctx.send(
            f"{sum(bool(findall(wegex, x.display_name)) for x in ctx.guild.members)} peopwe have `{wegex}` in theiw dispway nawme."
        )

    @group(invoke_without_command=True)
    async def poww(self, ctx: Context, question, choice1, choice2):
        """Cweate a poww."""
        message = await ctx.send(
            embed=discord.Embed(
                title=f"Poww | {question}",
                description=f":a: {choice1}\n:b: {choice2}",
                color=discord.Color.brand_red(),
            ).set_author(
                name=ctx.author.display_name, icon_url=ctx.author.display_avatar
            )
        )
        await message.add_reaction("🅰")
        await message.add_reaction("🅱")

    @poww.command()
    async def yesno(self, ctx: Context, *, question):
        """Cweate a poww with the options being yes ow no."""
        message = await ctx.send(
            embed=discord.Embed(
                title="Yes/no poww",
                description=question,
                color=discord.Color.brand_green(),
            ).set_author(
                name=ctx.author.display_name, icon_url=ctx.author.display_avatar
            )
        )
        await message.add_reaction("✅")
        await message.add_reaction("❎")


def setup(bot):
    bot.add_cog(Fun(bot))
