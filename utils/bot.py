from os import environ, getenv, path
from sys import argv
from json import load, dump
from traceback import format_exception
from typing import Dict, Optional

import discord
from discord.errors import ExtensionFailed
from discord.ext import commands
from tortoise import Tortoise


class PycordManager(commands.Bot):
    on_ready_fired: bool = False
    cache: Dict[str, Dict] = {"afk": {}, "unmute_task": {}, "example_list": {}}

    def __init__(self):
        config = self.load_config()
        prefix = config["prefix"] if "-t" not in argv else "d."

        super().__init__(
            command_prefix=prefix,
            intents=discord.Intents(
                members=True,
                messages=True,
                message_content=True,
                guilds=True,
                bans=True,
            ),
            owner_ids=config["owner_ids"],
            help_command=commands.MinimalHelpCommand(),
            allowed_mentions=discord.AllowedMentions.none(),
            activity=discord.Activity(
                type=discord.ActivityType.listening, name=f"{config['prefix']}help"
            ),
        )

        self.to_load = [
            "jishaku",
            "cogs.help_command",
            "cogs.developer",
            "cogs.fun",
            "cogs.gitlink",
        ]
        for cog in [
            "cogs.automod",
            "cogs.general",
            "cogs.moderation",
            "cogs.modlogs",
            "cogs.pycord",
            "cogs.tags",
            "cogs.warnings",
        ]:  # cogs with application commands
            self.load_cog(cog)

    @property
    def http_session(self):
        return self.http._HTTPClient__session

    def load_cog(self, cog: str) -> None:
        try:
            self.load_extension(cog)
        except ExtensionFailed as e:
            print("".join(format_exception(e.original)))
        except Exception as e:
            print("".join(format_exception(e)))

    def load_config(self, update: bool = True) -> dict:
        if not path.exists("config.json"):
            config = {}
        else:
            with open("config.json", "r") as f:
                config: dict = load(f)

        config.setdefault("debug_guilds", [881207955029110855])
        config.setdefault("owner_ids", [543397958197182464])
        config.setdefault("prefix", "p.")

        if update:
            self.config = config
        return config

    def dump_config(self, new_data: Optional[dict] = None) -> None:
        self.config.update(new_data)
        with open("config.json", "w") as f:
            dump(self.config, f)

    async def on_connect(self) -> None:
        if "-s" in argv:
            await self.sync_commands()
            print("Synchronized commands.")

    async def on_ready(self):
        if self.on_ready_fired:
            return
        self.on_ready_fired = True

        self.pycord = self.get_guild(881207955029110855)
        self.errors_webhook = discord.Webhook.from_url(
            getenv("ERRORS_WEBHOOK"),
            session=self.http_session,
            bot_token=self.http.token,
        )
        environ.setdefault("JISHAKU_HIDE", "1")
        environ.setdefault("JISHAKU_NO_UNDERSCORE", "1")

        for cog in self.to_load:
            self.load_cog(cog)

        await Tortoise.init(
            db_url="sqlite://data/database.db", modules={"models": ["utils.models"]}
        )
        await Tortoise.generate_schemas()
        print(self.user, "is ready")

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(
                "An unexpected error has occured, I've notified my developer."
            )
            text = "".join(format_exception(type(error), error, error.__traceback__))
            return await self.errors_webhook.send(f"```\n{text}```")
        if isinstance(error, commands.CheckFailure) and await self.is_owner(ctx.author):
            return await ctx.reinvoke()

        await ctx.send(
            embed=discord.Embed(
                title=error.__class__.__name__,
                description=str(error),
                color=discord.Color.red(),
            )
        )

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.content != after.content:
            await self.process_commands(after)

    def run(self):
        super().run(getenv("TOKEN"))
