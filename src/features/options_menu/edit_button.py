from nextcord import Interaction
import nextcord

from features.options_menu.editing import reaction_roles, embeds, role_messages
from features.options_menu.options_btn_interface import OptionsButton

class EditButton(OptionsButton):
    def get_label(self) -> str:
        return "Edit Message"

    async def load(self, interaction: Interaction, data: dict):
        self.message: nextcord.Message = data["message"]
        self.message_info: dict = data["message_info"]

        # Check Message Compatibility
        if not interaction.guild: return
        
        if self.determine_editability(interaction):
            self.outer.add_item(self)

    def determine_editability(self, interaction: Interaction):
        if not interaction.guild: return
        if not self.message.author == interaction.guild.me: return
        if not self.message_info: return
        if not interaction.user.id == self.message_info.author_id: 
            if not interaction.user.guild_permissions.administrator: return
        
        return True
            
    async def callback(self, interaction: Interaction):
        if self.message_info.message_type == "embed":
            await embeds.EditEmbed(self.message.id).setup(interaction)
        elif self.message_info.message_type == "reaction_role":
            await reaction_roles.EditReactionRole(self.message.id).setup(interaction)
        elif self.message_info.message_type == "role_message":
            await role_messages.EditRoleMessage(self.message.id).setup(interaction)