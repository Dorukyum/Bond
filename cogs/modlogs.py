import asyncio
from typing import Optional

import discord
from discord.ext.commands import Context, command, guild_only, has_permissions

from utils import Cog, GuildModel, ModAction, ModActions


class ModLogs(Cog):
    """A cog for moderation action logging."""

    async def mod_log_channel(self, guild: discord.Guild) -> Optional[discord.TextChannel]:
        id, _ = (await GuildModel.get_or_create(id=guild.id)).mod_log
        if id:
            return guild.get_channel(id)

    async def mod_log(
        self,
        mod: discord.Member,
        target: discord.User,
        reason: Optional[str],
        action: ModAction,
        channel: discord.TextChannel,
    ) -> None:
        await channel.send(
            embed=discord.Embed(
                description=f"**{action.emoji} {action.text} {target.name}**#{target.discriminator} *(ID {target.id})*\n:page_facing_up: **Reason:** {reason}",
                color=getattr(discord.Color, action.color)(),
            )
            .set_author(name=f"{mod} (ID {mod.id})", icon_url=mod.display_avatar)
            .set_thumbnail(url=target.display_avatar)
        )

    @command(name="mod_log")
    @has_permissions(manage_guild=True)
    @guild_only()
    async def _modlog(self, ctx: Context, channel_id: int):
        """Set the channel for moderation logs. Use `0` as channel_id to disable mod logs."""
        channel = ctx.guild.get_channel(channel_id)
        if channel_id != 0 and (channel is None or not isinstance(channel, discord.TextChannel)):
            return await ctx.send("A text channel in this guild with the given ID wasn't found.")
        guild, _ = await GuildModel.get_or_create(id=ctx.guild.id)
        await guild.update_from_dict({"mod_log": channel_id})
        await guild.save()
        if channel_id == 0:
            return await ctx.send("Mod logs have been disabled for this server.")
        await ctx.send(f"The mod log channel for this server is now {channel.mention}.")

    @Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user):
        if channel := await self.mod_log_channel(guild):
            await asyncio.sleep(2)
            async for entry in guild.audit_logs(
                limit=20, action=discord.AuditLogAction.ban
            ):
                if entry.target == user:
                    await self.mod_log(
                        entry.user, user, entry.reason, ModActions.BAN, channel
                    )

    @Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user):
        if channel := await self.mod_log_channel(guild):
            await asyncio.sleep(2)
            async for entry in guild.audit_logs(
                limit=20, action=discord.AuditLogAction.unban
            ):
                if entry.target == user:
                    await self.mod_log(
                        entry.user, user, entry.reason, ModActions.UNBAN, channel
                    )

    @Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if channel := await self.mod_log_channel(member.guild):
            await asyncio.sleep(2)
            async for entry in member.guild.audit_logs(
                limit=20, action=discord.AuditLogAction.kick
            ):
                if entry.target == member:
                    await self.mod_log(
                        entry.user, member, entry.reason, ModActions.KICK, channel
                    )
                    return


def setup(bot):
    bot.add_cog(ModLogs(bot))
