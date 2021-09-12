from discord.ext.commands import Context, command

from utils import Cog


class General(Cog):
    @command()
    async def ping(self, ctx: Context):
        await ctx.send(f"Pong! `{self.bot.latency*1000:.2f}ms`")


def setup(bot):
    bot.add_cog(General(bot))
