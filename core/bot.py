from os import environ, getenv
from sys import argv
from traceback import format_exception
from typing import Dict

import discord
from aiohttp import ClientSession
from discord.ext import commands
from tortoise import Tortoise

from .context import Context
from .models import GuildModel


class Toolkit(commands.Bot):
    on_ready_fired: bool = False
    cache: Dict[str, Dict] = {"afk": {}, "example_list": {}}

    def __init__(self):
        super().__init__(
            activity=discord.Activity(
                type=discord.ActivityType.listening, name=f"/help"
            ),
            allowed_mentions=discord.AllowedMentions.none(),
            chunk_guilds_at_startup=False,
            command_prefix="t." if "-t" not in argv else "d.",
            help_command=None,
            intents=discord.Intents(
                members=True,
                messages=True,
                message_content=True,
                guilds=True,
                bans=True,
            ),
            owner_ids=[543397958197182464],
        )

        for cog in [
            "jishaku",
            "cogs.automod",
            "cogs.developer",
            "cogs.dropdown_roles",
            "cogs.fun",
            "cogs.general",
            "cogs.help",
            "cogs.moderation",
            "cogs.modlogs",
            "cogs.owner",
            "cogs.pycord",
            "cogs.tags",
            "cogs.warnings",
        ]:
            self.load_cog(cog)

    @property
    def http_session(self) -> ClientSession:
        return self.http._HTTPClient__session

    def load_cog(self, cog: str) -> None:
        try:
            self.load_extension(cog)
        except Exception as e:
            e = getattr(e, "original", e)
            print("".join(format_exception(type(e), e, e.__traceback__)))

    async def on_connect(self) -> None:
        if "-s" in argv:
            await self.sync_commands()
            print("Synchronized commands.")

    async def on_ready(self):
        if self.on_ready_fired:
            return
        self.on_ready_fired = True

        self.errors_webhook = discord.Webhook.from_url(
            getenv("ERRORS_WEBHOOK"),
            session=self.http_session,
            bot_token=self.http.token,
        )
        environ.setdefault("JISHAKU_HIDE", "1")
        environ.setdefault("JISHAKU_NO_UNDERSCORE", "1")

        await Tortoise.init(
            db_url="sqlite://data/database.db", modules={"models": ["core.models"]}
        )
        await Tortoise.generate_schemas()
        print(self.user, "is ready")

    async def on_application_command_error(self, ctx: Context, error: Exception):
        if isinstance(error, discord.ApplicationCommandInvokeError):
            if isinstance((error := error.original), discord.HTTPException):
                message = (
                    "An HTTP exception has occured: "
                    f"{error.status} {error.__class__.__name__}"
                )
                if error.text:
                    message += f": {error.text}"
                return await ctx.respond(message)
            if not isinstance(error, discord.DiscordException):
                await ctx.respond(
                    "An unexpected error has occured and I've notified my developer. "
                    "In the meantime, consider joining my support server.",
                    view=discord.ui.View(
                        discord.ui.Button(
                            label="Support", url="https://discord.gg/8JsMVhBP4W"
                        ),
                        discord.ui.Button(
                            label="GitHub Repo",
                            url="https://github.com/Dorukyum/Toolkit",
                        ),
                    ),
                )
                header = f"Command: `/{ctx.command.qualified_name}`"
                if ctx.guild is not None:
                    header += f" | Guild: `{ctx.guild.name} ({ctx.guild_id})`"
                return await self.errors_webhook.send(
                    f"{header}\n```\n{''.join(format_exception(type(error), error, error.__traceback__))}```"
                )

        await ctx.respond(
            embed=discord.Embed(
                title=error.__class__.__name__,
                description=str(error),
                color=discord.Color.red(),
            )
        )

    async def on_message_edit(
        self, before: discord.Message, after: discord.Message
    ) -> None:
        if before.content != after.content:
            await self.process_commands(after)

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        if saved := await GuildModel.get_or_none(id=guild.id):
            await saved.delete()

    async def get_application_context(
        self, interaction: discord.Interaction
    ) -> Context:
        return Context(self, interaction)

    def run(self):
        super().run(getenv("TOKEN"))
