import discord
from discord.ext.commands import Context, command, group

from utils import Cog, Lowercase, TagModel, s


class Tags(Cog):
    """A cog for commands related to tags."""

    @group(invoke_without_command=True)
    async def tag(self, ctx: Context, *, name: Lowercase):
        """View a tag's content."""
        if tag := await TagModel.filter(name=name, guild_id=ctx.guild.id).first():
            await ctx.reply(tag.content)
            await tag.update_from_dict({"uses": tag.uses + 1}).save()
        else:
            await ctx.reply("A tag with this name doesn't exist.")

    @tag.command()
    async def create(self, ctx: Context, name: Lowercase, *, content):
        """Create a tag."""
        if await TagModel.filter(name=name, guild_id=ctx.guild.id).first():
            await ctx.reply("A tag with this name already exists.")
        else:
            await TagModel.create(
                name=name,
                content=content,
                author_id=ctx.author.id,
                guild_id=ctx.guild.id,
                uses=0,
            )
            await ctx.reply(f"Tag `{name}` created successfully.")

    @tag.command()
    async def edit(self, ctx: Context, name: Lowercase, *, content):
        """Edit the content of a tag."""
        if tag := await TagModel.filter(name=name, guild_id=ctx.guild.id).first():
            if (
                tag.author_id == ctx.author.id
                or ctx.channel.permissions_for(ctx.author).manage_messages
            ):
                await tag.update_from_dict({"content": content}).save()
                await ctx.reply(f"Tag `{name}` edited successfully.")
            else:
                await ctx.reply("You dont own this tag.")
        else:
            await ctx.reply("A tag with this name doesn't exist.")

    @tag.command()
    async def delete(self, ctx: Context, *, name: Lowercase):
        """Delete a tag."""
        if tag := await TagModel.filter(name=name, guild_id=ctx.guild.id).first():
            if (
                tag.author_id == ctx.author.id
                or ctx.channel.permissions_for(ctx.author).manage_messages
            ):
                await tag.delete()
                await ctx.reply(f"Tag `{name}` deleted successfully.")
            else:
                await ctx.reply("You dont own this tag.")
        else:
            await ctx.reply("A tag with this name doesn't exist.")

    @tag.command()
    async def transfer(
        self, ctx: Context, name: Lowercase, member: discord.Member = None
    ):
        """Transfer a tag's ownership."""
        if tag := await TagModel.filter(name=name, guild_id=ctx.guild.id).first():
            if tag.author_id == ctx.author.id:
                await tag.update_from_dict({"author_id": member.id}).save()
                await ctx.send(f"Tag `{name}` transferred to {member} successfully.")
            else:
                await ctx.reply("You dont own this tag.")
        else:
            await ctx.reply("A tag with this name doesn't exist.")

    @tag.command()
    async def rename(self, ctx: Context, name: Lowercase, *, new_name: Lowercase):
        """Rename a tag."""
        if tag := await TagModel.filter(name=name, guild_id=ctx.guild.id).first():
            if tag.author_id == ctx.author.id:
                if await TagModel.filter(name=new_name, guild_id=ctx.guild.id):
                    await ctx.send("A tag with this name already exists.")
                else:
                    await tag.update_from_dict({"name": new_name}).save()
                    await ctx.send(
                        f"Tag `{name}` renamed to `{new_name}` successfully."
                    )
            else:
                await ctx.reply("You dont own this tag.")
        else:
            await ctx.reply("A tag with this name doesn't exist.")

    @tag.command()
    async def info(self, ctx: Context, *, name: Lowercase):
        """View info about a tag."""
        if tag := await TagModel.filter(name=name, guild_id=ctx.guild.id).first():
            owner = self.bot.get_user(tag.author_id) or await self.bot.fetch_user(
                tag.author_id
            )
            await ctx.send(
                embed=discord.Embed(title=tag.name, color=discord.Color.blurple())
                .add_field(name="Owner", value=owner.mention)
                .add_field(name="Uses", value=tag.uses)
                .add_field(
                    name="Created At", value=discord.utils.format_dt(tag.created_at)
                )
            )
        else:
            await ctx.reply("A tag with this name doesn't exist.")

    @tag.command()
    async def raw(self, ctx: Context, *, name: Lowercase):
        """View the content of a tag, with escaped markdown."""
        if tag := await TagModel.filter(name=name, guild_id=ctx.guild.id).first():
            await ctx.send(discord.utils.escape_markdown(tag.content))
        else:
            await ctx.reply("A tag with this name doesn't exist.")

    @tag.command()
    async def claim(self, ctx: Context, *, name: Lowercase):
        """Claim a tag."""
        if tag := await TagModel.filter(name=name, guild_id=ctx.guild.id).first():
            if ctx.guild.get_member(tag.author_id):
                await ctx.reply("The author of this tag is still in the server.")
            else:
                await tag.update_from_dict({"author_id": ctx.author.id}).save()
                await ctx.reply("Successfully claimed tag.")
        else:
            await ctx.reply("A tag with this name doesn't exist.")

    @tag.command()
    async def search(self, ctx: Context, *, query):
        """Search the guild's tags."""
        if tags := await TagModel.filter(guild_id=ctx.guild.id):
            await ctx.send(
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
            await ctx.reply("This server has no tags.")

    @command(name="tags")
    async def _tags(self, ctx: Context, member: discord.Member = None):
        """View the guild's tags.
        Shows the tags of a member if supplied."""
        if member:
            if tags := await TagModel.filter(
                guild_id=ctx.guild.id, author_id=member.id
            ):
                await ctx.send(
                    embed=discord.Embed(
                        title=f"{member.display_name}'{s(member.display_name)} Tags",
                        description="\n".join(
                            f"{i+1}. {tag.name}" for i, tag in enumerate(tags)
                        ),
                        color=discord.Color.blurple(),
                    )
                )
            else:
                await ctx.reply("This member does not have any tags in this server.")
        elif tags := await TagModel.filter(guild_id=ctx.guild.id):
            await ctx.send(
                embed=discord.Embed(
                    title=f"Tags in {ctx.guild.name}",
                    description="\n".join(
                        f"{i+1}. {tag.name}" for i, tag in enumerate(tags)
                    ),
                    color=discord.Color.blurple(),
                )
            )
        else:
            await ctx.reply("This server does not have any tags.")

    async def cog_check(self, ctx) -> bool:
        return ctx.guild is not None


def setup(bot):
    bot.add_cog(Tags(bot))
