from os import environ, listdir
from sys import argv

import discord
from discord.ext import commands
from dotenv import load_dotenv
from tortoise import Tortoise

from utils import Tag


class PycordManager(commands.Bot):
    Tag = Tag

    def __init__(self):
        super().__init__(
            command_prefix=("p." if "-t" not in argv else "d."),
            intents=discord.Intents(members=True, messages=True, guilds=True),
            owner_ids={543397958197182464},
            help_command=commands.MinimalHelpCommand(),
            allowed_mentions=discord.AllowedMentions.none(),
            activity=discord.Activity(
                type=discord.ActivityType.listening, name="p.help"
            ),
            debug_guilds=[881207955029110855],
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

    async def on_ready(self):
        if self.on_ready_fired:
            return
        else:
            self.on_ready_fired = True

        self.main_guild = self.get_guild(881207955029110855)
        environ.setdefault("JISHAKU_HIDE", "1")
        environ.setdefault("JISHAKU_NO_UNDERSCORE", "1")

        for cog in self.to_load:
            self.load_cog(cog)

        await Tortoise.init(
            db_url="sqlite://data/database.db", modules={"models": ["utils"]}
        )
        # await Tortoise.generate_schemas()
        print(self.user, "is ready")


bot = PycordManager()
load_dotenv(".env")
bot.run(environ.get("TOKEN"))
