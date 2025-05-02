from nextcord import Interaction
import nextcord

from features.options_menu.ban_button import BanButton
from features.options_menu.delete_dm_message_button import DeleteDMButton
from features.options_menu.edit_button import EditButton

from components import utils
from config.global_settings import get_bot_load_status
from config.server import Server



class MessageCommandOptionsView(nextcord.ui.View):
    def __init__(self, interaction: Interaction, message: nextcord.Message, has_config_perms: bool):
        super().__init__(timeout = None)
        self.interaction = interaction
        self.message = message
        self.has_config_perms = has_config_perms
        
        self.this_message_id = None
        
        # Register buttons
        self.buttons = [
            DeleteDMButton(self, interaction),
            EditButton(self, interaction),
            BanButton(self, interaction)
        ]
        # Note: These buttons aren't added yet, because the load function needs to be called
        # on the buttons before they decide whether they want to add themselves or not.

    async def setup(self, interaction: Interaction):
        if not get_bot_load_status():
            await self.show_error(interaction, "The bot is not fully loaded yet. Please wait a few minutes and try again.")
            return
        
        if not utils.feature_is_active(feature="options_menu"):
            await self.show_error(interaction, "This feature is disabled by the developers of InfiniBot. This is likely due to an critical instability with it right now. It will be re-enabled shortly after the issue has been resolved.")
            return

        await self.show_loading(interaction)

        # Get message information
        message_info = None
        if interaction.guild:
            server = Server(interaction.guild.id)
            if self.message.id in server.managed_messages: message_info = server.managed_messages[self.message.id]

        data = {
            "message": self.message,
            "message_info": message_info
        }

        # Load buttons
        for button in self.buttons:
            button.load(interaction, data)

        if len(self.children) == 0:
            await self.show_error(interaction, "Hmmm. You don't have any options for this message.")
        else:
            await self.show_options(interaction)

    async def show_loading(self, interaction: Interaction):
        embed = nextcord.Embed(title="Message Options", description="Syncing Data. Please Wait...", color=nextcord.Color.blue())
        self.this_message_id = await self.send_robust(interaction, embed=embed, view=self)

    async def show_error(self, interaction: Interaction, description: str):
        embed = nextcord.Embed(title="Message Options - Error", description=description, color=nextcord.Color.red())
        await self.send_robust(interaction, embed=embed, view=self)

    async def send_robust(self, interaction: Interaction, **kwargs):
        if self.this_message_id is not None:
            if interaction.response.is_done():
                message = await interaction.followup.edit_message(self.this_message_id, **kwargs)
                message_id = message.id
            else:
                message = await interaction.response.edit_message(**kwargs)
                message_id = message.id
        else:
            # Ensure **kwargs has ephemeral set to True, unless explicitly set to False
            if "ephemeral" not in kwargs:
                kwargs["ephemeral"] = True
                
            if interaction.response.is_done():
                message = await interaction.followup.send(**kwargs)
                message_id = message.id
            else:
                message = await interaction.response.send_message(**kwargs)
                message_id = (await message.fetch()).id

        return message_id

    async def show_options(self, interaction: Interaction):
        embed = nextcord.Embed(title="Message Options", description="This message supports the options below:", color=nextcord.Color.blue())
        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except nextcord.errors.InteractionResponded:
            await interaction.followup.edit_message(self.this_message_id, embed=embed, view=self)
        
    async def disable_all(self, interaction: Interaction):
        for child in self.children:
            if isinstance(child, nextcord.ui.Button):
                child.disabled = True
        
        try:
            self.this_message_id = await interaction.response.edit_message(view = self, delete_after = 0.0)
        except nextcord.errors.InteractionResponded:
            await interaction.followup.edit_message(self.this_message_id.id, view = self, delete_after = 0.0)

async def run_message_command(interaction: Interaction, message: nextcord.Message):
    has_config_perms = (await utils.user_has_config_permissions(interaction, notify=False) if interaction.guild else True)
    await MessageCommandOptionsView(interaction, message, has_config_perms).setup(interaction)



