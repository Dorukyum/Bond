import asyncio
from collections import namedtuple
from contextlib import suppress
from typing import Optional

import discord
from discord.ext.commands import Context, Greedy, command, has_permissions

from utils import Cog, s

ModAction = namedtuple("LogData", ("color", "emoji", "text"))


class Moderation(Cog):
    """A cog for moderation commands"""

    BAN = ModAction("brand_red", ":hammer:", "Banned")
    KICK = ModAction("brand_red", ":hammer:", "Kicked")
    MUTE = ModAction("dark_grey", ":mute:", "Muted")
    UNMUTE = ModAction("brand_green", ":loud_sound:", "Unmuted")

    def __init__(self, bot) -> None:
        super().__init__(bot)
        guild = bot.get_guild(881207955029110855)
        self.mod_role = guild.get_role(881407111211384902)
        self.muted_role = guild.get_role(881532095661494313)
        self.mod_log_channel = bot.get_channel(884992286826577940)

    async def mod_log(
        self,
        mod: discord.Member,
        member: discord.Member,
        reason: str,
        action: ModAction,
    ) -> None:
        await self.mod_log_channel.send(
            embed=discord.Embed(
                description=f"**{action.emoji} {action.text} {member.name}**#{member.discriminator} *(ID {member.id})*\n:page_facing_up: **Reason:** {reason}",
                color=getattr(discord.Color, action.color)(),
            ).set_author(name=f"{mod} (ID {mod.id})", icon_url=mod.display_avatar)
        )

    async def mute(
        self, member: discord.Member, reason: str, duration: Optional[float] = None
    ):
        try:
            await member.add_roles(self.muted_role, reason=reason)
        except (discord.Forbidden, discord.HTTPException):
            return

        if duration is not None:

            async def unmute():
                await asyncio.sleep(duration)
                with suppress(discord.Forbidden, discord.HTTPException):
                    await member.remove_roles(
                        self.muted_role, reason="Mute duration expired."
                    )

            self.bot.cache["unmute_task"][member.id] = asyncio.create_task(unmute())

    @command()
    @has_permissions(ban_members=True)
    async def ban(self, ctx: Context, members: Greedy[discord.Member], *, reason):
        """Ban the supplied members from the guild. Limited to 10 at a time."""
        if len(members) > 10:
            return await ctx.send("Banning multiple members is limited to 10 at a time.")

        for member in members:
            await ctx.guild.ban(member, reason=reason)
            await self.mod_log(ctx.author, member, reason, self.BAN)
        await ctx.send(f"Banned **{len(members)}** member{s(members)}.")

    @command()
    @has_permissions(manage_messages=True)
    async def slowmode(self, ctx: Context, seconds: int = 0):
        """Set slowmode for the current channel."""
        if not 21600 > seconds > 0:
            return await ctx.send("Slowmode should be between `21600` and `0` seconds.")
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(
            f"Slowmode is now `{seconds}` second{s(seconds)}."
            if seconds > 0
            else "Slowmode is now disabled."
        )

    @command(name="mute")
    @has_permissions(manage_messages=True)
    async def _mute(
        self, ctx: Context, member: discord.Member, duration: Optional[int], *, reason
    ):
        if member.top_role.position >= ctx.author.top_role.position:
            return await ctx.send("You cant mute someone with the same or higher top role.")
        await self.mute(member, reason, duration)
        await ctx.send(f"Muted {member.mention} for `{reason}`.")
        await self.mod_log(ctx.author, member, reason, self.MUTE)

    @command(name="unmute")
    @has_permissions(manage_messages=True)
    async def _unmute(self, ctx: Context, member: discord.Member):
        if self.muted_role in member.roles:
            await member.remove_roles(self.muted_role)
            if (task := self.bot.cache["unmute_task"].pop(member.id)):
                task.cancel()

            await ctx.send(f"Unmuted {member.mention}")
            await self.mod_log(ctx.author, member, "Unknown", self.UNMUTE)
        else:
            await ctx.send("This member is not muted.")

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild != self.bot.main_guild:
            return
        if message.author.bot:
            return

        mentions = len(message.raw_mentions)
        if mentions >= 6 and self.mod_role not in message.author.roles:
            await message.delete()
            if mentions >= 10:
                return await message.guild.ban(
                    message.author, reason=f"Too many mentions ({mentions})"
                )

            await message.channel.send(f"{message.author.mention} Too many mentions.")
            await self.mute(message.author, f"Too many mentions ({mentions})", 10800)


def setup(bot):
    bot.add_cog(Moderation(bot))
