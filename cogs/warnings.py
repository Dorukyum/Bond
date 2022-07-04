import discord
from discord import ApplicationContext

from utils import Cog, WarnModel


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
    ) -> None:
        """Warn a member."""
        await WarnModel.create(
            mod_id=ctx.author.id,
            target_id=member.id,
            guild_id=ctx.guild.id,
            reason=reason,
        )
        await ctx.respond(f"Warned `{member}`.")

    @discord.slash_command()
    @discord.guild_only()
    @discord.default_permissions(manage_messages=True)
    @discord.option(
        "id", description="The ID of the warning. Use `/warns` to view warn data."
    )
    async def delwarn(self, ctx: ApplicationContext, id: int):
        """Delete a warning."""
        if warn := await WarnModel.get_or_none(id=id, guild_id=ctx.guild.id):
            await warn.delete()
            return await ctx.respond("Warning deleted.")
        await ctx.respond(f"Couldn't find a warning in this guild with the id `{id}`.")

    @discord.slash_command()
    @discord.guild_only()
    @discord.default_permissions(manage_messages=True)
    @discord.option("member", description="The member to view the warnings given to.")
    async def warns(self, ctx: ApplicationContext, member: discord.Member):
        """View the warnings given to a member."""
        if warns := await WarnModel().filter(
            target_id=member.id, guild_id=ctx.guild.id
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
