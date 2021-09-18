from os import environ, listdir
from re import compile as re_compile

from discord import Color, Embed, Intents, AllowedMentions
from discord.ext import commands
from dotenv import load_dotenv
from tortoise import Tortoise


class PycordManager(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="p.",
            intents=Intents(members=True, messages=True, guilds=True),
            owner_ids={543397958197182464},
            help_command=commands.MinimalHelpCommand(),
            allowed_mentions=AllowedMentions.none()
        )

    async def on_ready(self):
        self.cache = {"afk": {}}
        environ.setdefault("JISHAKU_HIDE", "1")
        environ.setdefault("JISHAKU_NO_UNDERSCORE", "1")
        self.load_extension("jishaku")

        for filename in listdir("./cogs/"):
            if filename.endswith(".py"):
                try:
                    self.load_extension(f"cogs.{filename[:-3]}")
                except Exception as e:
                    print(e)

        await Tortoise.init(
            db_url="sqlite://data/database.db", modules={"models": ["utils"]}
        )
        # await Tortoise.generate_schemas()
        print(self.user, "is ready")

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, commands.CommandInvokeError):
            raise error
        await ctx.send(
            embed=Embed(
                title=" ".join(
                    re_compile(r"[A-Z][a-z]*").findall(error.__class__.__name__)
                ),
                description=str(error),
                color=Color.red(),
            )
        )


bot = PycordManager()
load_dotenv(".env")
bot.run(environ.get("token"))
