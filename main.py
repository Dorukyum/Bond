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
        )

        for filename in listdir("./cogs/"):
            if filename.endswith(".py"):
                try:
                    self.load_extension(f"cogs.{filename[:-3]}")
                except Exception as e:
                    print(e)

    async def on_ready(self):
        self.main_guild = self.get_guild(881207955029110855)
        self.cache = {"afk": {}}
        environ.setdefault("JISHAKU_HIDE", "1")
        environ.setdefault("JISHAKU_NO_UNDERSCORE", "1")
        self.load_extension("jishaku")

        await Tortoise.init(
            db_url="sqlite://data/database.db", modules={"models": ["utils"]}
        )
        # await Tortoise.generate_schemas()
        print(self.user, "is ready")


bot = PycordManager()
load_dotenv(".env")
bot.run(environ.get("TOKEN"))
