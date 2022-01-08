from discord import Embed
from discord.ext.commands import Context, command, has_permissions

from utils import Cog, pycord_only


class Server(Cog):
    def __init__(self, bot):
        super().__init__(bot)
        self.staff_list_channel = bot.get_channel(884730803588829206)
        self.staff_list = None

    @command()
    @pycord_only
    @has_permissions(manage_guild=True)
    async def update_staff_list(self, ctx: Context):
        staff_roles = [
            929080208148017242,  # PA
            929081045087838309,  # Server Manager
            881407111211384902,  # Moderator
            882105157536591932,  # Trainee Moderator
            881519419375910932,  # Helper
        ]
        embed = Embed(title="**Staff List**", color=0x2F3136)
        embed.description = ""
        for role in staff_roles:
            role = ctx.guild.get_role(role)
            valid_members = [
                member for member in role.members if member.top_role == role
            ]
            embed.description += f"{role.mention} | **{len(valid_members)}** \n"

            for member in valid_members:
                embed.description += f"> `{member.id}` {member.mention}\n"
            embed.description += "\n"

        if self.staff_list is not None:
            await self.staff_list.edit(embed=embed)
        else:
            await self.staff_list_channel.purge(limit=1)
            await self.staff_list_channel.send(embed=embed)
        await ctx.send("Done!")


def setup(bot):
    bot.add_cog(Server(bot))
