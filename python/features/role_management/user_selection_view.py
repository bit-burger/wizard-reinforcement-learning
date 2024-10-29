from typing import Optional

import discord
from discord import ui


class MultiUserSelect(ui.UserSelect):
    def __init__(self, role_name: str, color: str):
        super().__init__(placeholder="Select users to assign the role", min_values=0, max_values=10)
        self.role_name = role_name
        self.color = color

    async def callback(self, interaction: discord.Interaction):
        selected_users = [user for user in self.values]
        self.view.selected_users = selected_users
        self.view.skipped = False
        self.view.stop()
        # noinspection PyUnresolvedReferences
        await interaction.response.defer()


class SkipButton(ui.Button):
    def __init__(self):
        super().__init__(label="Skip", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_users = []
        self.view.skipped = True
        self.view.stop()
        # noinspection PyUnresolvedReferences
        await interaction.response.defer()


class RoleAssignmentView(ui.View):
    def __init__(self, role_name: str, color: str):
        super().__init__()
        self.selected_users = []
        self.skipped = False
        self.interaction: Optional[discord.Interaction] = None
        self.add_item(MultiUserSelect(role_name, color))
        self.add_item(SkipButton())

    def set_interaction(self, interaction: discord.Interaction):
        """Stores the interaction to be used later for editing the message."""
        self.interaction = interaction
