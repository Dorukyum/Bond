from contextlib import suppress
from datetime import timedelta

import discord
from discord.ext.commands import command, Context, has_permissions

from utils import Cog, GuildModel


class Automod(Cog):
    """A cog for the automoderation system."""

    async def automod_on(self, target):
        """Returns whether or not the target should be automodded."""
        if hasattr(target, "bot") and target.bot:
            return False
        return (
            target.guild
            and (await GuildModel.get_or_create(id=target.guild.id))[0].automod
        )

    @command(name="automod")
    @has_permissions(manage_guild=True)
    async def _automod(self, ctx: Context, status: bool):
        guild, _ = await GuildModel.get_or_create(id=ctx.guild.id)
        as_text = {True: "on", False: "off"}[status]
        if guild.automod == status:
            return await ctx.send(f"Automod is already {as_text}.")

        guild.automod = status
        await guild.save()
        await ctx.send(f"Automod turned {as_text}.")

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if await self.automod_on(message):
            mentions = len(message.raw_mentions)
            if mentions >= 7 not in message.author.roles:
                await message.delete()
                if mentions >= 25:
                    return await message.guild.ban(
                        message.author, reason=f"Too many mentions ({mentions})"
                    )

                await message.channel.send(
                    f"{message.author.mention} Too many mentions."
                )
                duration = min(mentions * 15, 40320)
                await message.author.timeout_for(
                    timedelta(minutes=duration),
                    reason=f"Too many mentions ({mentions})",
                )

    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if await self.automod_on(member):
            age = member.joined_at - member.created_at
            if age.days < 56:
                until = (
                    timedelta(minutes=5) if age.days < 28 else timedelta(minutes=3)
                ) + member.joined_at
                await member.timeout(until, reason=f"Young account ({age.days} days)")
                with suppress(discord.HTTPException):
                    await member.send(
                        f"You have been timed out for security reasons. You will be able to speak <t:{int(until.timestamp())}:R>."
                    )

def setup(bot):
    bot.add_cog(Automod(bot))
