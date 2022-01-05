from os import environ, getenv, path
from sys import argv
from json import load, dump
from typing import Optional

import discord
from discord.ext import commands
from tortoise import Tortoise


class PycordManager(commands.Bot):
    def __init__(self):
        config = self.load_config()
        prefix = config["prefix"] if "-t" not in argv else "d."

        super().__init__(
            command_prefix=prefix,
            intents=discord.Intents(members=True, messages=True, guilds=True),
            owner_ids=config["owner_ids"],
            help_command=commands.MinimalHelpCommand(),
            allowed_mentions=discord.AllowedMentions.none(),
            activity=discord.Activity(
                type=discord.ActivityType.listening, name=f"{config['prefix']}help"
            ),
            debug_guilds=config["debug_guilds"],
        )

        self.on_ready_fired = False
        self.cache = {"afk": {}, "unmute_task": {}}
        self.to_load = [
            "jishaku",
            "cogs.developer",
            "cogs.events",
            "cogs.fun",
            "cogs.general",
            "cogs.moderation",
            "cogs.server",
            "cogs.tags",
        ]

        for cog in ["cogs.pycord"]:  # cogs with application commands
            self.load_cog(cog)

    def load_cog(self, cog: str) -> None:
        try:
            self.load_extension(cog)
        except Exception as e:
            print(e)

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

    async def on_ready(self):
        if self.on_ready_fired:
            return
        else:
            self.on_ready_fired = True

        self.pycord = self.get_guild(881207955029110855)
        self.log_error = discord.Webhook.from_url(
            getenv("ERRORS_WEBHOOK"), session=self.http._HTTPClient__session, bot_token=self.http.token
        ).send
        environ.setdefault("JISHAKU_HIDE", "1")
        environ.setdefault("JISHAKU_NO_UNDERSCORE", "1")

        for cog in self.to_load:
            self.load_cog(cog)

        await Tortoise.init(
            db_url="sqlite://data/database.db", modules={"models": ["utils.models"]}
        )
        await Tortoise.generate_schemas()
        print(self.user, "is ready")
    
    def run(self):
        super().run(getenv("TOKEN"))
