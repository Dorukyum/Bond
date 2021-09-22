from contextlib import suppress
from os import environ, listdir
from re import compile as re_compile

import discord
from discord.ext import commands
from dotenv import load_dotenv
from tortoise import Tortoise


class PycordManager(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="p.",
            intents=discord.Intents(members=True, messages=True, guilds=True),
            owner_ids={543397958197182464},
            help_command=commands.MinimalHelpCommand(),
            allowed_mentions=discord.AllowedMentions.none(),
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
            embed=discord.Embed(
                title=" ".join(
                    re_compile(r"[A-Z][a-z]*").findall(error.__class__.__name__)
                ),
                description=str(error),
                color=discord.Color.red(),
            )
        )

    async def on_message(self, message):
        if message.author.bot:
            return

        if message.author.id in self.cache["afk"].keys():
            del self.cache["afk"][message.author.id]
            await message.channel.send(
                f"Welcome back {message.author.display_name}! You're no longer AFK.",
                delete_after=4.0,
            )
            with suppress(discord.Forbidden):
                await message.author.edit(nick=message.author.display_name[6:])
        for mention in message.mentions:
            if msg := self.cache["afk"].get(mention.id):
                await message.channel.send(f"{mention.display_name} is AFK: {msg}")

        await self.process_commands(message)


bot = PycordManager()
load_dotenv(".env")
bot.run(environ.get("token"))
