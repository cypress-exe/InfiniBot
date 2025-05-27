from nextcord import Interaction
import nextcord
import logging

from components.ui_components import disabled_feature_override
from components.utils import feature_is_active

class BanButton(nextcord.ui.Button):
    def __init__(self, outer, interaction: Interaction):
        super().__init__(label = "Ban Message Author")
        self.outer = outer
        self.interaction = interaction
        
    def load(self, interaction: Interaction, data: dict):
        self.message: nextcord.Message = data["message"]

        if not interaction.guild:
            return

        enabled = (
            interaction.user.guild_permissions.ban_members
            and interaction.guild.me.guild_permissions.ban_members
            and interaction.user.id != self.message.author.id
            and (
                self.message.author not in interaction.guild.members
                or (
                    interaction.guild.me.id != self.message.author.id
                    and interaction.guild.me.top_role.position > self.message.author.top_role.position
                )
            )
        )
        
        if enabled:
            self.outer.add_item(self)
            return True
        
        return False
            
    class BanView(nextcord.ui.View):
        def __init__(self, outer, message: nextcord.Message):
            super().__init__(timeout = None)
            self.outer = outer
            self.message = message

            noBtn = nextcord.ui.Button(label="No, Cancel", style=nextcord.ButtonStyle.danger)
            noBtn.callback = self.no_btn_callback
            self.add_item(noBtn)

            yesBtn = nextcord.ui.Button(label="Yes, Ban", style=nextcord.ButtonStyle.green)
            yesBtn.callback = self.yes_btn_callback
            self.add_item(yesBtn)
            
        async def setup(self, interaction: Interaction):
            if not feature_is_active(feature="options_menu__banning", guild_id=interaction.guild.id):
                await disabled_feature_override(self, interaction)
                return
            
            if self.message.author in interaction.guild.members:
                # If the member is in the server
                description = f"Are you sure that you want to ban {self.message.author.mention}?\n\nThis means that they will be kicked and not be able to re-join this server unless they are un-baned.\n\nNo messages will be deleted."
            else:
                # If the member is not in the server
                description = f"Are you sure that you want to ban \"{self.message.author}\"?\n\nThis means that they will not be able to join this server unless they are un-baned.\n\nNo messages will be deleted."
            
            embed = nextcord.Embed(title="Confirm Ban?", description=description, color=nextcord.Color.orange())
            await interaction.response.edit_message(embed=embed, view=self)
            
        async def no_btn_callback(self, interaction: Interaction):
            await self.outer.setup(interaction)
            
        async def yes_btn_callback(self, interaction: Interaction):
            try:
                await interaction.guild.ban(user=self.message.author, reason=f"{interaction.user} requested that this user be banned.", delete_message_seconds=0)
                await self.outer.disable_all(interaction)
            except Exception as error:
                logging.error(f"Error When Banning Member: {error}")
                await self.outer.setup(interaction)
                await interaction.followup.send(embed=nextcord.Embed(title="An Unknown Error Occured", description="An unknown error occured while performing this action.", color=nextcord.Color.red()), ephemeral=True)
                
    async def callback(self, interaction: Interaction):
        await self.BanView(self.outer, self.message).setup(interaction)