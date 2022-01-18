import discord
from discord.ext.commands import Context, command, group

from utils import Cog, Lowercase, Tagmodew, s


class Tags(Cog):
    """A cog fow commands wewated tuwu tags."""

    @group(invoke_without_command=True)
    async def tag(self, ctx: Context, *, name: Lowercase):
        """View a tag's content."""
        if tag := await Tagmodew.filter(name=name, guild_id=ctx.guild.id).first():
            await ctx.reply(tag.content)
            await tag.update_from_dict({"uses": tag.uses + 1}).save()
        else:
            await ctx.reply("A tag with thiws nawme doesn't exist.")

    @tag.command()
    async def cweate(self, ctx: Context, name: Lowercase, *, content):
        """Cweate a tag."""
        if await Tagmodew.filter(name=name, guild_id=ctx.guild.id).first():
            await ctx.reply("A tag with thiws nawme awweady exists.")
        else:
            await Tagmodew.create(
                name=name,
                content=content,
                author_id=ctx.author.id,
                guild_id=ctx.guild.id,
                uses=0,
            )
            await ctx.reply(f"Tag `{name}` cweated successfuwwy.")

    @tag.command()
    async def edit(self, ctx: Context, name: Lowercase, *, content):
        """Edit the content of a tag."""
        if tag := await Tagmodew.filter(name=name, guild_id=ctx.guild.id).first():
            if (
                tag.author_id == ctx.author.id
                or ctx.channel.permissions_for(ctx.author).manage_messages
            ):
                await tag.update_from_dict({"content": content}).save()
                await ctx.reply(f"Tag `{name}` edited successfuwwy.")
            else:
                await ctx.reply("Uwu dont own thiws tag.")
        else:
            await ctx.reply("A tag with thiws nawme doesn't exist.")

    @tag.command()
    async def dewete(self, ctx: Context, *, name: Lowercase):
        """Dewete a tag."""
        if tag := await Tagmodew.filter(name=name, guild_id=ctx.guild.id).first():
            if (
                tag.author_id == ctx.author.id
                or ctx.channel.permissions_for(ctx.author).manage_messages
            ):
                await tag.delete()
                await ctx.reply(f"Tag `{name}` deweted successfuwwy.")
            else:
                await ctx.reply("Uwu dont own thiws tag.")
        else:
            await ctx.reply("A tag with thiws nawme doesn't exist.")

    @tag.command()
    async def twansfew(self, ctx: Context, name: Lowercase, member: discord.Member = None):
        """Twansfew a tag's ownewship."""
        if tag := await Tagmodew.filter(name=name, guild_id=ctx.guild.id).first():
            if tag.author_id == ctx.author.id:
                await tag.update_from_dict({"author_id": member.id}).save()
                await ctx.send(f"Tag `{name}` twansfewwed tuwu {member} successfuwwy.")
            else:
                await ctx.reply("Uwu dont own thiws tag.")
        else:
            await ctx.reply("A tag with thiws nawme doesn't exist.")

    @tag.command()
    async def wename(self, ctx: Context, name: Lowercase, *, new_name: Lowercase):
        """Wename a tag."""
        if tag := await Tagmodew.filter(name=name, guild_id=ctx.guild.id).first():
            if tag.author_id == ctx.author.id:
                if await Tagmodew.filter(name=new_name, guild_id=ctx.guild.id):
                    await ctx.send("A tag with thiws nawme awweady exists.")
                else:
                    await tag.update_from_dict({"name": new_name}).save()
                    await ctx.send(
                        f"Tag `{name}` wenamed tuwu `{new_name}` successfuwwy."
                    )
            else:
                await ctx.reply("Uwu dont own thiws tag.")
        else:
            await ctx.reply("A tag with thiws nawme doesn't exist.")

    @tag.command()
    async def info(self, ctx: Context, *, name: Lowercase):
        """View info about a tag."""
        if tag := await Tagmodew.filter(name=name, guild_id=ctx.guild.id).first():
            owner = self.bot.get_user(tag.author_id) or await self.bot.fetch_user(
                tag.author_id
            )
            await ctx.send(
                embed=discord.Embed(title=tag.name, color=discord.Color.blurple())
                .add_field(name="Ownew", value=owner.mention)
                .add_field(name="Uses", value=tag.uses)
                .add_field(
                    name="Cweated at", value=discord.utils.format_dt(tag.created_at)
                )
            )
        else:
            await ctx.reply("A tag with thiws nawme doesn't exist.")

    @tag.command()
    async def waw(self, ctx: Context, *, name: Lowercase):
        """View the content of a tag, with escaped mawkdown."""
        if tag := await Tagmodew.filter(name=name, guild_id=ctx.guild.id).first():
            await ctx.send(discord.utils.escape_markdown(tag.content))
        else:
            await ctx.reply("A tag with thiws nawme doesn't exist.")

    @tag.command()
    async def cwaim(self, ctx: Context, *, name: Lowercase):
        """Cwaim a tag."""
        if tag := await Tagmodew.filter(name=name, guild_id=ctx.guild.id).first():
            if ctx.guild.get_member(tag.author_id):
                await ctx.reply("The authow of thiws tag iws stiww in the sewvew.")
            else:
                await tag.update_from_dict({"author_id": ctx.author.id}).save()
                await ctx.reply("Successfuwwy cwaimed tag.")
        else:
            await ctx.reply("A tag with thiws nawme doesn't exist.")

    @tag.command()
    async def seawch(self, ctx: Context, *, query):
        """Seawch the guiwd's tags."""
        if tags := await Tagmodew.filter(guild_id=ctx.guild.id):
            await ctx.send(
                embed=discord.Embed(
                    title=f"Tag seawch | {query}",
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
            await ctx.reply("Thiws sewvew has no tags.")

    @command(name="tags")
    async def _tags(self, ctx: Context, member: discord.Member = None):
        """View the guiwd's tags.
            shows the tags of a membew if suppwied."""
        if member:
            if tags := await Tagmodew.filter(guild_id=ctx.guild.id, author_id=member.id):
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
                await ctx.reply("Thiws membew does nowt have any tags in thiws sewvew.")
        elif tags := await Tagmodew.filter(guild_id=ctx.guild.id):
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
            await ctx.reply("Thiws sewvew does nowt have any tags.")

    async def cog_check(self, ctx) -> bool:
        return ctx.guild is not None


def setup(bot):
    bot.add_cog(Tags(bot))
