from nextcord import Interaction
import nextcord
import logging

from features.options_menu.options_btn_interface import OptionsButton
from components.ui_components import CustomView, disabled_feature_override
from components.utils import feature_is_active

class BanButton(OptionsButton):
    def get_label(self) -> str:
        return "Ban Message Author" if self._type == "message" else "Ban Member"
        
    def load(self, interaction: Interaction, data: dict):
        self.message: nextcord.Message = data.get("message", None)
        self.member: nextcord.Member = data.get("member", None)
        
        self.relevant_member = self.message.author if self.message else self.member

        # Confirm that the member is not already banned

        if not interaction.guild:
            return

        enabled = (
            interaction.user.guild_permissions.ban_members
            and interaction.guild.me.guild_permissions.ban_members
            and interaction.user.id != self.relevant_member.id
            and (
                self.relevant_member not in interaction.guild.members
                or (
                    interaction.guild.me.id != self.relevant_member.id
                    and interaction.guild.me.top_role.position > self.relevant_member.top_role.position
                )
            )
        )
        
        if enabled:
            self.outer.add_item(self)
            return True
        
        return False
            
    class BanView(CustomView):
        def __init__(self, outer, parent, message: nextcord.Message):
            super().__init__(timeout = None)
            self.outer = outer
            self.parent = parent
            self.message = message

            no_btn = nextcord.ui.Button(label="No, Cancel", style=nextcord.ButtonStyle.danger)
            no_btn.callback = self.no_btn_callback
            self.add_item(no_btn)

            yes_btn = nextcord.ui.Button(label="Yes, Ban", style=nextcord.ButtonStyle.green)
            yes_btn.callback = self.yes_btn_callback
            self.add_item(yes_btn)

        async def setup(self, interaction: Interaction):
            if not feature_is_active(feature="options_menu__banning", guild_id=interaction.guild.id):
                await disabled_feature_override(self, interaction)
                return

            if self.parent.relevant_member in interaction.guild.members:
                # If the member is in the server
                description = f"Are you sure that you want to ban {self.parent.relevant_member.mention}?\n\nThis means that they will be kicked and not be able to re-join this server unless they are un-baned.\n\nNo messages will be deleted."
            else:
                # If the member is not in the server
                description = f"Are you sure that you want to ban \"{self.parent.relevant_member}\"?\n\nThis means that they will not be able to join this server unless they are un-baned.\n\nNo messages will be deleted."

            embed = nextcord.Embed(title="Confirm Ban?", description=description, color=nextcord.Color.orange())
            await interaction.response.edit_message(embed=embed, view=self)
            
        async def no_btn_callback(self, interaction: Interaction):
            await self.outer.disable_all(interaction)
            
        async def yes_btn_callback(self, interaction: Interaction):
            try:
                await interaction.guild.ban(user=self.parent.relevant_member, reason=f"{interaction.user} requested that this user be banned.", delete_message_seconds=0)
                await self.outer.disable_all(interaction)
            except Exception as error:
                logging.error(f"Error When Banning Member: {error}")
                await self.outer.setup(interaction)
                await interaction.followup.send(embed=nextcord.Embed(title="An Unknown Error Occured", description="An unknown error occured while performing this action.", color=nextcord.Color.red()), ephemeral=True)
                
    async def callback(self, interaction: Interaction):
        await self.BanView(self.outer, self, self.message).setup(interaction)