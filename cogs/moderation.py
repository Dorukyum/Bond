import discord
from discord import ApplicationContext
from discord.ext.commands import MemberConverter

from core import Cog, s


class Moderation(Cog):
    """A cog for moderation commands."""

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
        ctx: ApplicationContext,
        members: str,
        *,
        reason: str,
    ):
        """Ban the supplied members from the guild. Limited to 10 at a time."""
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
    async def slowmode(self, ctx: ApplicationContext, seconds: int):
        """Set slowmode for the current channel."""
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
    async def lock(self, ctx: ApplicationContext, *, reason: str):
        """Lock the current channel, disabling send messages permissions for the default role."""
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
    async def unlock(self, ctx: ApplicationContext, *, reason: str):
        """Unlock the current channel, enabling send messages permissions for the default role."""
        if ctx.channel.permissions_for(ctx.guild.default_role).send_messages:
            return await ctx.respond("This channel isn't locked.")
        await ctx.channel.set_permissions(
            ctx.guild.default_role,
            send_messages=True,
            reason=f"{ctx.author} ({ctx.author.id}): {reason}",
        )
        await ctx.respond("Unlocked this channel.")


def setup(bot):
    bot.add_cog(Moderation(bot))
