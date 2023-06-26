import warnings

import discord
from discord import Color, Embed
from discord.ext import pages

from . import fuzzy, parser
from core import Cog, Toolkit


targets = {
    "aiohttp": "https://docs.aiohttp.org/en/stable",
    "aiosqlite": "https://aiosqlite.omnilib.dev/en/latest",
    "apraw": "https://apraw.readthedocs.io/en/latest",
    "asyncpg": "https://magicstack.github.io/asyncpg/current",
    "discord.py": "https://discordpy.readthedocs.io/en/latest",
    "django": "https://django.readthedocs.io/en/stable",
    "flask": "https://flask.palletsprojects.com/en/1.1.x",
    "imageio": "https://imageio.readthedocs.io/en/stable",
    "matplotlib": "https://matplotlib.org/stable",
    "numpy": "https://numpy.readthedocs.io/en/latest",
    "pandas": "https://pandas.pydata.org/docs",
    "pillow": "https://pillow.readthedocs.io/en/stable",
    "praw": "https://praw.readthedocs.io/en/latest",
    "py-cord": "https://docs.pycord.dev/en/stable",
    "py-cord-master": "https://docs.pycord.dev/en/master",
    "pygame": "https://www.pygame.org/docs",
    "python": "https://docs.python.org/3",
    "requests": "https://requests.readthedocs.io/en/master",
    "seaborn": "https://seaborn.pydata.org",
    "simplejson": "https://simplejson.readthedocs.io/en/latest",
    "sqlalchemy": "https://docs.sqlalchemy.org/en/14",
    "tensorflow": "https://www.tensorflow.org/api_docs/python",
    "wikipedia": "https://wikipedia.readthedocs.io/en/latest",
}


url_overrides = {
    "tensorflow": "https://github.com/mr-ubik/tensorflow-intersphinx/raw/master/tf2_py_objects.inv"
}

def auto_complete(ctx: discord.AutocompleteContext):
        target = ctx.options["library"]
        cache = ctx.cog.cache.get(target)

        if not cache:
            return []
        
        results = ctx.cog.get_results(target, ctx.value)
    
        if not results:
            return []
        else:
            return [key for key, url in results]
    
def auto_complete_pycord(ctx: discord.AutocompleteContext):
        target = "py-cord"
        
        results = ctx.cog.get_results(target, ctx.value)
    
        if not results:
            return []
        else:
            return [key for key, url in results]

def create_buttons():
    buttons = [
        pages.PaginatorButton(
            "first",
            label="<<",
            style=discord.ButtonStyle.blurple,
        ),
        pages.PaginatorButton(
            "prev",
            label="<",
            style=discord.ButtonStyle.blurple,
            loop_label="↪",
        ),
        pages.PaginatorButton(
            "page_indicator",
            style=discord.ButtonStyle.grey,
            disabled=True,
        ),
        pages.PaginatorButton(
            "next",
            label=">",
            style=discord.ButtonStyle.blurple,
            loop_label="↩",
        ),
        pages.PaginatorButton(
            "last",
            label=">>",
            style=discord.ButtonStyle.blurple,
        ),
    ]
    return buttons


class RTFM(Cog):
    """Search through manuals of several python modules and python itself"""

    def __init__(self, bot: Toolkit) -> None:
        self.bot = bot
        self.cache: dict[str, dict] = {}
        self.bot.loop.create_task(self.ready_task())



    async def build(self, target) -> None:
        url = targets[target]
        req = await self.bot.http_session.get(url_overrides.get(target, url + "/objects.inv"))
        if req.status != 200:
            warnings.warn(
                Warning(
                    f"Received response with status code {req.status} when trying to build RTFM cache for {target} through {url}/objects.inv"
                )
            )
            raise discord.ApplicationCommandError("Failed to build RTFM cache")
        self.cache[target] = parser.SphinxObjectFileReader(
            await req.read()
        ).parse_object_inv(url)
    
    async def ready_task(self):
        await self.bot.wait_until_ready()
        for target in targets:
            self.bot.loop.create_task(self.build(target))
        
    
    def get_results(self, target, term):
        cache = self.cache.get(target)
        if not cache:
            return []
        results = fuzzy.finder(term, list(cache.items()), key=lambda x: x[0], lazy=False)

        return results

    async def do_rtfm(self, ctx: discord.ApplicationContext, doc, term):
        results = self.get_results(doc, term)

        if not results:
            return await ctx.respond("Couldn't find any results")

        if len(results) <= 15:  # type: ignore
            embed = Embed(
                title=f"Searched in {doc}",
                description="\n".join([f"[`{key}`]({url})" for key, url in results]),
                color=0x5867F7,
            )
            return await ctx.respond(embed=embed)

        chunks = discord.utils.as_chunks(results, 15)  # type: ignore
        embeds = []
        for chunk in chunks:
            embed = Embed(
                title=f"Searched in {doc}",
                description="\n".join([f"[`{key}`]({url})" for key, url in chunk]),
                color=0x5867F7,
            )
            embeds.append(embed)

        paginator = pages.Paginator(
            embeds, custom_buttons=create_buttons(), use_default_buttons=False
        )
        await paginator.respond(ctx.interaction)

    

    r_group = discord.SlashCommandGroup(name="rtfm", description="Search through docs of a library")

    @r_group.command(name="lib", description="Search through docs of a library")
    async def lib(self, ctx: discord.ApplicationContext, doc: discord.Option(str, name="library", description="The library to search in", choices=list(targets.keys())), term: discord.Option(str, name="term", description="The term to search for", autocomplete=auto_complete)):
        """
        Search through docs of a library
        Args: doc, term
        """
        await self.do_rtfm(ctx, doc, term)
    
    @r_group.command(name="py-cord", description="Search through docs of py-cord")
    async def py_cord(self, ctx: discord.ApplicationContext, term: discord.Option(str, name="term", description="The term to search for", autocomplete=auto_complete_pycord)):
        """
        Search through docs of py-cord
        Args: term
        """
        await self.do_rtfm(ctx, "py-cord", term)

    @r_group.command(name="list")
    async def list_targets(self, ctx: discord.ApplicationContext):
        """List all the avaliable documentation search targets"""

        embed = Embed(title="RTFM list of avaliable modules", color=Color.green())
        embed.description = ", ".join(
            [
                f"[{target}]({link})"
                for target, link in targets.items()
            ]
        )

        await ctx.respond(embed=embed)
