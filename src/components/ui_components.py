import copy
import logging
import uuid

import nextcord
from nextcord import Interaction

from config.global_settings import get_configs, required_permissions
from core.log_manager import get_uuid_for_logging

# View overrides
async def disabled_feature_override(self: nextcord.ui.View, interaction: Interaction) -> None:
    """
    Overrides a page if the feature was disabled.

    :param self: The current view.
    :type self: nextcord.ui.View
    :param interaction: An interaction.
    :type interaction: nextcord.Interaction
    :return: None
    :rtype: None
    """
    # Only allow the back button
    for child in list(self.children):
        if isinstance(child, nextcord.ui.Button):
            if child.style == nextcord.ButtonStyle.danger or child.style == nextcord.ButtonStyle.red:
                child.label = "Back"
                continue
            else:
                self.remove_item(child)
    
    # Replace with error
    embed = nextcord.Embed(title = "Disabled Feature", description = "This feature has been disabled by the developers of InfiniBot. This is likely due to an critical instability with it right now. It will be re-enabled shortly after the issue has been resolved.", color = nextcord.Color.red())
    try: await interaction.response.edit_message(embed = embed, view = self)
    except: await interaction.response.send_message(embed = embed, view = self, ephemeral=True)

async def infinibot_loading_override(self: nextcord.ui.View, interaction: Interaction) -> None:
    """
    Overrides a page if the feature is still loading

    :param self: The current view.
    :type self: nextcord.ui.View
    :param interaction: An interaction.
    :type interaction: nextcord.Interaction
    :return: None
    :rtype: None
    """
    # Only allow the back button
    for child in list(self.children):
        if isinstance(child, nextcord.ui.Button):
            if child.style == nextcord.ButtonStyle.danger or child.style == nextcord.ButtonStyle.red:
                child.label = "Back"
                continue
            else:
                self.remove_item(child)
    
    # Replace with error
    embed = nextcord.Embed(title = "InfiniBot is still loading", 
                           description = "InfiniBot has been recently restarted. It is still coming back online. Please try again in a few minutes.", 
                           color = nextcord.Color.red())
    try: await interaction.response.edit_message(embed = embed, view = self)
    except: await interaction.response.send_message(embed = embed, view = self, ephemeral=True)


# Views and Modals for everything
class CustomView(nextcord.ui.View):
    """
    A custom view that handles exceptions raised in the view's item callbacks.

    It logs the exception with a unique ID and informs the user about the error with the ID.

    To use this class, simply subclass it and add your items to the view.

    :return: None
    :rtype: None
    """
    async def on_error(self, error: Exception, item, interaction: Interaction) -> None:
        """
        Handles exceptions raised in the view's item callbacks.

        :param error: The exception that was raised.
        :type error: Exception
        :param item: The item that was interacted with.
        :type item: nextcord.ui.Item
        :param interaction: The interaction that occurred.
        :type interaction: Interaction
        :return: None
        :rtype: None
        """
        # Generate a unique ID for the error
        error_id = get_uuid_for_logging()

        # Log the error with the unique ID
        logging.error(f"Error ID: {error_id} - Exception in view interaction", exc_info=error)

        # Inform the user about the error with the ID
        embed = nextcord.Embed(
            title = "Woops...",
            description = f"An unexpected error occurred. If the issue persists, please report it to the support team.",
            color = nextcord.Color.red()
        )
        embed.set_footer(text = f"View Interaction - Error ID: {error_id}")
        await interaction.response.send_message(
            embed=embed, ephemeral=True, view=SupportView()
        )

