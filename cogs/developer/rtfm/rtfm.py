from discord import ButtonStyle
from discord.ext.pages import PaginatorButton

TARGETS = {
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
    "pycord": "https://docs.pycord.dev/en/stable",
    "pycord-master": "https://docs.pycord.dev/en/master",
    "pygame": "https://www.pygame.org/docs",
    "python": "https://docs.python.org/3",
    "requests": "https://requests.readthedocs.io/en/master",
    "seaborn": "https://seaborn.pydata.org",
    "simplejson": "https://simplejson.readthedocs.io/en/latest",
    "sqlalchemy": "https://docs.sqlalchemy.org/en/14",
    "tensorflow": "https://www.tensorflow.org/api_docs/python",
    "wikipedia": "https://wikipedia.readthedocs.io/en/latest",
}


OVERRIDES = {
    "tensorflow": "https://github.com/mr-ubik/tensorflow-intersphinx/raw/master/tf2_py_objects.inv",
}


def create_buttons() -> list[PaginatorButton]:
    return [
        PaginatorButton(
            "first",
            label="<<",
            style=ButtonStyle.blurple,
        ),
        PaginatorButton(
            "prev",
            label="<",
            style=ButtonStyle.blurple,
            loop_label="↪",
        ),
        PaginatorButton(
            "page_indicator",
            style=ButtonStyle.grey,
            disabled=True,
        ),
        PaginatorButton(
            "next",
            label=">",
            style=ButtonStyle.blurple,
            loop_label="↩",
        ),
        PaginatorButton(
            "last",
            label=">>",
            style=ButtonStyle.blurple,
        ),
    ]
