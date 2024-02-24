from urllib import parse

from asyncio import sleep
from random import choice

import discord
from discord.utils import TimestampStyle, format_dt, utcnow

from core import Cog, Context


class Miscellaneous(Cog):
    """Miscellaneous commands."""

    @discord.slash_command()
    @discord.guild_only()
    async def serverinfo(self, ctx: Context):
        """View information/statistics about the server."""
        guild = ctx.guild
        assert guild
        creation = ((guild.id >> 22) + 1420070400000) // 1000
        boost_emoji = (
            "<:shiny_boost:1007971330332839996>"
            if guild.premium_subscription_count > 0
            else "<:boost:1007970712977420338>"
        )

        embed = (
            discord.Embed(
                title=guild.name,
                description=f"**ID:** {guild.id}\n\n**Features:**\n"
                + "\n".join(f"- {f.replace('_', ' ').title()}" for f in guild.features),
                color=0x0060FF,
            )
            .add_field(
                name="Members",
                value=f"Total: {guild.member_count}\nBots: {sum(m.bot for m in guild.members)}",
            )
            .add_field(
                name="Time of Creation",
                value=f"<t:{creation}>\n<t:{creation}:R>",
            )
            .add_field(
                name="Channels",
                value=f"Text: {len(guild.text_channels)}\nVoice: {len(guild.voice_channels)}"
                f"\nCategories: {len(guild.categories)}",
            )
            .add_field(
                name="Roles",
                value=f"{len(guild._roles)} roles\nHighest:\n{guild.roles[-1].mention}",
            )
            .add_field(
                name="Boost Status",
                value=f"Level {guild.premium_tier}\n"
                f"{boost_emoji}{guild.premium_subscription_count} boosts",
            )
            .set_footer(
                text=f"Requested by {ctx.author}",
                icon_url=ctx.author.display_avatar.url,
            )
        )
        if owner := guild.owner:
            embed.insert_field_at(0, name="Owner", value=f"{owner}\n{owner.mention}")
        if icon := guild.icon:
            embed.set_thumbnail(url=icon.url)
        await ctx.respond(embed=embed)

    def permissions(self, target: discord.Member, include: int = 0) -> str:
        permissions = target.guild_permissions
        if permissions.administrator:
            return "- Administrator"
        return (
            "\n".join(
                f"- {k.replace('_', ' ').title()}"
                for k, v in target.guild_permissions
                if v and (not include or getattr(discord.Permissions(include), k))
            )
            or "_No permissions_"
        )

    @discord.slash_command()
    @discord.option(
        "user",
        discord.User,
        description="The user to view information about.",
        default=None,
    )
    async def userinfo(self, ctx: Context, user: discord.User | None):
        """View information about a user."""
        assert ctx.author
        target = user or ctx.author
        creation = ((target.id >> 22) + 1420070400000) // 1000
        embed = (
            discord.Embed(
                title="User Information",
                description=f"{target.mention}\n**ID:** {target.id}",
                color=0x0060FF,
            )
            .set_author(name=str(target), icon_url=target.display_avatar.url)
            .set_thumbnail(url=target.display_avatar.url)
            .add_field(
                name="Account Creation",
                value=f"<t:{creation}>\n<t:{creation}:R>",
            )
            .set_footer(
                text=f"Requested by {ctx.author}",
                icon_url=ctx.author.display_avatar.url,
            )
        )
        if isinstance(target, discord.Member):
            embed.fields = [
                discord.EmbedField(
                    name="<:moderator:1008380045573767268> Staff Permissions",
                    value=self.permissions(target, 27813093566),
                    inline=True,
                ),
                discord.EmbedField(
                    name="Member Permissions",
                    value=self.permissions(target, 655052817217),
                    inline=True,
                ),
                discord.EmbedField(
                    name=f"Roles ({len(target._roles)})",
                    value=", ".join(r.mention for r in target.roles[::-1][:-1])
                    or "_Member has no roles_",
                ),
                *embed.fields,
            ]
            joined = target.joined_at and int(target.joined_at.timestamp())
            embed.add_field(name="Joined", value=f"<t:{joined}>\n<t:{joined}:R>")
            if boost := target.premium_since:
                timestamp = int(boost.timestamp())
                embed.add_field(
                    name="Boosting Since", value=f"<t:{timestamp}>\n<t:{timestamp}:R>"
                )
            else:
                embed.add_field(name="Boosting Server?", value="No")
        await ctx.respond(embed=embed)

    @discord.slash_command()
    async def ping(self, ctx: Context):
        """View the websocket latency of the bot."""
        await ctx.info("Latency", f"I am running with a latency of `{self.bot.latency*1000:.2f}ms`.")

    @discord.slash_command()
    @discord.option(
        "style",
        str,
        description="The style of the formatted timestamp.",
        choices=["f", "F", "d", "D", "t", "T", "R"],
        default=None,
    )
    async def timestamp(self, ctx: Context, style: TimestampStyle):
        """View the current timestamp."""
        time = utcnow()
        formatted = format_dt(time, style=style)
        await ctx.info(
            "Timestamp",
            f"The current ISO timestamp is `{time.timestamp()}.\n" \
            f"Formatted: {formatted} (`{formatted}`)",
        )

    @discord.slash_command()
    @discord.option("query", description="The query to make.")
    async def search(self, ctx: Context, *, query: str):
        """Get a search url from Bing, DuckDuckGo and Google."""
        param = parse.urlencode({"q": query})
        await ctx.respond(
            f"Use the buttons below to search for `{query}` on the internet.",
            view=discord.ui.View(
                discord.ui.Button(
                    label="Google", url=f"https://www.google.com/search?{param}"
                ),
                discord.ui.Button(
                    label="Bing", url=f"https://www.bing.com/search?{param}"
                ),
                discord.ui.Button(
                    label="DuckDuckGo", url=f"https://www.duckduckgo.com/?{param}"
                ),
            ),
        )

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
        """Shows the amount of members that have the provided text in their display name."""
        assert ctx.guild
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
        choice3: str | None,
        choice4: str | None,
        choice5: str | None,
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
            ).original_message()  # type: ignore
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
        message = await interaction.original_message()  # type: ignore
        await message.add_reaction("✅")
        await sleep(1)
        await message.add_reaction("❎")

def setup(bot):
    bot.add_cog(Miscellaneous(bot))
