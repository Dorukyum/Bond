import discord
from discord import ApplicationContext

from cogs.modlogs import ModLogs
from core import Cog, GuildModel, LogActions, WarnModel


class Warns(Cog):
    """A cog for commands related to warnings."""

    def format_warn(self, warn: WarnModel) -> str:
        return f"#{warn.id} | <t:{int(warn.created_at.timestamp())}:R>:\n{warn.reason}\nBy **{self.bot.get_user(warn.mod_id)}**"

    @discord.slash_command()
    @discord.guild_only()
    @discord.default_permissions(manage_messages=True)
    @discord.option("member", description="The member to warn.")
    @discord.option("reason", description="The reason of the warning.")
    async def warn(
        self, ctx: ApplicationContext, member: discord.Member, *, reason: str
    ):
        """Warn a member."""
        if member == ctx.author:
            return await ctx.respond("You can't warn yourself.")
        assert ctx.guild and isinstance(ctx.author, discord.Member)
        if (
            member.top_role.position > ctx.author.top_role.position
            and not ctx.guild.owner_id == ctx.author.id
        ):
            return await ctx.respond(
                "The member you're trying to warn has a higher top role than you."
            )
        if ctx.guild.owner_id == member.id:
            return await ctx.respond("You can't warn the owner of the server.")
        if member.bot:
            return await ctx.respond("You can't warn a bot.")
        await WarnModel.create(
            mod_id=ctx.author.id,
            target_id=member.id,
            guild_id=ctx.guild_id,
            reason=reason,
        )
        await ctx.respond(f"Warned `{member}`.")
        if channel := await GuildModel.get_text_channel(ctx.guild, "mod_log"):
            if isinstance((cog := self.bot.get_cog("ModLogs")), ModLogs):
                await cog.mod_log(ctx.author, member, reason, LogActions.WARN, channel)

    @discord.slash_command()
    @discord.guild_only()
    @discord.default_permissions(manage_messages=True)
    @discord.option(
        "id", description="The ID of the warning. Use `/warns` to view warn data."
    )
    async def delwarn(self, ctx: ApplicationContext, id: int):
        """Delete a warning."""
        if warn := await WarnModel.get_or_none(id=id, guild_id=ctx.guild_id):
            await warn.delete()
            return await ctx.respond("Warning deleted.")
        await ctx.respond(f"Couldn't find a warning in this guild with the id `{id}`.")

    @discord.slash_command()
    @discord.guild_only()
    @discord.default_permissions(manage_messages=True)
    @discord.option("member", description="The member to view the warnings given to.")
    async def warns(self, ctx: ApplicationContext, member: discord.Member):
        """View the warnings given to a member."""
        if member.bot:
            return await ctx.respond("Bots can't be warned.")
        if warns := await WarnModel().filter(
            target_id=member.id, guild_id=ctx.guild_id
        ):
            return await ctx.respond(
                embed=discord.Embed(
                    title=f"Warnings | {member.display_name}",
                    description="\n\n".join(self.format_warn(warn) for warn in warns),
                    color=discord.Color.brand_red(),
                )
            )
        await ctx.respond("This member has received no warnings.")


def setup(bot):
    bot.add_cog(Warns(bot))
