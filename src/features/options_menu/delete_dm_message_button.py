from nextcord import Interaction
import nextcord

from config.global_settings import get_bot_id

class DeleteDMButton(nextcord.ui.Button):
    def __init__(self, outer, interaction: Interaction):
        super().__init__(label = "Delete Message")
        
        self.outer = outer
        self.interaction = interaction
        
    def load(self, interaction: Interaction, data: dict):
        self.message: nextcord.Message = data["message"]

        # Check Message Compatibility
        if not interaction.guild and self.message.author.id == get_bot_id():
            self.outer.add_item(self)
            return True
        
        return False
            
    async def callback(self, interaction: Interaction):
        await self.message.delete()
        await self.outer.disable_all(interaction)