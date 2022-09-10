from asyncio import sleep
from random import choice
from typing import Optional

import discord

from core import Cog, Context


class Fun(Cog):
    """Fun commands."""

    magic_8ball = discord.SlashCommandGroup(
        "8ball", "Commands to ask a question to the magic 8 ball."
    )

    @magic_8ball.command(name="ask")
    @discord.option(
        "question",
        description="The question to ask to the magic 8 ball.",
    )
    async def magic_8ball_ask(self, ctx: Context, question: str):
        """Ask a yes-or-no question to the magic 8 ball and get an answer."""
        await ctx.defer()
        answer = choice(
            (
                "Definitely.",
                "Most probably.",
                "I'm not sure.",
                "Perhaps.",
                "I don't think so.",
                "There's a chance!",
                "Under no circumstances.",
            )
        )
        await sleep(2)
        await ctx.respond(f"> {question}\n{answer}")

    @magic_8ball.command(name="yes_or_no")
    @discord.option(
        "question",
        description="The question to ask to the magic 8 ball.",
    )
    async def magic_8ball_yes_or_no(self, ctx: Context, question: str):
        """Ask a yes-or-no question to the magic 8 ball and get an answer (either yes or no)."""
        await ctx.defer()
        answer = choice(("Yes.", "No."))
        await sleep(2)
        await ctx.respond(f"> {question}\n{answer}")

    @discord.slash_command()
    @discord.guild_only()
    @discord.option("text", description="The text to check for in display names.")
    async def how_many(self, ctx: Context, *, text: str):
        """Shows the amount of members that have the supplied text in their display name."""
        text = text.strip().lower()
        count = sum(text in member.display_name.lower() for member in ctx.guild.members)
        await ctx.respond(
            f"{count} members have `{text}` (any case) in their display name."
        )

    @discord.slash_command()
    @discord.option("question", description="The question of the poll.")
    @discord.option("choice1", description="The first choice.")
    @discord.option("choice2", description="The second choice.")
    @discord.option("choice3", str, description="The third choice.", default=None)
    @discord.option("choice4", str, description="The fourth choice.", default=None)
    @discord.option("choice5", str, description="The fifth choice.", default=None)
    async def poll(
        self,
        ctx: Context,
        question: str,
        choice1: str,
        choice2: str,
        choice3: Optional[str],
        choice4: Optional[str],
        choice5: Optional[str],
    ):
        """Create a poll with upto 5 choices."""
        choices = [
            (emoji, choice)
            for emoji, choice in zip(
                ("🇦", "🇧", "🇨", "🇩", "🇪"),
                (choice1, choice2, choice3, choice4, choice5),
            )
            if choice is not None
        ]

        message = await (
            await ctx.respond(
                embed=discord.Embed(
                    title=f"Poll: {question}",
                    description="\n".join(
                        f"{emoji} {choice}" for emoji, choice in choices
                    ),
                    color=0x0060FF,
                ).set_author(
                    name=ctx.author.display_name, icon_url=ctx.author.display_avatar
                )
            )
        ).original_message()
        for emoji, _ in choices:
            await message.add_reaction(emoji)
            await sleep(1)

    @discord.slash_command()
    @discord.option("question", description="The question of the poll.")
    async def poll_yesno(self, ctx: Context, *, question: str):
        """Create a poll with the options being yes or no."""
        interaction = await ctx.respond(
            embed=discord.Embed(
                title="Yes/No Poll",
                description=question,
                color=discord.Color.brand_green(),
            ).set_author(
                name=ctx.author.display_name, icon_url=ctx.author.display_avatar
            )
        )
        message = await interaction.original_message()
        await message.add_reaction("✅")
        await sleep(1)
        await message.add_reaction("❎")


def setup(bot):
    bot.add_cog(Fun(bot))
