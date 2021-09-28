import discord
from discord.ext.commands import Context, Greedy, command, has_permissions

from utils import Cog


class Moderation(Cog):
    """A cog for moderation commands"""

    def __init__(self, bot) -> None:
        super().__init__(bot)
        self.mod_log_channel = bot.get_channel(881412086041804811)

    async def mod_log(self, mod, member, action):  # Missing Access
        await self.mod_log_channel.send(
            embed=discord.Embed(
                description=f"{member.mention} has been {action} by {mod.mention}.",
                color=discord.Color.brand_red(),
            ).set_author(name=mod.display_name, icon_url=mod.display_avatar)
        )

    @command()
    @has_permissions(ban_members=True)
    async def ban(self, ctx: Context, members: Greedy[discord.Member], *, reason):
        """Ban the supplied members from the guild."""
        for member in members:
            await ctx.guild.ban(member, reason=reason)
        await ctx.send(
            f"Banned **{len(members)}** member{'s' if len(members) > 1 else ''}."
        )

    @command()
    @has_permissions(manage_messages=True)
    async def slowmode(self, ctx: Context, seconds: int = 0):
        """Set slowmode for the current channel."""
        if not 21600 > seconds > 0:
            await ctx.send("Slowmode should be between `21600` and `0` seconds.")
        else:
            await ctx.channel.edit(slowmode_delay=seconds)
            await ctx.send(
                f"Slowmode is now `{seconds}` second{'s' if seconds > 1 else ''}."
                if seconds > 0
                else "Slowmode is now disabled."
            )


def setup(bot):
    bot.add_cog(Moderation(bot))
