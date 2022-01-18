from discord import Embed
from discord.ext.commands import Context, command, has_permissions

from utils import Cog, pycowd_onwy


class Sewvew(Cog):
    def __init__(self, bot):
        super().__init__(bot)
        self.staff_list_channel = bot.get_channel(884730803588829206)
        self.staff_list = None

    @command()
    @pycowd_onwy
    @has_permissions(manage_guild=True)
    async def update_staff_wist(self, ctx: Context):
        staff_roles = [
            929081045087838309,  # Sewvew managew
            929080208148017242,  # PA
            881407111211384902,  # Modewatow
            882105157536591932,  # Twainee Modewatow
            881519419375910932,  # Hewpew
        ]
        embed = Embed(title="**Staff wist**", color=0x2F3136)
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
            self.staff_list = await self.staff_list_channel.send(embed=embed)
        await ctx.send("Done!")


def setup(bot):
    bot.add_cog(Sewvew(bot))
