from contextlib import suppress
from datetime import timedelta
from tortoise.exceptions import ConfigurationError
from typing import Union

import discord
from discord import ApplicationContext

from core import Cog, GuildModel


class Automod(Cog):
    """A cog for the automoderation system."""

    async def automod_on(self, target: Union[discord.Message, discord.Member]) -> bool:
        """Returns whether or not the target should be automodded."""
        with suppress(ConfigurationError):
            return bool(
                not getattr(target, "bot", False)
                and target.guild
                and (guild := await GuildModel.get_or_none(id=target.guild.id))
                and guild.automod
            )

    @discord.slash_command()
    @discord.guild_only()
    @discord.default_permissions(manage_guild=True)
    @discord.option(
        "status",
        description="Turn automod on or off.",
        choices=["On", "Off"],
    )
    async def automod(self, ctx: ApplicationContext, status: str):
        """Toggle automoderation for this server."""
        guild, _ = await GuildModel.get_or_create(id=ctx.guild_id)
        as_bool = status == "On"
        if guild.automod == as_bool:
            return await ctx.respond(f"Automod is already {status.lower()}.")

        await guild.update_from_dict({"automod": as_bool}).save()
        await ctx.respond(f"Automod is now {status.lower()}.")

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
            if age.days < 28:
                until = timedelta(minutes=5) + member.joined_at
                await member.timeout(
                    until, reason=f"Automod: Young account ({age.days} days)"
                )
                with suppress(discord.HTTPException):
                    await member.send(
                        f"You have been timed out for security reasons. You will be able to speak <t:{int(until.timestamp())}:R>."
                    )


def setup(bot):
    bot.add_cog(Automod(bot))
