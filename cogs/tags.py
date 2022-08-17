from typing import Optional
import discord

from core import Cog, Context, Lowercase, TagModel, s


class Tags(Cog):
    """Commands related to tags."""

    tag = discord.SlashCommandGroup("tag", "Commands related to tags.", guild_only=True)

    @tag.command()
    @discord.option("name", description="The name of the tag to view.")
    async def view(self, ctx: Context, *, name: Lowercase):
        """View a tag's content."""
        if tag := await TagModel.get_or_none(name=name, guild_id=ctx.guild_id):
            await ctx.respond(tag.content)
            await tag.update_from_dict({"uses": tag.uses + 1}).save()
        else:
            await ctx.respond("A tag with this name doesn't exist.")

    @tag.command()
    @discord.option("name", description="The name of the tag to create.")
    @discord.option("content", description="The content of the tag to create.")
    async def create(self, ctx: Context, name: Lowercase, *, content: str):
        """Create a tag."""
        if await TagModel.exists(name=name, guild_id=ctx.guild_id):
            await ctx.respond("A tag with this name already exists.")
        else:
            await TagModel.create(
                name=name,
                content=content,
                author_id=ctx.author.id,
                guild_id=ctx.guild_id,
                uses=0,
            )
            await ctx.respond(f"Tag `{name}` created successfully.")

    @tag.command()
    @discord.option("name", description="The name of the tag to edit.")
    @discord.option("content", description="The new content of the tag.")
    async def edit(self, ctx: Context, name: Lowercase, *, content: str):
        """Edit the content of a tag."""
        if tag := await TagModel.get_or_none(name=name, guild_id=ctx.guild_id):
            if (
                tag.author_id == ctx.author.id
                or ctx.channel.permissions_for(ctx.author).manage_messages
            ):
                await tag.update_from_dict({"content": content}).save()
                await ctx.respond(f"Tag `{name}` edited successfully.")
            else:
                await ctx.respond("You don't own this tag.")
        else:
            await ctx.respond("A tag with this name doesn't exist.")

    @tag.command()
    @discord.option(
        "name",
        description="The name of the tag to delete. You must own the tag to be able to delete it.",
    )
    async def delete(self, ctx: Context, *, name: Lowercase):
        """Delete a tag."""
        if tag := await TagModel.get_or_none(name=name, guild_id=ctx.guild_id):
            if (
                tag.author_id == ctx.author.id
                or ctx.channel.permissions_for(ctx.author).manage_messages
            ):
                await tag.delete()
                await ctx.respond(f"Tag `{name}` deleted successfully.")
            else:
                await ctx.respond("You don't own this tag.")
        else:
            await ctx.respond("A tag with this name doesn't exist.")

    @tag.command()
    @discord.option("name", description="The name of the tag to transfer.")
    @discord.option(
        "member", description="The member to transfer ownership of the tag to."
    )
    async def transfer(
        self, ctx: Context, name: Lowercase, member: discord.Member
    ):
        """Transfer a tag's ownership."""
        if tag := await TagModel.get_or_none(name=name, guild_id=ctx.guild_id):
            if tag.author_id == ctx.author.id:
                await tag.update_from_dict({"author_id": member.id}).save()
                await ctx.respond(f"Tag `{name}` transferred to {member} successfully.")
            else:
                await ctx.respond("You don't own this tag.")
        else:
            await ctx.respond("A tag with this name doesn't exist.")

    @tag.command()
    @discord.option("name", description="The current name of the tag to rename.")
    @discord.option("new_name", description="The new name of the tag.")
    async def rename(
        self, ctx: Context, name: Lowercase, *, new_name: Lowercase
    ):
        """Rename a tag."""
        if tag := await TagModel.get_or_none(name=name, guild_id=ctx.guild_id):
            if tag.author_id == ctx.author.id:
                if await TagModel.filter(name=new_name, guild_id=ctx.guild_id):
                    await ctx.respond("A tag with this name already exists.")
                else:
                    await tag.update_from_dict({"name": new_name}).save()
                    await ctx.respond(
                        f"Tag `{name}` renamed to `{new_name}` successfully."
                    )
            else:
                await ctx.respond("You don't own this tag.")
        else:
            await ctx.respond("A tag with this name doesn't exist.")

    @tag.command()
    @discord.option(
        "name", description="The name of the tag to view information about."
    )
    async def info(self, ctx: Context, *, name: Lowercase):
        """View information about a tag."""
        if tag := await TagModel.get_or_none(name=name, guild_id=ctx.guild_id):
            owner = self.bot.get_user(tag.author_id) or await self.bot.fetch_user(
                tag.author_id
            )
            await ctx.respond(
                embed=discord.Embed(title=tag.name, color=discord.Color.blurple())
                .add_field(name="Owner", value=owner.mention)
                .add_field(name="Uses", value=tag.uses)
                .add_field(
                    name="Created At", value=discord.utils.format_dt(tag.created_at)
                )
            )
        else:
            await ctx.respond("A tag with this name doesn't exist.")

    @tag.command()
    @discord.option(
        "name", description="The name of the tag to view with escaped markdown."
    )
    async def raw(self, ctx: Context, *, name: Lowercase):
        """View the content of a tag, with escaped markdown."""
        if tag := await TagModel.get_or_none(name=name, guild_id=ctx.guild_id):
            await ctx.respond(discord.utils.escape_markdown(tag.content))
        else:
            await ctx.respond("A tag with this name doesn't exist.")

    @tag.command()
    @discord.option("name", description="The name of the tag to claim.")
    async def claim(self, ctx: Context, *, name: Lowercase):
        """Claim a tag."""
        if tag := await TagModel.get_or_none(name=name, guild_id=ctx.guild_id):
            if ctx.guild.get_member(tag.author_id):
                await ctx.respond("The author of this tag is still in the server.")
            else:
                await tag.update_from_dict({"author_id": ctx.author.id}).save()
                await ctx.respond("Successfully claimed tag.")
        else:
            await ctx.respond("A tag with this name doesn't exist.")

    @tag.command()
    @discord.option("query", description="The query to use while searching tags.")
    async def search(self, ctx: Context, *, query: str):
        """Search the guild's tags."""
        if tags := await TagModel.filter(guild_id=ctx.guild_id):
            await ctx.respond(
                embed=discord.Embed(
                    title=f"Tag Search | {query}",
                    description="\n".join(
                        f"{i+1}. {name}"
                        for i, name in enumerate(
                            tag.name for tag in tags if query in tag.name
                        )
                    ),
                    color=discord.Color.blurple(),
                )
            )
        else:
            await ctx.respond("This server has no tags.")

    @tag.command(name="list")
    @discord.option(
        "member",
        discord.Member,
        description="The member to list the tags of.",
        default=None,
    )
    async def tag_list(self, ctx: Context, member: Optional[discord.Member]):
        """List the tags of a member or all tags created in this server."""
        if member:
            if tags := await TagModel.filter(
                guild_id=ctx.guild_id, author_id=member.id
            ):
                await ctx.respond(
                    embed=discord.Embed(
                        title=f"{member.display_name}'{s(member.display_name)} Tags",
                        description="\n".join(
                            f"{i+1}. {tag.name}" for i, tag in enumerate(tags)
                        ),
                        color=discord.Color.blurple(),
                    )
                )
            else:
                await ctx.respond("This member does not have any tags in this server.")
        elif tags := await TagModel.filter(guild_id=ctx.guild_id):
            await ctx.respond(
                embed=discord.Embed(
                    title=f"Tags in {ctx.guild.name}",
                    description="\n".join(
                        f"{i+1}. {tag.name}" for i, tag in enumerate(tags)
                    ),
                    color=discord.Color.blurple(),
                )
            )
        else:
            await ctx.respond("This server does not have any tags.")


def setup(bot):
    bot.add_cog(Tags(bot))
