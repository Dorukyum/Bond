import discord
from discord.utils import utcnow

from core import Cog, Context, GuildModel, WarnModel


async def warn(
    interaction: discord.Interaction, member: discord.Member, reason: str | None = None
):
    assert interaction.guild and isinstance(interaction.user, discord.Member)
    if member == interaction.user:
        return await interaction.response.send_message(
            "You can't warn yourself.", ephemeral=True
        )
    if (
        member.top_role.position > interaction.user.top_role.position
        and not interaction.guild.owner_id == interaction.user.id
    ):
        return await interaction.response.send_message(
            "The member you're trying to warn has a higher top role than you.",
            ephemeral=True,
        )
    if interaction.guild.owner_id == member.id:
        return await interaction.response.send_message(
            "You can't warn the owner of the server.", ephemeral=True
        )
    if member.bot:
        return await interaction.response.send_message(
            "You can't warn a bot.", ephemeral=True
        )
    await WarnModel.create(
        mod_id=interaction.user.id,
        target_id=member.id,
        guild_id=interaction.guild_id,
        reason=reason,
    )
    await interaction.response.send_message(f"Warned `{member}` for `{reason}`.")


class WarnModal(discord.ui.Modal):
    def __init__(self, member: discord.Member, logs: discord.Cog | None) -> None:
        super().__init__(
            discord.ui.InputText(
                label="Reason", placeholder="The reason for warning this member"
            ),
            title="Warn Member",
        )
        self.member = member
        self.logs = logs

    async def callback(self, interaction: discord.Interaction) -> None:
        assert interaction.guild
        await warn(interaction, self.member, reason=self.children[0].value)
        if (
            channel := await GuildModel.get_text_channel(interaction.guild, "mod_log")
            and self.logs
        ):
            await self.logs.log_moderation_action(  # type: ignore # cog must be the logs cog
                "warning",
                self.member,
                interaction.user,
                self.children[0].value,
                channel,
            )


class Warnings(Cog):
    """Commands related to warnings."""

    def format_warning(self, warn: WarnModel) -> str:
        mod = self.bot.get_user(warn.mod_id)
        return (
            f"#{warn.id} | <t:{int(warn.created_at.timestamp())}:R>:\n"
            f"{warn.reason}\n"
            f"By **{f'{mod.name} ({mod.mention})' if mod else f'Unknown User (<@{warn.mod_id}>)'}**"
        )

    @discord.slash_command(name="warn")
    @discord.guild_only()
    @discord.default_permissions(manage_messages=True)
    @discord.option("member", description="The member to warn.")
    @discord.option("reason", description="The reason of the warning.")
    async def warn_slash(self, ctx: Context, member: discord.Member, *, reason: str):
        """Warn a member."""
        await warn(ctx.interaction, member, reason)

    @discord.user_command(name="Warn Member")
    @discord.guild_only()
    @discord.default_permissions(manage_messages=True)
    async def warn_member(self, ctx: Context, member: discord.Member):
        """Warn a member."""
        await ctx.send_modal(WarnModal(member, self.bot.get_cog("Logs")))

    warning = discord.SlashCommandGroup(
        "warning", "Commands related to warnings.", guild_only=True, default_member_permissions=discord.Permissions(manage_messages=True)
    )

    @warning.command()
    @discord.option(
        "id", description="The ID of the warning. Use `/warning list` or `View Warnings` to view warn data."
    )
    async def delete(self, ctx: Context, id: int):
        """Delete a warning."""
        if warn := await WarnModel.get_or_none(id=id, guild_id=ctx.guild_id):
            await warn.delete()
            return await ctx.respond("Warning deleted.")
        await ctx.respond(f"Couldn't find a warning in this guild with the id `{id}`.")

    async def list_warnings(self, ctx: Context, member: discord.Member):
        if member.bot:
            return await ctx.respond("Bots can't be warned.")
        if warns := await WarnModel().filter(
            target_id=member.id, guild_id=ctx.guild_id
        ):
            return await ctx.respond(
                embed=discord.Embed(
                    title=f"Warnings | {member.display_name}",
                    description="\n\n".join(self.format_warning(warn) for warn in warns),
                    color=discord.Color.yellow(),
                    thumbnail=member.display_avatar.url,
                    timestamp=utcnow(),
                )
            )
        await ctx.respond("This member has received no warnings.")

    @warning.command()
    @discord.option("member", description="The member to view the warnings given to.")
    async def list(self, ctx: Context, member: discord.Member):
        """View the warnings given to a member."""
        await self.list_warnings(ctx, member)

    @discord.user_command(name="View Warnings")
    async def view(self, ctx: Context, member: discord.Member):
        """View the warnings given to a member."""
        await self.list_warnings(ctx, member)

def setup(bot):
    bot.add_cog(Warnings(bot))
