from discord.ext import commands


class Pycowdonwy(commands.CheckFailure):
    pass


async def predicate(ctx):
    if ctx.guild and ctx.guild.id == 881207955029110855:
        return True
    raise Pycowdonwy("Thiws command cawn onwy be used in the pycowd sewvew.")


pycowd_onwy = commands.check(predicate)
