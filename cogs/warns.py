import discord
from discord.ext.commands import Context, command, group

from utils import Cog, WarnModel


class Warns(Cog):
    """A cog for commands related to warns."""

    def format_warn(self, warn: WarnModel):
        return f"#{warn.id} | <t:{int(warn.created_at.timestamp())}:R>:\n{warn.reason}\nBy **{self.bot.get_user(warn.mod_id)}**"

    @group(invoke_without_command=True)
    async def warn(self, ctx: Context, member: discord.Member, *, reason: str):
        """Warn a member."""
        await WarnModel.create(
            mod_id=ctx.author.id,
            target_id=member.id,
            guild_id=ctx.guild.id,
            reason=reason,
        )
        await ctx.send(f"Warned `{member}`.")

    @warn.command()
    async def delete(self, ctx: Context, id: int):
        """Delete a warn."""
        if warn := await WarnModel.get_or_none(id=id, guild_id=ctx.guild.id):
            await warn.delete()
            return await ctx.send("Warn deleted.")
        await ctx.send(f"Couldn't find a warn in this guild with the id `{id}`.")

    @command()
    async def warns(self, ctx: Context, member: discord.Member):
        if warns := await WarnModel().filter(
            target_id=member.id, guild_id=ctx.guild.id
        ):
            return await ctx.send(
                embed=discord.Embed(
                    title=f"Warns | {member.display_name}",
                    description="\n\n".join(self.format_warn(warn) for warn in warns),
                    color=discord.Color.brand_red(),
                )
            )
        await ctx.send("This member has no warns.")

    async def cog_check(self, ctx):
        return ctx.author.guild_permissions.manage_messages


def setup(bot):
    bot.add_cog(Warns(bot))
