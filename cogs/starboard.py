import discord

from utils import Cog, pycord_only, StarboardModel

class Starboard(Cog):
    """A cog for the starboard."""

    def __init__(self, bot) -> None:
        super().__init__(bot)
        self.starboard_channel = bot.get_channel(881493944175820831)

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        isKnown = async IsKnown(message.id)

        if isKnown:
            return
        else:
            return

def setup(bot):
    bot.add_cog(Starboard(bot))
