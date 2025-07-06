import logging
from nextcord import Interaction
import nextcord

from features.options_menu.ban_button import BanButton
from features.options_menu.delete_dm_message_button import DeleteDMButton
from features.options_menu.edit_button import EditButton

from components import ui_components, utils
from config.global_settings import get_bot_load_status
from config.server import Server



class OptionsView(ui_components.CustomView):
    def __init__(self, interaction: Interaction, has_config_perms: bool, buttons: list, relevant_object: (nextcord.Message | nextcord.Member)):
        super().__init__(timeout = None)
        self.interaction = interaction
        self.has_config_perms = has_config_perms
        
        self.this_message_id = None
        self.relevant_object = relevant_object

        # Determine if the relevant object is a message or a member
        self.relevant_object_type = "Unknown"
        if isinstance(relevant_object, nextcord.Message):
            self.relevant_object_type = "Message"
        elif isinstance(relevant_object, nextcord.Member) or isinstance(relevant_object, nextcord.User):
            self.relevant_object_type = "Member"

        # Register buttons
        self.buttons = [button(self, interaction, _type=self.relevant_object_type) for button in buttons]
        # Note: These buttons aren't added yet, because the load function needs to be called
        # on the buttons before they decide whether they want to add themselves or not.

    async def setup(self, interaction: Interaction):
        # Uncomment this if to check if the bot is fully loaded before showing the options
        # if not get_bot_load_status():
        #     await self.show_error(interaction, "The bot is not fully loaded yet. Please wait a few minutes and try again.")
        #     return
        
        if not utils.feature_is_active(feature="options_menu"):
            await self.show_error(interaction, "This feature is disabled by the developers of InfiniBot. This is likely due to an critical instability with it right now. It will be re-enabled shortly after the issue has been resolved.")
            return

        await self.show_loading(interaction)

        # Get data for buttons
        data = {}
        if self.relevant_object_type == "Message":
            message_info = None
            if interaction.guild:
                server = Server(interaction.guild.id)
                if self.relevant_object.id in server.managed_messages: message_info = server.managed_messages[self.relevant_object.id]

            data.update({
                "message": self.relevant_object,
                "message_info": message_info
            })
        elif self.relevant_object_type == "Member":
            data.update({
                "member": self.relevant_object
            })

        # Load buttons
        for button in self.buttons:
            await button.load(interaction, data)

        if len(self.children) == 0:
            await self.show_error(interaction, f"Hmmm. You don't have any options for this {self.relevant_object_type.lower()}.")
        else:
            await self.show_options(interaction)

    async def show_loading(self, interaction: Interaction):
        embed = nextcord.Embed(title=f"{self.relevant_object_type} Options", description="Syncing Data. Please Wait...", color=nextcord.Color.blue())
        await self.disable_all(interaction, edit=False)
        self.this_message_id = await self.send_robust(interaction, embed=embed, view=self)

    async def show_error(self, interaction: Interaction, description: str):
        embed = nextcord.Embed(title=f"{self.relevant_object_type} Options - Error", description=description, color=nextcord.Color.red())
        await self.send_robust(interaction, embed=embed, view=self)

    async def send_robust(self, interaction: Interaction, **kwargs):
        if self.this_message_id is not None:
            try:
                message = await interaction.response.edit_message(**kwargs)
                message_id = message.id
            except nextcord.errors.InteractionResponded:
                message = await interaction.followup.edit_message(self.this_message_id, **kwargs)
                message_id = message.id
            
        else:
            # Ensure **kwargs has ephemeral set to True, unless explicitly set to False
            if "ephemeral" not in kwargs:
                kwargs["ephemeral"] = True
            
            try:
                message = await interaction.response.send_message(**kwargs)
                message_id = (await message.fetch()).id
            except nextcord.errors.InteractionResponded:
                message = await interaction.followup.send(**kwargs)
                message_id = message.id

        self.this_message_id = message
        return message_id

    async def show_options(self, interaction: Interaction):
        embed = nextcord.Embed(title=f"{self.relevant_object_type} Options", description="This message supports the options below:", color=nextcord.Color.blue())
        await self.send_robust(interaction, embed=embed, view=self)
        
    async def disable_all(self, interaction: Interaction, edit=True):
        for child in self.children:
            if isinstance(child, nextcord.ui.Button):
                child.disabled = True

        if not edit: return
        if self.this_message_id is None: return
        
        try:
            self.this_message_id = await interaction.response.edit_message(view=self, delete_after=0.0)
        except nextcord.errors.InteractionResponded:
            await interaction.followup.edit_message(self.this_message_id.id, view=self, delete_after=0.0)


class MessageCommandOptionsView(OptionsView):
    def __init__(self, interaction: Interaction, has_config_perms: bool, relevant_message: nextcord.Message):
        buttons = [
            EditButton,
            BanButton,
            DeleteDMButton
        ]

        super().__init__(interaction, has_config_perms, buttons, relevant_message)        

async def run_message_command(interaction: Interaction, relevant_message: nextcord.Message):
    has_config_perms = (await utils.user_has_config_permissions(interaction, notify=False) if interaction.guild else True)
    await MessageCommandOptionsView(interaction, has_config_perms, relevant_message).setup(interaction)


class MemberCommandOptionsView(OptionsView):
    def __init__(self, interaction: Interaction, has_config_perms: bool, relevant_member: nextcord.Member):
        buttons = [
            BanButton
        ]

        super().__init__(interaction, has_config_perms, buttons, relevant_member)        

async def run_member_command(interaction: Interaction, relevant_member: nextcord.Member):
    has_config_perms = (await utils.user_has_config_permissions(interaction, notify=False) if interaction.guild else True)
    await MemberCommandOptionsView(interaction, has_config_perms, relevant_member).setup(interaction)

