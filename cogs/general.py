from contextlib import suppress
from io import BytesIO
from re import compile
from typing import Optional
from urllib import parse

import discord

from core import Cog, Context, GuildModel, humanize_time

PULL_HASH_REGEX = compile(
    r"(?:(?P<org>(?:[A-Za-z]|\d|-)+)/)?(?P<repo>(?:[A-Za-z]|\d|-)+)?(?:##)(?P<index>[0-9]+)"
)


class General(Cog):
    """General commands."""

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
    async def userinfo(self, ctx: Context, user: Optional[discord.User]):
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
    @discord.guild_only()
    @discord.option("suggestion", description="The suggestion.")
    async def suggest(self, ctx: Context, *, suggestion: str):
        """Make a suggestion for the server. This will be sent to the channel set by the server managers."""
        await ctx.assert_permissions(external_emojis=True)
        if not (channel := await GuildModel.get_text_channel(ctx.guild, "suggestions")):
            return await ctx.respond("This server doesn't have a suggestions channel.")

        msg = await channel.send(
            embed=discord.Embed(
                description=suggestion,
                colour=discord.Color.blurple(),
            )
            .set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
            .set_footer(text=f"ID: {ctx.author.id}")
        )
        await msg.add_reaction("<:upvote:881521766231584848>")
        await msg.add_reaction("<:downvote:904068725475508274>")
        await ctx.respond(
            f"Your suggestion has been sent to {channel.mention}.", ephemeral=True
        )

    suggestions = discord.SlashCommandGroup(
        "suggestions",
        "Commands related to member suggestions.",
        guild_only=True,
        default_member_permissions=discord.Permissions(manage_guild=True),
    )

    @suggestions.command(name="set")
    @discord.option(
        "channel",
        description="The channel new member suggestions will be sent to.",
    )
    async def suggestions_set(
        self, ctx: Context, channel: discord.TextChannel
    ):
        """Set the channel for member suggestions."""
        await GuildModel.update_or_create(
            id=ctx.guild_id, defaults={"suggestions": channel.id}
        )
        await ctx.respond(f"Member suggestions will now be sent to {channel.mention}.")

    @suggestions.command(name="disable")
    async def suggestions_disable(self, ctx: Context):
        """Disable member suggestions."""
        if (
            guild := await GuildModel.filter(id=ctx.guild_id)
            .exclude(suggestions=0)
            .first()
        ):
            await guild.update_from_dict({"suggestions": 0}).save()
            return await ctx.respond(
                "Member suggestions have been disabled for this server."
            )
        await ctx.respond("Member suggestions are already disabled for this server.")

    @discord.slash_command()
    async def ping(self, ctx: Context):
        """View the websocket latency of the bot."""
        await ctx.respond(f"Pong! `{self.bot.latency*1000:.2f}ms`")

    @discord.slash_command()
    @discord.option(
        "style",
        str,
        description="The style of the formatted timestamp.",
        choices=["f", "F", "d", "D", "t", "T", "R"],
        default=None,
    )
    async def timestamp(self, ctx: Context, style: Optional[str]):
        """View the current timestamp."""
        time = discord.utils.utcnow()
        await ctx.respond(
            embed=discord.Embed(
                title="Timestamp",
                description=(
                    f"{discord.utils.format_dt(time, style=style)}\n\n"
                    f"`{round(time.timestamp())}`"
                ),
                color=0x0060FF,
                timestamp=time,
            )
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

    emoji = discord.SlashCommandGroup(
        "emoji",
        "Commands related to emojis.",
        guild_only=True,
        default_member_permissions=discord.Permissions(manage_guild=True),
    )

    @emoji.command(name="add")
    @discord.option("name", description="The name of the emoji.")
    @discord.option("url", description="The image url of the emoji.")
    async def emoji_add(self, ctx: Context, name: str, url: str):
        """Add a custom emoji to this guild."""
        await ctx.assert_permissions(manage_emojis=True)
        async with self.bot.http_session.get(url) as res:
            if 300 > res.status >= 200:
                emoji = await ctx.guild.create_custom_emoji(
                    name=name, image=BytesIO(await res.read()).getvalue()
                )
                await ctx.respond(f"{emoji} Successfully created emoji.")
            else:
                await ctx.respond(
                    f"An HTTP error has occured while fetching the image: {res.status} {res.reason}"
                )

    @emoji.command(name="delete")
    @discord.option("name", description="The name of the emoji to delete.")
    @discord.option(
        "reason", str, description="The reason to delete the emoji.", default=None
    )
    async def emoji_delete(
        self, ctx: Context, name: str, reason: Optional[str]
    ):
        """Delete a custom emoji from this guild."""
        await ctx.assert_permissions(manage_emojis=True)
        for emoji in ctx.guild.emojis:
            if emoji.name == name:
                await emoji.delete(reason=reason)
                return await ctx.respond(f"Successfully deleted `:{name}:`.")
        await ctx.respond(f'No emoji named "{name}" found.')

    @discord.slash_command()
    @discord.option(
        "reason",
        description="The message to show when you're mentioned.",
        default="_No reason specified._",
    )
    @discord.option(
        "change_nick",
        description="If True, your nickname will be prefixed with [AFK].",
        default=True,
    )
    async def afk(self, ctx: Context, *, reason: str, change_nick: bool):
        """Become AFK."""
        await ctx.respond(f"Set your AFK: {reason}")
        self.bot.cache["afk"][ctx.author.id] = reason
        if change_nick and not ctx.author.display_name.startswith("[AFK] "):
            with suppress(discord.HTTPException):
                await ctx.author.edit(nick=f"[AFK] {ctx.author.display_name}")

    @Cog.listener()
    async def on_message(self, message):
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
        def make_link(index, org=None, repo=None):
            org = org or "Pycord-Development"
            repo = repo or "pycord"
            return f"https://github.com/{org}/{repo}/pull/{index}"

        links = list(
            set(
                make_link(index, org, repo)
                for org, repo, index in PULL_HASH_REGEX.findall(message.content)
            )
        )[:15]
        if len(links) > 2:
            links = [f"<{link}>" for link in links]
        if links:
            await message.reply("\n".join(links))

    @discord.user_command(name="View Account Age")
    async def account_age(self, ctx, member: discord.Member):
        """View the age of an account."""
        age = discord.utils.utcnow() - member.created_at
        await ctx.respond(
            f"{member.mention} is {humanize_time(age)} old.", ephemeral=True
        )


def setup(bot):
    bot.add_cog(General(bot))
