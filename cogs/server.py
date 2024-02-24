import discord
from discord.utils import get
from aiohttp import InvalidURL
from io import BytesIO

from core import Cog, Context, GuildModel


class Server(Cog):
    """Commands related to server settings."""

    emoji = discord.SlashCommandGroup(
        "emoji",
        "Commands related to emojis.",
        guild_only=True,
        default_member_permissions=discord.Permissions(manage_guild=True),
    )

    @emoji.command(name="add")
    @discord.option("name", description="The name of the emoji.")
    @discord.option("url", description="The image url of the emoji.")
    async def emoji_add(self, ctx: Context, name: str, url: str):
        """Add a custom emoji to this guild."""
        assert ctx.guild
        await ctx.assert_permissions(manage_emojis=True)
        try:
            async with self.bot.http_session.get(url) as res:
                if 300 > res.status >= 200:
                    emoji = await ctx.guild.create_custom_emoji(
                        name=name, image=BytesIO(await res.read()).getvalue()
                    )
                    await ctx.respond(f"{emoji} Successfully created emoji.")
                else:
                    await ctx.respond(
                        f"An HTTP error has occured while fetching the image: {res.status} {res.reason}"
                    )
        except InvalidURL:
            await ctx.respond("You have provided an invalid URL.", ephemeral=True)

    @emoji.command(name="delete")
    @discord.option("name", description="The name of the emoji to delete.")
    @discord.option(
        "reason", str, description="The reason to delete the emoji.", default=None
    )
    async def emoji_delete(
        self,
        ctx: Context,
        name: str,
        reason: str | None,
    ):
        """Delete a custom emoji from this guild."""
        assert ctx.guild
        await ctx.assert_permissions(manage_emojis=True)
        if emoji := get(ctx.guild.emojis, name=name):
            await emoji.delete(reason=reason)
            return await ctx.respond(f"Successfully deleted emoji `:{name}:`.")
        await ctx.respond(f'No emoji named "{name}" found.')

    suggestions = discord.SlashCommandGroup(
        "suggestions",
        "Commands related to member suggestions.",
        guild_only=True,
        default_member_permissions=discord.Permissions(manage_guild=True),
    )

    @suggestions.command(name="set")
    @discord.option(
        "channel",
        description="The channel new member suggestions will be sent to.",
    )
    async def suggestions_set(self, ctx: Context, channel: discord.TextChannel):
        """Set the channel for member suggestions."""
        await GuildModel.update_or_create(
            id=ctx.guild_id, defaults={"suggestions": channel.id}
        )
        await ctx.respond(f"Member suggestions will now be sent to {channel.mention}.")

    @suggestions.command(name="disable")
    async def suggestions_disable(self, ctx: Context):
        """Disable member suggestions."""
        if (
            guild := await GuildModel.filter(id=ctx.guild_id)
            .exclude(suggestions=0)
            .first()
        ):
            await guild.update_from_dict({"suggestions": 0}).save()
            return await ctx.respond(
                "Member suggestions have been disabled for this server."
            )
        await ctx.respond("Member suggestions are already disabled for this server.")

    @discord.slash_command()
    @discord.guild_only()
    @discord.option("suggestion", description="The suggestion.")
    async def suggest(self, ctx: Context, *, suggestion: str):
        """Make a suggestion for the server. This will be sent to the channel set by the server managers."""
        await ctx.assert_permissions(external_emojis=True)
        assert ctx.guild
        if not (channel := await GuildModel.get_text_channel(ctx.guild, "suggestions")):
            return await ctx.respond("This server doesn't have a suggestions channel.")

        msg = await channel.send(
            embed=discord.Embed(
                description=suggestion,
                colour=discord.Color.blurple(),
            )
            .set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
            .set_footer(text=f"ID: {ctx.author.id}")
        )
        await msg.add_reaction("<:upvote:881521766231584848>")
        await msg.add_reaction("<:downvote:904068725475508274>")
        await ctx.success(
            "Suggestion Sent",
            f"Your suggestion has been sent to {channel.mention}.",
            ephemeral=True,
        )

def setup(bot):
    bot.add_cog(Server(bot))
