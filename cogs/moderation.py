import discord
from discord.ext.commands import MemberConverter

from core import Cog, Context, s


class Moderation(Cog):
    """Commands related to moderation."""

    @discord.slash_command()
    @discord.guild_only()
    @discord.default_permissions(ban_members=True)
    @discord.option(
        "members",
        description="The mentions, usernames or IDs of members to ban, seperated with spaces.",
    )
    @discord.option(
        "reason",
        description="The reason for banning these members.",
        default="No reason provided",
    )
    async def massban(
        self,
        ctx: Context,
        members: str,
        *,
        reason: str,
    ):
        """Ban the supplied members from the guild. Limited to 10 at a time."""
        await ctx.assert_permissions(ban_members=True)
        converter = MemberConverter()
        converted_members = [
            await converter.convert(ctx, member) for member in members.split()
        ]
        if (count := len(converted_members)) > 10:
            return await ctx.respond("You can only ban 10 members at a time.")

        for member in converted_members:
            await ctx.guild.ban(
                member, reason=f"{ctx.author} ({ctx.author.id}): {reason}"
            )
        await ctx.respond(f"Banned **{count}** member{s(converted_members)}.")

    @discord.slash_command()
    @discord.guild_only()
    @discord.default_permissions(manage_messages=True)
    @discord.option(
        "seconds",
        description="The slowmode cooldown in seconds, 0 to disable slowmode.",
    )
    async def slowmode(self, ctx: Context, seconds: int):
        """Set slowmode for the current channel."""
        await ctx.assert_permissions(manage_channels=True)
        if not 21600 >= seconds >= 0:
            return await ctx.respond(
                "Slowmode should be between `21600` and `0` seconds."
            )
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.respond(
            f"The slowmode cooldown is now `{seconds}` second{s(seconds)}."
            if seconds > 0
            else "Slowmode is now disabled."
        )

    @discord.slash_command()
    @discord.guild_only()
    @discord.default_permissions(ban_members=True)
    @discord.option(
        "reason",
        description="The reason for locking this channel.",
        default="No reason provided",
    )
    async def lock(self, ctx: Context, *, reason: str):
        """Lock the current channel, disabling send messages permissions for the default role."""
        await ctx.assert_permissions(manage_roles=True)
        if not ctx.channel.permissions_for(ctx.guild.default_role).send_messages:
            return await ctx.respond("This channel is already locked.")
        await ctx.channel.set_permissions(
            ctx.guild.default_role,
            send_messages=False,
            reason=f"{ctx.author} ({ctx.author.id}): {reason}",
        )
        await ctx.respond("Locked this channel.")

    @discord.slash_command()
    @discord.guild_only()
    @discord.default_permissions(ban_members=True)
    @discord.option(
        "reason",
        description="The reason for unlocking this channel.",
        default="No reason provided",
    )
    async def unlock(self, ctx: Context, *, reason: str):
        """Unlock the current channel, enabling send messages permissions for the default role."""
        await ctx.assert_permissions(manage_roles=True)
        if ctx.channel.permissions_for(ctx.guild.default_role).send_messages:
            return await ctx.respond("This channel isn't locked.")
        await ctx.channel.set_permissions(
            ctx.guild.default_role,
            send_messages=True,
            reason=f"{ctx.author} ({ctx.author.id}): {reason}",
        )
        await ctx.respond("Unlocked this channel.")

    async def purge_channel(self, ctx: Context, **kwargs):
        await ctx.assert_permissions(read_message_history=True, manage_messages=True)
        if purge := getattr(ctx.channel, "purge", None):
            count = len(await purge(**kwargs))
            return await ctx.respond(f"Purged **{count}** messages.", ephemeral=True)
        await ctx.respond("This channel cannot be purged.", ephemeral=True)

    purge = discord.SlashCommandGroup(
        "purge",
        "Commands to purge messages.",
        guild_only=True,
        default_member_permissions=discord.Permissions(manage_messages=True),
    )

    @purge.command(name="all")
    @discord.option(
        "limit",
        description="The amount of messages to search.",
        min_value=1,
        max_value=100,
    )
    @discord.option(
        "reason",
        description="The reason for purging this channel.",
        default="No reason provided",
    )
    async def purge_all(
        self,
        ctx: Context,
        limit: int,
        *,
        reason: str,
    ):
        """Delete messages from this channel."""
        await self.purge_channel(ctx, limit=limit, reason=reason)

    @purge.command(name="member")
    @discord.option(
        "member",
        description="The member whose messages will be deleted.",
    )
    @discord.option(
        "limit",
        description="The amount of messages to search.",
        min_value=1,
        max_value=100,
    )
    @discord.option(
        "reason",
        description="The reason for purging this channel.",
        default="No reason provided",
    )
    async def purge_member(
        self,
        ctx: Context,
        member: discord.Member,
        limit: int,
        *,
        reason: str,
    ):
        """Purge a member's messages from this channel."""
        await self.purge_channel(
            ctx, check=lambda m: m.author.id == member.id, limit=limit, reason=reason
        )

    @purge.command(name="bots")
    @discord.option(
        "limit",
        description="The amount of messages to search.",
        min_value=1,
        max_value=100,
    )
    @discord.option(
        "reason",
        description="The reason for purging this channel.",
        default="No reason provided",
    )
    async def purge_bots(
        self,
        ctx: Context,
        limit: int,
        *,
        reason: str,
    ):
        """Purge bot messages from this channel."""
        await self.purge_channel(
            ctx, check=lambda m: m.author.bot, limit=limit, reason=reason
        )

    @purge.command(name="containing")
    @discord.option(
        "phrase",
        description="The phrase to delete messages containing it.",
    )
    @discord.option(
        "limit",
        description="The amount of messages to search.",
        min_value=1,
        max_value=100,
    )
    @discord.option(
        "reason",
        description="The reason for purging this channel.",
        default="No reason provided",
    )
    async def purge_containing(
        self,
        ctx: Context,
        phrase: str,
        limit: int,
        *,
        reason: str,
    ):
        """Purge messages containing a specific phrase from this channel."""
        await self.purge_channel(
            ctx, check=lambda m: phrase in m.content, limit=limit, reason=reason
        )


def setup(bot):
    bot.add_cog(Moderation(bot))
