from re import findall

import discord
from discord.ext.commands import Context, command, group

from utils import Cog


class Fun(Cog):
    """A cog for fun commands."""

    @command()
    async def how_many(self, ctx: Context, *, text):
        """Shows the amount of people that has the supplied text in their display name."""
        text = text.strip().lower()
        if text == "asked":
            return await ctx.send("Nobody.")
        count = sum(text in member.display_name.lower() for member in ctx.guild.members)
        await ctx.send(
            f"{count} people have `{text}` (any case) in their display name."
        )

    @group(invoke_without_command=True)
    async def poll(self, ctx: Context, question: str, *choices: str):
        """Create a poll."""
        def to_emoji(c):
            base = 0x1F1E6
            return chr(base + c)
        choices = [(to_emoji(e), v) for e, v in enumerate(choices[:28])]
        body = "\n".join(f"{key}: {c}" for key, c in choices)

        message = await ctx.send(
            embed=discord.Embed(
                title=f"Poll | {question}",
                description=f"{body}",
                color=discord.Color.brand_red(),
            ).set_author(
                name=ctx.author.display_name, icon_url=ctx.author.display_avatar
            )
        )
        for reaction in choices:
            await message.add_reaction(reaction)

    @poll.command()
    async def yesno(self, ctx: Context, *, question):
        """Create a poll with the options being yes or no."""
        message = await ctx.send(
            embed=discord.Embed(
                title="Yes/No Poll",
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
