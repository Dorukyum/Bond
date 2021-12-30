from discord.ext import commands


class PycordOnly(commands.CheckFailure):
    pass


async def predicate(ctx):
    if ctx.guild and ctx.guild.id == 881207955029110855:
        return True
    raise PycordOnly("This command can only be used in the Pycord server.")


pycord_only = commands.check(predicate)
