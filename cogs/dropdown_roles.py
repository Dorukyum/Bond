from typing import Optional, Set

import discord
from discord.ext.commands import RoleConverter, RoleNotFound

from core import Cog, Context


def message(view: "DropdownRolesSetup") -> str:
    return (
        f"Current roles: {', '.join(role.mention for role in view.roles)}"
        if view.roles
        else "No roles added."
    )


class RoleDropdown(discord.ui.Select):
    def __init__(self, roles: Set[discord.Role]) -> None:
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
                f"You've got rid of role <@&{role_id}>.", ephemeral=True
            )
        else:
            await interaction.user.add_roles(discord.Object(id=role_id))
            await interaction.response.send_message(
                f"You've received role <@&{role_id}>.", ephemeral=True
            )
        assert self._view
        await self._view.message.edit(view=self._view)


class ChooseRoleModal(discord.ui.Modal):
    def __init__(self, view: "DropdownRolesSetup", title: str) -> None:
        super().__init__(
            discord.ui.InputText(
                label=f"Roles to {title.split()[0]}",
                placeholder='Enter role mentions, IDs or names seperated by a comma and a whitespace (", ")',
            ),
            title=title,
        )
        self.view = view

    async def callback(self, interaction: discord.Interaction):
        assert (raw_input := self._children[0].value)
        self.stop()
        for role_input in set(raw_input.split(", ")):
            if len(self.view.roles) == 25:
                break

            try:
                role = await RoleConverter().convert(
                    interaction, role_input  # type: ignore # there's no context, just interaction
                )
                if self._title == "Add Roles":
                    self.view.roles.add(role)
                elif self._title == "Remove Roles":
                    if role in self.view.roles:
                        self.view.roles.remove(role)
                    else:
                        return await interaction.response.send_message(
                            f"Role {role.mention} isn't added.", ephemeral=True
                        )
            except RoleNotFound as error:
                return await interaction.response.send_message(
                    f'Role "{error.argument}" not found.', ephemeral=True
                )

        await interaction.response.edit_message(
            content=message(self.view), view=self.view
        )


class DropdownRolesSetup(discord.ui.View):
    def __init__(self, message: Optional[str]) -> None:
        super().__init__()
        self.content = message
        self.roles: Set[discord.Role] = set()

    @discord.ui.button(label="Add roles", style=discord.ButtonStyle.green)
    async def add_role_button(self, _, interaction: discord.Interaction):
        await interaction.response.send_modal(ChooseRoleModal(self, "Add Roles"))

    @discord.ui.button(label="Remove roles", style=discord.ButtonStyle.red)
    async def remove_role_button(self, _, interaction: discord.Interaction):
        await interaction.response.send_modal(ChooseRoleModal(self, "Remove Roles"))

    @discord.ui.button(label="Submit", style=discord.ButtonStyle.blurple)
    async def submit_button(self, _, interaction: discord.Interaction):
        if not self.roles:
            return await interaction.response.send_message(
                "You cannot create a dropdown without adding roles.", ephemeral=True
            )
        await interaction.channel.send(  # type: ignore # StageChannel has no attribute "send"
            self.content,
            view=discord.ui.View(RoleDropdown(self.roles), timeout=None),
        )
        await interaction.response.send_message(
            "Successfully created role selection dropdown.", ephemeral=True
        )
        self.stop()


class DropdownRoles(Cog):
    """Commands related to self-role selection dropdowns."""

    @Cog.listener()
    async def on_ready(self):
        self.bot.add_view(
            discord.ui.View(discord.ui.Select(custom_id="role_selector"), timeout=None)
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
            view=DropdownRolesSetup(message),
            ephemeral=True,
        )


def setup(bot):
    bot.add_cog(DropdownRoles(bot))
