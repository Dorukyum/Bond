from typing import List, Optional

import discord

from core import Cog, Context


class RoleDropdown(discord.ui.Select):
    def __init__(self, roles: List[discord.Role]) -> None:
        super().__init__(
            custom_id="role_dropdown",
            placeholder="Select a role",
            options=[
                discord.SelectOption(label=role.name, value=str(role.id))
                for role in roles
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        assert isinstance(interaction.user, discord.Member)
        role_id = int(self.values[0])
        if role_id in interaction.user._roles:
            await interaction.user.remove_roles(discord.Object(id=role_id))
            await interaction.response.send_message(
                f"Removed role <@&{role_id}>.", ephemeral=True
            )
        else:
            await interaction.user.add_roles(discord.Object(id=role_id))
            await interaction.response.send_message(
                f"Received role <@&{role_id}>.", ephemeral=True
            )
        assert self._view
        await self._view.message.edit(view=self._view)


class DropdownRolesSetup(discord.ui.Select):
    def __init__(self, custom_message: Optional[str] = None) -> None:
        super().__init__(
            discord.ComponentType.role_select,
            placeholder="Choose self-roles",
            max_values=25,
        )
        self.custom_message = custom_message

    async def callback(self, interaction: discord.Interaction):
        if any(
            role.position >= interaction.user.top_role.position   # type: ignore # these roles aren't None
            for role in self.values
        ) and interaction.guild.owner_id != interaction.user.id:  # type: ignore # these members aren't None
            return await interaction.response.send_message(
                "You can only choose roles that are below your top role.",
                ephemeral=True,
            )
        await interaction.channel.send(
            content=self.custom_message,
            view=discord.ui.View(RoleDropdown(self.values)),
        )
        await interaction.response.send_message(
            "Successfuly created self-role selection dropdown.",
            ephemeral=True,
        )


class DropdownRoles(Cog):
    """Commands related to self-role selection dropdowns."""

    @Cog.listener()
    async def on_ready(self):
        self.bot.add_view(
            discord.ui.View(discord.ui.Select(custom_id="role_dropdown"), timeout=None)
        )

    dropdown_roles = discord.SlashCommandGroup(
        "dropdown_roles",
        "Commands related to self-role selection dropdowns.",
        guild_only=True,
        default_member_permissions=discord.Permissions(manage_guild=True),
    )

    @dropdown_roles.command()
    @discord.option(
        "message",
        str,
        description="The content of the message to be sent along with the dropdown.",
        default=None,
    )
    async def setup(self, ctx: Context, message: Optional[str]):
        """Setup a dropdown menu for choosing roles."""
        await ctx.respond(
            "Add roles to get started.",
            view=discord.ui.View(DropdownRolesSetup(message)),
            ephemeral=True,
        )


def setup(bot):
    bot.add_cog(DropdownRoles(bot))
