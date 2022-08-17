import asyncio
from typing import Optional, Union

import discord

from core import (
    Cog,
    Context,
    GuildModel,
    LogAction,
    LogActions,
    humanize_time,
)


class ModLogs(Cog):
    """Commands related to logs."""

    async def mod_log(
        self,
        mod: discord.Member,
        target: discord.User,
        reason: Optional[str],
        action: LogAction,
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
        action: LogAction,
        channel: discord.TextChannel,
        after: Optional[Union[discord.Role, discord.TextChannel]] = None,
    ) -> None:
        if isinstance(target, discord.Role):
            # action target is a role
            if action is LogActions.ROLE_UPDATE:
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
            if action is LogActions.CHANNEL_UPDATE:
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

                if changes_of_channel:
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

    logs = discord.SlashCommandGroup(
        "logs",
        "Commands related to logs.",
        guild_only=True,
        default_member_permissions=discord.Permissions(manage_guild=True),
    )

    @logs.command(name="set")
    @discord.option(
        "category",
        choices=["Moderation", "Server"],
        description="The category of logs to set a channel for.",
    )
    @discord.option(
        "channel",
        description="The channel these logs will be sent to.",
    )
    async def logs_set(
        self,
        ctx: Context,
        category: str,
        channel: discord.TextChannel,
    ):
        """Set channels for logs."""
        field = "mod_log" if category == "Moderation" else "server_log"
        await GuildModel.update_or_create(id=ctx.guild_id, defaults={field: channel.id})
        await ctx.respond(f"{category} logs will be sent to {channel.mention}.")

    @logs.command(name="disable")
    @discord.option(
        "category",
        choices=["Moderation", "Server"],
        description="The category of logs to disable.",
    )
    async def logs_disable(self, ctx: Context, category: str):
        field = "mod_log" if category == "Moderation" else "server_log"
        if (
            guild := await GuildModel.filter(id=ctx.guild_id)
            .exclude(**{field: 0})
            .first()
        ):
            await guild.update_from_dict({field: 0}).save()
            return await ctx.respond(
                f"{category} logs have been disabled for this server."
            )
        await ctx.respond(f"{category} logs are already disabled for this server.")

    @Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user):
        if channel := await GuildModel.get_text_channel(guild, "mod_log"):
            await asyncio.sleep(2)
            async for entry in guild.audit_logs(
                limit=20, action=discord.AuditLogAction.ban
            ):
                if entry.target == user:
                    return await self.mod_log(
                        entry.user, user, entry.reason, LogActions.BAN, channel
                    )

    @Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user):
        if channel := await GuildModel.get_text_channel(guild, "mod_log"):
            await asyncio.sleep(2)
            async for entry in guild.audit_logs(
                limit=20, action=discord.AuditLogAction.unban
            ):
                if entry.target == user:
                    return await self.mod_log(
                        entry.user, user, entry.reason, LogActions.UNBAN, channel
                    )

    @Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if channel := await GuildModel.get_text_channel(member.guild, "mod_log"):
            await asyncio.sleep(2)
            async for entry in member.guild.audit_logs(
                limit=20, action=discord.AuditLogAction.kick
            ):
                if entry.target == member:
                    return await self.mod_log(
                        entry.user, member, entry.reason, LogActions.KICK, channel
                    )

    @Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if (
            before.communication_disabled_until == after.communication_disabled_until
            or not after.timed_out
        ):
            return
        if channel := await GuildModel.get_text_channel(after.guild, "mod_log"):
            await asyncio.sleep(2)
            async for entry in after.guild.audit_logs(
                limit=20, action=discord.AuditLogAction.member_update
            ):
                if entry.target == after and entry.user != after:
                    if entry.reason and entry.reason.startswith("Automod:"):
                        return  # don't log auto-timeouts

                    duration = (
                        after.communication_disabled_until - discord.utils.utcnow()
                    )
                    reason = f"{entry.reason}\n:hourglass_flowing_sand: **Duration:** {humanize_time(duration)}"
                    return await self.mod_log(
                        entry.user, after, reason, LogActions.TIMEOUT, channel
                    )

    # server logs
    @Cog.listener()
    async def on_guild_channel_create(self, channel):
        if mod_log := await GuildModel.get_text_channel(channel.guild, "server_log"):
            await asyncio.sleep(2)
            async for entry in channel.guild.audit_logs(
                limit=20, action=discord.AuditLogAction.channel_create
            ):
                if entry.target == channel:
                    return await self.server_log(
                        entry.user,
                        channel,
                        entry.reason,
                        LogActions.CHANNEL_CREATE,
                        mod_log,
                    )

    @Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if mod_log := await GuildModel.get_text_channel(channel.guild, "server_log"):
            await asyncio.sleep(2)
            async for entry in channel.guild.audit_logs(
                limit=20, action=discord.AuditLogAction.channel_delete
            ):
                if entry.target == channel:
                    return await self.server_log(
                        entry.user,
                        channel,
                        entry.reason,
                        LogActions.CHANNEL_DELETE,
                        mod_log,
                    )

    @Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if mod_log := await GuildModel.get_text_channel(after.guild, "server_log"):
            await asyncio.sleep(2)
            async for entry in before.guild.audit_logs(
                limit=20, action=discord.AuditLogAction.channel_update
            ):
                if entry.target == before:
                    return await self.server_log(
                        entry.user,
                        before,
                        entry.reason,
                        LogActions.CHANNEL_UPDATE,
                        mod_log,
                        after,
                    )

    @Cog.listener()
    async def on_guild_role_create(self, role):
        if mod_log := await GuildModel.get_text_channel(role.guild, "server_log"):
            await asyncio.sleep(2)
            async for entry in role.guild.audit_logs(
                limit=20, action=discord.AuditLogAction.role_create
            ):
                if entry.target == role:
                    return await self.server_log(
                        entry.user, role, entry.reason, LogActions.ROLE_CREATE, mod_log
                    )

    @Cog.listener()
    async def on_guild_role_delete(self, role):
        if mod_log := await GuildModel.get_text_channel(role.guild, "server_log"):
            await asyncio.sleep(2)
            async for entry in role.guild.audit_logs(
                limit=20, action=discord.AuditLogAction.role_delete
            ):
                if entry.target == role:
                    return await self.server_log(
                        entry.user, role, entry.reason, LogActions.ROLE_DELETE, mod_log
                    )

    @Cog.listener()
    async def on_guild_role_update(self, before, after):
        if mod_log := await GuildModel.get_text_channel(after.guild, "server_log"):
            await asyncio.sleep(2)
            async for entry in before.guild.audit_logs(
                limit=20, action=discord.AuditLogAction.role_update
            ):
                if entry.target == before:
                    return await self.server_log(
                        entry.user,
                        before,
                        entry.reason,
                        LogActions.ROLE_UPDATE,
                        mod_log,
                        after,
                    )


def setup(bot):
    bot.add_cog(ModLogs(bot))
