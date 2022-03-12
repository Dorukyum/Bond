import asyncio
from typing import Optional, Union

import discord
from discord.ext.commands import Context, command, guild_only, has_permissions

from utils import Cog, GuildModel, humanize_time, ModAction, ModActions


class ModLogs(Cog):
    """A cog for moderation action logging."""

    async def mod_log_channel(
        self, guild: discord.Guild
    ) -> Optional[discord.TextChannel]:
        guild_data, _ = await GuildModel.get_or_create(id=guild.id)
        if guild_data.mod_log:
            return guild.get_channel(guild_data.mod_log)

    async def server_log_channel(
        self, guild: discord.Guild
    ) -> Optional[discord.TextChannel]:
        guild_data, _ = await GuildModel.get_or_create(id=guild.id)
        if guild_data.server_log:
            return guild.get_channel(guild_data.server_log)

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

    async def server_log(
        self,
        mod: discord.Member,
        target: Union[discord.Role, discord.TextChannel],
        reason: Optional[str],
        action: ModAction,
        channel: discord.TextChannel,
        after: Optional[Union[discord.Role, discord.TextChannel]] = None,
    ) -> None:
        if isinstance(target, discord.Role):
            # action target is a role
            if action is ModActions.ROLE_UPDATE:
                changes_of_role = []
                if target.name != after.name:
                    changes_of_role.append(
                        f"Name has been changed from {target.name} to {after.name}."
                    )
                if target.hoist != after.hoist:
                    if after.hoist:
                        changes_of_role.append("Role has been hoisted.")
                    else:
                        changes_of_role.append("Role has been non-hoisted.")
                await channel.send(
                    embed=discord.Embed(
                        description=f"**{action.emoji} {action.text}** {after.mention} *(ID {target.id})*\n:page_facing_up: **Reason:** {reason}",
                        color=getattr(discord.Color, action.color)(),
                    )
                    .add_field(
                        name="Changes",
                        value="\n".join(changes_of_role),
                    )
                    .set_author(name=f"{mod} (ID {mod.id})")
                )
                return
            await channel.send(
                embed=discord.Embed(
                    description=f"**{action.emoji} {action.text}** {after.mention} *(ID {target.id})*\n:page_facing_up: **Reason:** {reason}",
                    color=getattr(discord.Color, action.color)(),
                ).set_author(name=f"{mod} (ID {mod.id})")
            )
        else:
            if action is ModActions.CHANNEL_UPDATE:
                changes_of_channel = []
                if target.name != after.name:
                    changes_of_channel.append(
                        f"Name has been changed from **#{target.name}** to {after.mention}."
                    )
                if target.position != after.position:
                    changes_of_channel.append(
                        f"Position has been changed from {target.position+1} to {after.position+1}."
                    )

                if isinstance(target, discord.TextChannel):
                    if target.topic != after.topic:
                        if target.topic and after.topic:
                            changes_of_channel.append(
                                "Topic has been changed from `{0.topic}` to `{1.topic}`.".format(
                                    target, after
                                )
                            )
                        elif not target.topic:
                            changes_of_channel.append("Topic has been added.")
                        else:
                            changes_of_channel.append("Topic has been removed.")
                    if target.slowmode_delay != after.slowmode_delay:
                        changes_of_channel.append(
                            f"Slowmode has been changed from `{target.slowmode_delay}s` to `{after.slowmode_delay}s`."
                        )

                elif isinstance(target, discord.VoiceChannel):
                    if target.user_limit != after.user_limit:
                        changes_of_channel.append(
                            f"Voice members limit has changed from `{target.user_limit}` to `{after.user_limit}`."
                        )

                await channel.send(
                    embed=discord.Embed(
                        description=f"**{action.emoji} {action.text}** {target.mention} *(ID {target.id})*\n:page_facing_up: **Reason:** {reason}",
                        color=getattr(discord.Color, action.color)(),
                    )
                    .add_field(
                        name="Changes",
                        value="\n".join(changes_of_channel),
                    )
                    .set_author(name=f"{mod} (ID {mod.id})")
                )
                return
            await channel.send(
                embed=discord.Embed(
                    description=f"**{action.emoji} {action.text}** {target.mention} *(ID {target.id})*\n:page_facing_up: **Reason:** {reason}",
                    color=getattr(discord.Color, action.color)(),
                ).set_author(name=f"{mod} (ID {mod.id})")
            )

    @command(name="mod_log")
    @has_permissions(manage_guild=True)
    @guild_only()
    async def _modlog(self, ctx: Context, channel_id: int):
        """Set the channel for moderation logs. Use `0` as channel_id to disable mod logs."""
        channel = ctx.guild.get_channel(channel_id)
        if channel_id != 0 and (
            channel is None or not isinstance(channel, discord.TextChannel)
        ):
            return await ctx.send(
                "A text channel in this guild with the given ID wasn't found."
            )
        guild, _ = await GuildModel.get_or_create(id=ctx.guild.id)
        await guild.update_from_dict({"mod_log": channel_id})
        await guild.save()
        if channel_id == 0:
            return await ctx.send("Mod logs have been disabled for this server.")
        await ctx.send(f"The mod log channel for this server is now {channel.mention}.")

    @command(name="server_log")
    @has_permissions(manage_guild=True)
    @guild_only()
    async def _serverlog(self, ctx: Context, channel_id: int):
        """Set the channel for server logs. Use `0` as channel_id to disable server logs."""
        channel = ctx.guild.get_channel(channel_id)
        if channel_id != 0 and (
            channel is None or not isinstance(channel, discord.TextChannel)
        ):
            return await ctx.send(
                "A text channel in this guild with the given ID wasn't found."
            )
        guild, _ = await GuildModel.get_or_create(id=ctx.guild.id)
        await guild.update_from_dict({"server_log": channel_id})
        await guild.save()
        if channel_id == 0:
            return await ctx.send("Server logs have been disabled for this server.")
        await ctx.send(
            f"The server log channel for this server is now {channel.mention}."
        )

    @Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user):
        if channel := await self.mod_log_channel(guild):
            await asyncio.sleep(2)
            async for entry in guild.audit_logs(
                limit=20, action=discord.AuditLogAction.ban
            ):
                if entry.target == user:
                    return await self.mod_log(
                        entry.user, user, entry.reason, ModActions.BAN, channel
                    )

    @Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user):
        if channel := await self.mod_log_channel(guild):
            await asyncio.sleep(2)
            async for entry in guild.audit_logs(
                limit=20, action=discord.AuditLogAction.unban
            ):
                if entry.target == user:
                    return await self.mod_log(
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
                    return await self.mod_log(
                        entry.user, member, entry.reason, ModActions.KICK, channel
                    )

    @Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if (
            before.communication_disabled_until == after.communication_disabled_until
            or not after.timed_out
        ):
            return
        if channel := await self.mod_log_channel(after.guild):
            await asyncio.sleep(2)
            async for entry in after.guild.audit_logs(
                limit=20, action=discord.AuditLogAction.member_update
            ):
                if entry.target == after and entry.user != after:
                    duration = (
                        after.communication_disabled_until - discord.utils.utcnow()
                    )
                    reason = f"{entry.reason}\n:hourglass_flowing_sand: **Duration:** {humanize_time(duration)}"
                    return await self.mod_log(
                        entry.user, after, reason, ModActions.TIMEOUT, channel
                    )

    # server logs
    @Cog.listener()
    async def on_guild_channel_create(self, channel):
        if mod_log := await self.server_log_channel(channel.guild):
            await asyncio.sleep(2)
            async for entry in channel.guild.audit_logs(
                limit=20, action=discord.AuditLogAction.channel_create
            ):
                if entry.target == channel:
                    return await self.server_log(
                        entry.user,
                        channel,
                        entry.reason,
                        ModActions.CHANNEL_CREATE,
                        mod_log,
                    )

    @Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if mod_log := await self.server_log_channel(channel.guild):
            await asyncio.sleep(2)
            async for entry in channel.guild.audit_logs(
                limit=20, action=discord.AuditLogAction.channel_delete
            ):
                if entry.target == channel:
                    return await self.server_log(
                        entry.user,
                        channel,
                        entry.reason,
                        ModActions.CHANNEL_DELETE,
                        mod_log,
                    )

    @Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if mod_log := await self.server_log_channel(before.guild):
            await asyncio.sleep(2)
            async for entry in before.guild.audit_logs(
                limit=20, action=discord.AuditLogAction.channel_update
            ):
                if entry.target == before:
                    return await self.server_log(
                        entry.user,
                        before,
                        entry.reason,
                        ModActions.CHANNEL_UPDATE,
                        mod_log,
                        after,
                    )

    @Cog.listener()
    async def on_guild_role_create(self, role):
        if mod_log := await self.server_log_channel(role.guild):
            await asyncio.sleep(2)
            async for entry in role.guild.audit_logs(
                limit=20, action=discord.AuditLogAction.role_create
            ):
                if entry.target == role:
                    return await self.server_log(
                        entry.user, role, entry.reason, ModActions.ROLE_CREATE, mod_log
                    )

    @Cog.listener()
    async def on_guild_role_delete(self, role):
        if mod_log := await self.server_log_channel(role.guild):
            await asyncio.sleep(2)
            async for entry in role.guild.audit_logs(
                limit=20, action=discord.AuditLogAction.role_delete
            ):
                if entry.target == role:
                    return await self.server_log(
                        entry.user, role, entry.reason, ModActions.ROLE_DELETE, mod_log
                    )

    @Cog.listener()
    async def on_guild_role_update(self, before, after):
        if mod_log := await self.server_log_channel(before.guild):
            await asyncio.sleep(2)
            async for entry in before.guild.audit_logs(
                limit=20, action=discord.AuditLogAction.role_update
            ):
                if entry.target == before:
                    return await self.server_log(
                        entry.user,
                        before,
                        entry.reason,
                        ModActions.ROLE_UPDATE,
                        mod_log,
                        after,
                    )


def setup(bot):
    bot.add_cog(ModLogs(bot))
