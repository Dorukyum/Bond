import asyncio
from collections import namedtuple
from datetime import timedelta

import discord
from discord.utils import utcnow

from core import Cog, Context, GuildModel, humanize_time

Preset = namedtuple("Preset", ("color", "emoji", "text"))
PRESETS = {
    "warning": Preset(discord.Color.yellow(), ":warning:", "Warned"),
    "timeout": Preset(discord.Color.dark_orange(), ":stopwatch:", "Timed out"),
    "kick": Preset(discord.Color.orange(), ":boot:", "Kicked"),
    "ban": Preset(discord.Color.from_rgb(255, 0, 0), ":no_entry_sign:", "Banned"),
    "unban": Preset(discord.Color.brand_green(), ":unlock:", "Unbanned"),
    "channel_create": Preset(
        discord.Color.yellow(), ":heavy_plus_sign:", "Created channel"
    ),
    "channel_delete": Preset(
        discord.Color.dark_orange(), ":heavy_minus_sign:", "Deleted channel"
    ),
    "channel_update": Preset(discord.Color.orange(), ":wrench:", "Updated channel"),
    "role_create": Preset(discord.Color.yellow(), ":heavy_plus_sign:", "Created role"),
    "role_delete": Preset(
        discord.Color.dark_orange(), ":heavy_minus_sign:", "Deleted role"
    ),
    "role_update": Preset(discord.Color.orange(), ":wrench:", "Updated role"),
}


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

    async def log_moderation_action(
        self,
        action: str,
        target: discord.User | discord.Member,
        mod: discord.Member,
        reason: str | None,
        channel: discord.TextChannel,
    ) -> None:
        action_preset = PRESETS[action]
        await channel.send(
            embed=discord.Embed(
                description=(
                    f"{action_preset.emoji} **{action_preset.text}** {target} (ID: {target.id})\n"
                    f":page_facing_up: **Reason:** {reason}\n"
                    f":calendar_spiral: <t:{int(utcnow().timestamp())}>"
                ),
                color=action_preset.color,
            )
            .set_author(
                name=f"{mod.display_name} (ID: {mod.id})", icon_url=mod.display_avatar
            )
            .set_thumbnail(url=target.display_avatar),
            view=CreateThreadView(),
        )

    async def log_server_action(
        self,
        action: str,
        target: discord.abc.GuildChannel | discord.Role,
        changelog: str,
        mod: discord.Member,
        reason: str | None,
        channel: discord.TextChannel,
    ) -> None:
        action_preset = PRESETS[action]
        await channel.send(
            embed=discord.Embed(
                description=(
                    f"{action_preset.emoji} **{action_preset.text}** {target.mention} (ID: {target.id})\n"
                    f":page_facing_up: **Reason:** {reason}\n"
                    f":calendar_spiral: <t:{int(utcnow().timestamp())}>\n\n"
                    f"**Changes**\n{changelog}"
                ),
                color=action_preset.color,
            )
            .set_author(
                name=f"{mod.display_name} (ID: {mod.id})", icon_url=mod.display_avatar
            )
            .set_thumbnail(url=mod.display_avatar),
            view=CreateThreadView(),
        )

    async def prepare_moderation_log(
        self, action: str, guild: discord.Guild, target: discord.User | discord.Member
    ):
        if channel := await GuildModel.get_text_channel(guild, "mod_log"):
            await asyncio.sleep(1)
            async for entry in guild.audit_logs(
                action=getattr(discord.AuditLogAction, action),
                after=utcnow() - timedelta(seconds=2),
            ):
                if entry.target == target:
                    assert isinstance(entry.user, discord.Member)
                    return await self.log_moderation_action(
                        action,
                        target,
                        entry.user,
                        entry.reason,
                        channel,
                    )

    async def prepare_server_log(
        self,
        action: str,
        before: discord.abc.GuildChannel | discord.Role,
        after: discord.abc.GuildChannel | discord.Role | None = None,
    ):
        if not (
            channel := await GuildModel.get_text_channel(before.guild, "server_log")
        ):
            return

        await asyncio.sleep(1)
        async for entry in before.guild.audit_logs(
            action=getattr(discord.AuditLogAction, action),
            after=utcnow() - timedelta(seconds=2),
        ):
            if entry.target == before:
                break
        else:  # I don't want to enter nesting hell
            return

        changelog = ""
        if isinstance(before, discord.Role):
            assert isinstance(after, discord.Role)
            if action == "role_update":
                if before.name != after.name:
                    changelog += (
                        f"- Name changed from **@{before.name}** to {after.mention}.\n"
                    )
                if after.hoist and not before.hoist:
                    changelog += (
                        "Members are now displayed seperately from online members.\n"
                    )
                elif before.hoist and not after.hoist:
                    changelog += "Members are no longer displayed seperately from online members.\n"
        elif action == "channel_update":
            assert after
            if before.name != after.name:
                changelog += (
                    f"- Name changed from **#{before.name}** to {after.mention}.\n"
                )
            if before.position != after.position:
                changelog += f"- Position changed from `{before.position+1}` to `{after.position+1}`.\n"

            if isinstance(before, discord.TextChannel):
                assert isinstance(after, discord.TextChannel)
                if before.topic != after.topic:
                    if before.topic and after.topic:
                        changelog += "- Topic changed from `{target.topic}` to `{after.topic}`.\n"
                    elif not before.topic:
                        changelog += "- Topic has been added.\n"
                    else:
                        changelog += "- Topic has been removed.\n"
                if before.slowmode_delay != after.slowmode_delay:
                    changelog += f"- Slowmode delay changed from `{before.slowmode_delay}s` to `{after.slowmode_delay}s`.\n"
            elif isinstance(before, discord.VoiceChannel):
                assert isinstance(after, discord.VoiceChannel)
                if before.user_limit != after.user_limit:
                    changelog += f"- Voice users limit changed from `{before.user_limit}` to `{after.user_limit}`.\n"

        assert isinstance(entry.user, discord.Member)
        return await self.log_server_action(
            action,
            before,
            changelog,
            entry.user,
            entry.reason,
            channel,
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
            await asyncio.sleep(1)
            async for entry in after.guild.audit_logs(
                action=discord.AuditLogAction.member_update,
                after=utcnow() - timedelta(seconds=2),
            ):
                if entry.target == after and entry.user != after:
                    assert isinstance(entry.user, discord.Member)

                    duration = after.communication_disabled_until - utcnow()
                    reason = f"{entry.reason}\n:hourglass_flowing_sand: **Duration:** {humanize_time(duration)}"
                    return await self.log_moderation_action(
                        "timeout",
                        after,
                        entry.user,
                        reason,
                        channel,
                    )

    @Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user):
        await self.prepare_moderation_log("ban", guild, user)

    @Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user):
        await self.prepare_moderation_log("unban", guild, user)

    @Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.prepare_moderation_log("kick", member.guild, member)

    @Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        await self.prepare_server_log("channel_create", channel)

    @Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        await self.prepare_server_log("channel_delete", channel)

    @Cog.listener()
    async def on_guild_channel_update(
        self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel
    ):
        await self.prepare_server_log("channel_update", before, after)

    @Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        await self.prepare_server_log("role_create", role)

    @Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        await self.prepare_server_log("role_delete", role)

    @Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        await self.prepare_server_log("role_delete", before, after)

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


def setup(bot):
    bot.add_cog(Logs(bot))