class CustomModal(nextcord.ui.Modal):
    """
    A custom modal that handles exceptions raised in the modal's execution.

    To use this class, simply subclass it and add your items to the modal.

    :return: None
    :rtype: None
    """
    async def on_error(self, error: Exception, interaction: Interaction) -> None:
        """
        Handles exceptions raised in the modal's execution.

        :param error: The exception that was raised.
        :type error: Exception
        :param interaction: The interaction that occurred.
        :type interaction: Interaction
        :return: None
        :rtype: None
        """
        # Generate a unique ID for the error
        error_id = get_uuid_for_logging()

        # Log the error with the unique ID
        logging.error(f"Error ID: {error_id} - Exception in modal interaction", exc_info=error)

        # Inform the user about the error with the ID
        embed = nextcord.Embed(
            title = "Woops...",
            description = f"An unexpected error occurred. If the issue persists, please report it to the support team.",
            color = nextcord.Color.red()
        )
        embed.set_footer(text = f"Modal Interaction - Error ID: {error_id}")
        await interaction.response.send_message(
            embed=embed, ephemeral=True, view=SupportView()
        )

# Error "Why Administrator Privileges?" Button
class ErrorWhyAdminPrivilegesButton(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
    
    @nextcord.ui.button(label = "Why Administrator Privileges?", style = nextcord.ButtonStyle.gray, custom_id = "why_administrator_privileges")
    async def event(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        global required_permissions

        # Generate required permissions ui
        required_permissions_ui = "\n**Text Channel Permissions:**"
        for permission in required_permissions["text_channel_permissions"]:
            required_permissions_ui += f"\n- {permission}"

        required_permissions_ui += "\n\n**Voice Channel Permissions:**"
        for permission in required_permissions["voice_channel_permissions"]:
            required_permissions_ui += f"\n- {permission}"

        required_permissions = f"{required_permissions_ui}"

        # Generate general message
        general_message = f"\n\n**Why Administrator Privileges?**\nSome of InfiniBot's features work best when it is able to view every channel and have all its required permissions in every channel. An alternative to Administrator is to give InfiniBot the following permissions in every channel: \n{required_permissions_ui}"
        
        embed = interaction.message.embeds[0]
        embed.description += general_message
        
        button.disabled = True
        
        await interaction.response.edit_message(view = self, embed = embed)

# View for handling selects with pagnation if needed
class SelectView(CustomView):
    """
    Creates a select view that has pages if needed.

    :param embed: The embed
    :type embed: nextcord.Embed
    :param options: Options of the Select
    :type options: list[nextcord.SelectOption]
    :param return_command: Command to call when finished. Returns a value if the user selected something.
                          Returns None if the user canceled.
    :type return_command: callable[[Interaction, str | None], None]
    :param placeholder: Placeholder for the Select. Defaults to None.
    :type placeholder: str | None
    :param continue_button_label: Continue Button Label. Defaults to "Continue".
    :type continue_button_label: str
    :param cancel_button_label: Cancel Button Label. Defaults to "Cancel".
    :type cancel_button_label: str
    :param preserve_order: Preserves the order of options. Defaults to False, where the options will be alphabetized.
    :type preserve_order: bool

    :raises ValueError: If the arguments are incorrect.

    Setup
    ------
    Call `await ~setup(nextcord.Interaction)` to begin setup.
    """
    def __init__(self, embed: nextcord.Embed, 
                 options: list[nextcord.SelectOption], 
                 return_command, 
                 placeholder: str = None, 
                 continue_button_label = "Continue", 
                 cancel_button_label = "Cancel", 
                 preserve_order = False) -> None:
        
        super().__init__()
        self.page = 0
        self.embed = embed
        self.options = options
        self.return_command = return_command
        
        # Confirm objects
        
    def __init__(self, embed: nextcord.Embed, 
                 options: list[nextcord.SelectOption], 
                 return_command, 
                 placeholder: str = None, 
                 continue_button_label = "Continue", 
                 cancel_button_label = "Cancel", 
                 preserve_order = False):
        
        super().__init__()
        self.page = 0
        self.embed = embed
        self.options = options
        self.return_command = return_command
        
        # Confirm objects
        if self.options == None or self.options == []:
            raise ValueError(f"'options' must be a 'list' with one or more 'nextcord.SelectOption' items.")       
        if type(self.options) != list:
            raise ValueError(f"'options' must be of type 'list'. Recieved type '{type(self.options)}'")        
        for option in self.options:
            if type(option) != nextcord.SelectOption:
                raise ValueError(f"'options' must only contain 'nextcord.SelectOption' items. Countained 1+ '{type(option)}'")
            
        # Remove Unknowns
        if not self.embed.description: self.embed.description = ""
        confirmed_options = []
        for option in self.options:
            if option == None: continue
            if not isinstance(option, nextcord.SelectOption): continue
            if option.label == None: continue
            if option.value == None: continue
            confirmed_options.append(option)
        self.options = confirmed_options
        
        # Alphabetize options
        if not preserve_order:
            # For some reason, this is how we have to do it to sort and get all "__" values at the top.
            self.options = sorted(self.options, key=lambda option: [not(isinstance(option.value, str) and option.value.startswith("__")), option.label.lower()])
        
        
        # Parse options into different pages
        self.select_options = [[]]
        xindex = 0
        yindex = 0
        for option in self.options:
            if yindex == 25:    # <--------------------------- Change the Threshold HERE!!!!
                # Create new page
                self.select_options.append([])
                xindex += 1
                yindex = 0
            # Add to current page
            self.select_options[xindex].append(option)
            yindex += 1
            
        del xindex, yindex
        
        # Add select menu
        self.select = nextcord.ui.Select(options = [nextcord.SelectOption(label = "PLACEHOLDER!!!")], placeholder=placeholder)
        self.add_item(self.select)
        
        # Add buttons
        self.back_btn = nextcord.ui.Button(emoji = "◀️", style = nextcord.ButtonStyle.gray, row = 1, disabled = True)
        self.back_btn.callback = self.back
        
        self.next_btn = nextcord.ui.Button(emoji = "▶️", style = nextcord.ButtonStyle.gray, row = 1)
        self.next_btn.callback = self.next
        
        if len(self.select_options) > 1: # If we need pages
            self.add_item(self.back_btn)
            self.add_item(self.next_btn)
        
        self.cancel_btn = nextcord.ui.Button(label = cancel_button_label, style = nextcord.ButtonStyle.danger, row = 2)
        self.cancel_btn.callback = self.cancelButtonCallback
        self.add_item(self.cancel_btn)
        
        self.continue_btn = nextcord.ui.Button(label = continue_button_label, style = nextcord.ButtonStyle.blurple, row = 2)
        self.continue_btn.callback = self.continueButtonCallback
        self.add_item(self.continue_btn)
        
    async def setup(self, interaction):
        await self.setPage(interaction, 0)
        
    async def setPage(self, interaction: Interaction, page: int):
        if page >= len(self.select_options): raise IndexError("Page (int) was out of bounds of self.selectOptions (list[nextcord.SelectOption]).")
        
        embed = copy.copy(self.embed)
        if len(self.select_options) > 1: # If we don't need pages, don't bother the user with pages.
            embed.description += f"\n\n**Page {page + 1} of {len(self.select_options)}**\n{self.select_options[page][0].label} → {self.select_options[page][-1].label}"
        
        self.select.options = self.select_options[page]

        if interaction != None: 
            await interaction.response.edit_message(embed = embed, view = self) 
            self.page = page
            return True
        
        return False
    
    
    async def back(self, interaction: Interaction):
        if self.page == 0: return
        
        #check to see if the back button *will* become unusable...
        self.back_btn.disabled = False
        self.next_btn.disabled = False
        if self.page - 1 == 0: self.back_btn.disabled = True
        else: self.next_btn.disabled = False
        
        #set the page
        await self.setPage(interaction, self.page - 1)
        
    async def next(self, interaction: Interaction):
        if self.page == (len(self.select_options) - 1): return
        
        #check to see if the next button *will* become unusable...
        self.back_btn.disabled = False
        self.next_btn.disabled = False
        if self.page + 1 == (len(self.select_options) - 1): self.next_btn.disabled = True
        else: self.back_btn.disabled = False
        
        #set the page
        await self.setPage(interaction, self.page + 1)
        
    
    async def cancelButtonCallback(self, interaction: Interaction):
        await self.return_command(interaction, None)
    
    async def continueButtonCallback(self, interaction: Interaction):
        if len(self.select.values) == 0: return
        await self.return_command(interaction, self.select.values[0])   


# Common Add-On Views
class SupportView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        supportServerBtn = nextcord.ui.Button(label = "Support Server", style = nextcord.ButtonStyle.link, url = get_configs()["links"]["support_server_invite_link"])
        self.add_item(supportServerBtn)

class InviteView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        inviteBtn = nextcord.ui.Button(label = "Add to Your Server", style = nextcord.ButtonStyle.link, url = get_configs()["links"]["bot_invite_link"])
        self.add_item(inviteBtn)

class SupportAndInviteView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        supportServerBtn = nextcord.ui.Button(label = "Support Server", style = nextcord.ButtonStyle.link, url = get_configs()["links"]["support_server_invite_link"])
        self.add_item(supportServerBtn)
        
        inviteBtn = nextcord.ui.Button(label = "Add To Your Server", style = nextcord.ButtonStyle.link, url = get_configs()["links"]["bot_invite_link"])
        self.add_item(inviteBtn)

class SupportInviteAndTopGGVoteView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        supportServerBtn = nextcord.ui.Button(label = "Support Server", style = nextcord.ButtonStyle.link, url = get_configs()["links"]["support_server_invite_link"])
        self.add_item(supportServerBtn)
        
        inviteBtn = nextcord.ui.Button(label = "Invite", style = nextcord.ButtonStyle.link, url = get_configs()["links"]["bot_invite_link"])
        self.add_item(inviteBtn)
        
        topGGVoteBtn = nextcord.ui.Button(label = "Vote for InfiniBot", style = nextcord.ButtonStyle.link, url = get_configs()["links"]["topgg_review_link"])
        self.add_item(topGGVoteBtn)
        
class SupportInviteAndTopGGReviewView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        supportServerBtn = nextcord.ui.Button(label = "Support Server", style = nextcord.ButtonStyle.link, url = get_configs()["links"]["support_server_invite_link"])
        self.add_item(supportServerBtn)
        
        inviteBtn = nextcord.ui.Button(label = "Invite", style = nextcord.ButtonStyle.link, url = get_configs()["links"]["bot_invite_link"])
        self.add_item(inviteBtn)
        
        topGGReviewBtn = nextcord.ui.Button(label = "Leave a Review", style = nextcord.ButtonStyle.link, url = get_configs()["links"]["topgg_review_link"])
        self.add_item(topGGReviewBtn)

class TopGGVoteView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        topGGVoteBtn = nextcord.ui.Button(label = "Vote", style = nextcord.ButtonStyle.link, url = get_configs()["links"]["topgg_vote_link"])
        self.add_item(topGGVoteBtn)
        
class TopGGAll(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        topGG = nextcord.ui.Button(label = "Visit on Top.GG", style = nextcord.ButtonStyle.link, url = get_configs()["links"]["topgg_link"])
        self.add_item(topGG)
        
        topGGVoteBtn = nextcord.ui.Button(label = "Vote for InfiniBot", style = nextcord.ButtonStyle.link, url = get_configs()["links"]["topgg_vote_link"])
        self.add_item(topGGVoteBtn)
        
        topGGReviewBtn = nextcord.ui.Button(label = "Leave a Review", style = nextcord.ButtonStyle.link, url = get_configs()["links"]["topgg_review_link"])
        self.add_item(topGGReviewBtn)