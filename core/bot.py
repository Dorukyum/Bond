from os import environ, getenv, makedirs
from traceback import format_exception

import discord
from aiohttp import ClientSession
from discord.ext import commands
from tortoise import Tortoise

from .context import Context
from .models import GuildModel, TagModel, WarnModel


class Bond(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            allowed_mentions=discord.AllowedMentions.none(),
            auto_sync_commands=False,
            chunk_guilds_at_startup=False,
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
        self.cache: dict[str, dict] = {"example_list": {}}

    async def setup_tortoise(self) -> None:
        makedirs("data", exist_ok=True)
        await Tortoise.init(
            db_url="sqlite://data/database.db", modules={"models": ["core.models"]}
        )
        await Tortoise.generate_schemas()

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        await self.setup_tortoise()
        return await super().start(token, reconnect=reconnect)

    async def close(self) -> None:
        await Tortoise.close_connections()
        return await super().close()

    async def get_application_context(
        self, interaction: discord.Interaction
    ) -> Context:
        return Context(self, interaction)

    @property
    def http_session(self) -> ClientSession:
        return self.http._HTTPClient__session  # type: ignore # it exists

    async def on_ready(self) -> None:
        self.errors_webhook = (
            discord.Webhook.from_url(
                webhook_url,
                session=self.http_session,
                bot_token=self.http.token,
            )
            if (webhook_url := getenv("ERRORS_WEBHOOK"))
            else None
        )
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
            if self.errors_webhook and not isinstance(error, discord.DiscordException):
                await ctx.respond(
                    "An unexpected error has occured and I've notified my developer. "
                    "In the meantime, consider joining my support server.",
                    view=discord.ui.View(
                        discord.ui.Button(
                            label="Support", url="https://discord.gg/8JsMVhBP4W"
                        ),
                        discord.ui.Button(
                            label="GitHub Repo",
                            url="https://github.com/Dorukyum/Bond",
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
        if data := await GuildModel.get_or_none(id=guild.id):
            await data.delete()
        for data in await TagModel.filter(id=guild.id):
            await data.delete()
        for data in await WarnModel.filter(id=guild.id):
            await data.delete()

    def run(
        self, debug: bool = False, cogs: list[str] | None = None, sync: bool = False
    ) -> None:
        self.load_extensions("jishaku", *cogs or ("cogs", "cogs.developer"))
        if sync:

            async def on_connect() -> None:
                await self.sync_commands(delete_existing=not debug)
                print("Synchronized commands.")

            self.on_connect = on_connect

        environ.setdefault("JISHAKU_NO_UNDERSCORE", "1")
        if debug:
            return super().run(getenv("DEBUG_TOKEN", getenv("TOKEN")))

        environ.setdefault("JISHAKU_HIDE", "1")
        super().run(getenv("TOKEN"))
