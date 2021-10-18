from contextlib import suppress
from re import compile as re_compile

import discord
from discord.ext import commands

from utils import Cog


class WelcomeView(discord.ui.View):
    def __init__(self, member: discord.Member):
        super().__init__()
        self.member = member
        self.used_by = []

    async def on_timeout(self):
        self.children[0].disabled = True
        await self.message.edit(view=self)

    @discord.ui.button(
        style=discord.ButtonStyle.green, label="Welcome", emoji="\U0001f44b"
    )
    async def welcome(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user == self.member:
            await interaction.response.send_message(
                "You can't welcome yourself.", ephemeral=True
            )
        elif interaction.user in self.used_by:
            await interaction.response.send_message(
                "You have already welcomed this member.", ephemeral=True
            )
        else:
            self.used_by.append(interaction.user)
            users = ", ".join(f"**{user.name}**" for user in self.used_by)
            self.embed.description = self.embed.description.split("\n")[0] + (
                f"\n\n{users} welcome {self.member.name}."
            )
            await self.message.edit(
                embed=self.embed,
            )
            await interaction.response.send_message(
                f"You welcomed {self.member}.", ephemeral=True
            )


class Events(Cog):
    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # AFK
        if message.author.id in self.bot.cache["afk"].keys():
            del self.bot.cache["afk"][message.author.id]
            await message.channel.send(
                f"Welcome back {message.author.display_name}! You're no longer AFK.",
                delete_after=4.0,
            )
            with suppress(discord.Forbidden):
                await message.author.edit(nick=message.author.display_name[6:])
        for mention in message.mentions:
            if msg := self.bot.cache["afk"].get(mention.id):
                await message.channel.send(f"{mention.display_name} is AFK: {msg}")

        # Pull requests and issues
        links = [
            f"<https://github.com/Pycord-Development/pycord/issues/{text[2:]}>"
            for text in message.content.split()
            if text.startswith("##") and len(text) > 2 and text[2:].isdigit()
        ]
        if links:
            await message.reply("\n".join(links))

    @Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, commands.CommandInvokeError):
            raise error
        await ctx.send(
            embed=discord.Embed(
                title=" ".join(
                    re_compile(r"[A-Z][a-z]*").findall(error.__class__.__name__)
                ),
                description=str(error),
                color=discord.Color.red(),
            )
        )

    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        view = WelcomeView(member)
        view.embed = discord.Embed(
            title="New Member",
            description=f"{member} joined the server :wave:\n\n",
            color=discord.Color.blurple(),
        ).set_thumbnail(url=member.display_avatar.url)
        view.message = await self.bot.main_guild.system_channel.send(
            embed=view.embed,
            view=view,
        )


def setup(bot):
    bot.add_cog(Events(bot))
