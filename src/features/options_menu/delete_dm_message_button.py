from nextcord import Interaction
import nextcord

from features.options_menu.options_btn_interface import OptionsButton
from config.global_settings import get_bot_id

class DeleteDMButton(OptionsButton):
    def get_label(self) -> str:
        return "Delete Message"

    async def load(self, interaction: Interaction, data: dict):
        self.message: nextcord.Message = data["message"]

        # Check Message Compatibility
        if not interaction.guild and self.message.author.id == get_bot_id():
            self.outer.add_item(self)
            return True
        
        return False
            
    async def callback(self, interaction: Interaction):
        await self.message.delete()
        await self.outer.disable_all(interaction)