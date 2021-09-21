import discord
from discord.ext.commands import Context, command, has_permissions

from utils import Cog


class CloseTicketButton(discord.ui.Button):
    def __init__(self, channel, user):
        self.channel: discord.TextChannel = channel
        self.user = user
        super().__init__(style=discord.ButtonStyle.red, label="Close Ticket")

    async def callback(self, interaction: discord.Interaction):
        await self.channel.send("Closed ticket.")
        await self.channel.edit(
            name=self.channel.name.replace("ticket", "closed"),
            overwrites={self.user: discord.PermissionOverwrite(view_channel=None)},
        )


class CreateTicketButton(discord.ui.Button):
    def __init__(self, category):
        self.category: discord.CategoryChannel = category
        super().__init__(style=discord.ButtonStyle.green, label="Open Ticket")

    async def callback(self, interaction: discord.Interaction):
        channel = await self.category.create_text_channel(
            f"ticket-{interaction.user.name.replace(' ', '-')}",
            overwrites={
                interaction.user: discord.PermissionOverwrite(
                    view_channel=True, send_messages=True
                )
            },
        )
        await interaction.response.send_message(
            f"Ticket created! {channel.mention}", ephemeral=True
        )
        view = discord.ui.View()
        view.add_item(CloseTicketButton(channel, interaction.user))
        await channel.send(
            embed=discord.Embed(
                title=f"Ticket | {interaction.user.name}",
                color=discord.Color.blurple(),
            ),
            view=view,
        )


class Tickets(Cog):
    """A cog for the ticket system."""

    @command()
    @has_permissions(manage_permissions=True)
    async def ticket_init(self, ctx: Context):
        """Send a ticket creator message."""
        view = discord.ui.View(timeout=None)
        view.add_item(CreateTicketButton(ctx.channel.category))
        await ctx.send(
            embed=discord.Embed(
                title="Support Tickets",
                description="Use the dropdown below to open a support ticket. Remember that opening unnecessary tickets will lead to punishment.",
                color=discord.Color.blurple(),
            ),
            view=view,
        )


def setup(bot):
    bot.add_cog(Tickets(bot))
