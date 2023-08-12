import asyncio

import discord
from discord.utils import utcnow

from core import Cog, Context, GuildModel, LogAction, LogActions, humanize_time


class CreateThreadModal(discord.ui.Modal):
    def __init__(self, view: "CreateThreadView") -> None:
        super().__init__(
            discord.ui.InputText(label="Thread name", max_length=99),
            title="Create Thread",
        )
        self.view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        assert self.view.message and self.children[0].value
        thread = await self.view.message.create_thread(name=self.children[0].value)
        await interaction.response.send_message(
            f"Thread created: {thread.mention}", ephemeral=True
        )
        await self.view.message.edit(view=None)
        self.view.stop()


class CreateThreadView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=3600, disable_on_timeout=True)

    @discord.ui.button(label="Create Thread", style=discord.ButtonStyle.green)
    async def create_thread(self, _, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(CreateThreadModal(self))


class Logs(Cog):
    """Commands related to logs."""

    async def mod_log(
        self,
        mod: discord.Member,
        target: discord.User | discord.Member,
        reason: str | None,
        action: LogAction,
        channel: discord.TextChannel,
    ) -> None:
        await channel.send(
            embed=discord.Embed(
                description=(
                    f"{action.emoji} **{action.text}** {target} (ID: {target.id})\n"
                    f":page_facing_up: **Reason:** {reason}\n"
                    f":calendar_spiral: <t:{int(utcnow().timestamp())}>"
                ),
                color=action.color,
            )
            .set_author(name=f"{mod.display_name} (ID: {mod.id})", icon_url=mod.display_avatar)
            .set_thumbnail(url=target.display_avatar),
            view=CreateThreadView(),
        )

    async def server_log(
        self,
        mod: discord.Member,
        target: discord.Role | discord.TextChannel,
        reason: str | None,
        action: LogAction,
        channel: discord.TextChannel,
        after: discord.Role | discord.TextChannel | None = None,
    ) -> None:
        changes: list[str] = []
        if isinstance(target, discord.Role):
            assert isinstance(after, discord.Role)
            if action is LogActions.ROLE_UPDATE:
                if target.name != after.name:
                    changes.append(
                        f"- Name changed from **@{target.name}** to {after.mention}."
                    )
                if after.hoist and not target.hoist:
                    changes.append("Members are now displayed seperately from online members.")
                elif target.hoist and not after.hoist:
                    changes.append("Members are no longer displayed seperately from online members.")
        elif action is LogActions.CHANNEL_UPDATE:
            assert after
            if target.name != after.name:
                changes.append(
                    f"- Name changed from **#{target.name}** to {after.mention}."
                )
            if target.position != after.position:
                changes.append(
                    f"- Position changed from `{target.position+1}` to `{after.position+1}`."
                )

            if isinstance(target, discord.TextChannel):
                assert isinstance(after, discord.TextChannel)
                if target.topic != after.topic:
                    if target.topic and after.topic:
                        changes.append(
                            "- Topic changed from `{target.topic}` to `{after.topic}`."
                        )
                    elif not target.topic:
                        changes.append("- Topic has been added.")
                    else:
                        changes.append("- Topic has been removed.")
                if target.slowmode_delay != after.slowmode_delay:
                    changes.append(
                        f"- Slowmode delay changed from `{target.slowmode_delay}s` to `{after.slowmode_delay}s`."
                    )
            elif isinstance(target, discord.VoiceChannel):
                assert isinstance(after, discord.VoiceChannel)
                if target.user_limit != after.user_limit:
                    changes.append(
                        f"- Voice users limit changed from `{target.user_limit}` to `{after.user_limit}`."
                    )

        await channel.send(
            embed=discord.Embed(
                description=(
                    f"{action.emoji} **{action.text}** {target.mention} (ID: {target.id})\n"
                    f":page_facing_up: **Reason:** {reason}\n"
                    f":calendar_spiral: <t:{int(utcnow().timestamp())}>"
                ),
                color=action.color,
                fields=[discord.EmbedField(name="Changes", value="\n".join(changes))],
            )
            .set_author(name=f"{mod.display_name} (ID: {mod.id})", icon_url=mod.display_avatar)
            .set_thumbnail(url=mod.display_avatar),
            view=CreateThreadView(),
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
                    assert isinstance(entry.user, discord.Member)
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
                    assert isinstance(entry.user, discord.Member)
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
                    assert isinstance(entry.user, discord.Member)
                    return await self.mod_log(
                        entry.user, member, entry.reason, LogActions.KICK, channel
                    )

    @Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        assert after.communication_disabled_until
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
                    assert isinstance(entry.user, discord.Member)
                    if entry.reason and entry.reason.startswith("Automod:"):
                        return  # don't log auto-timeouts

                    duration = after.communication_disabled_until - utcnow()
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
    bot.add_cog(Logs(bot))
