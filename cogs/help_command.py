import discord
from discord.ext import commands

COLOR = discord.Color.blurple()


async def get_cog_help(cog: commands.Cog, ctx: commands.Context) -> discord.Embed:
    cog = ctx.bot.get_cog(cog)
    embed = discord.Embed(color=COLOR)
    embed.title = cog.__cog_name__ + " Commands"
    embed.description = "\n".join(
        f"`{command.name}`: {command.help}"
        for command in cog.get_commands()
        if not isinstance(command, discord.ApplicationCommand)
    )
    embed.description = f"For more info on a command: `{ctx.clean_prefix}help <command>`\n\n**Commands:**\n{embed.description}"
    return embed


class HelpSelect(discord.ui.Select):
    def __init__(self, options, ctx):
        super().__init__(placeholder="Choose a category", options=options)
        self.context = ctx

    async def callback(self, i):
        await i.response.send_message(
            embed=await get_cog_help(self.values[0], self.context), ephemeral=True
        )


class HelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        bot = self.context.bot
        embed = discord.Embed(
            title=bot.user.name,
            description="The ultimate open source server management bot. Use the menu below to navigate through the command list.",
            colour=COLOR,
        )
        embed.set_thumbnail(url=bot.user.avatar.url)
        embed.add_field(name="Server Count", value=len(bot.guilds))
        embed.add_field(name="User Count", value=len(bot.users))
        embed.add_field(name="Ping", value=f"{bot.latency*1000:.2f}ms")

        options = [
            discord.SelectOption(
                label=cog.__cog_name__,
                value=cog.__cog_name__,
                description=cog.__doc__,
            )
            for cog, commands in mapping.items()
            if cog
            and commands
            and cog.__cog_name__ not in ["Jishaku", "Pycord", "Developer"]
        ]

        view = discord.ui.View()
        view.add_item(HelpSelect(options, self.context))
        async def timeoutfunc(interaction):
          view.disable_all_items() 
        view.on_timeout = timeoutfunc

        await self.context.send(embed=embed, view=view)

    async def send_cog_help(self, cog: commands.Cog):
        await self.context.send(embed=get_cog_help(cog.__cog_name__, self.context))

    async def send_group_help(self, group: commands.Group):
        embed = discord.Embed(title=group.name, description=group.help, color=COLOR)
        embed.add_field(
            name="Usage",
            value=f"{self.context.prefix}{group.name} {group.signature}",
        )
        if len(group.commands):
            embed.add_field(
                name="Subcommands",
                value=", ".join(i.name for i in group.commands if not i.hidden),
                inline=False,
            )
        await self.context.send(embed=embed)

    async def send_command_help(self, command: commands.Command):
        embed = discord.Embed(
            title=command.name,
            description=command.short_doc,
            color=COLOR,
        )
        embed.add_field(
            name="Usage",
            value=f"{self.context.prefix}{command.name} {command.signature}",
        )
        await self.context.send(embed=embed)


def setup(bot):
    bot._default_help_command = bot.help_command
    bot.help_command = HelpCommand()


def teardown(bot):
    bot.help_command = bot._default_help_command
