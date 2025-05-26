from nextcord import Interaction
import nextcord
import logging
import asyncio
import datetime

from components import utils, ui_components
from config.global_settings import (
    is_channel_purging,
    add_channel_to_purging,
    remove_channel_from_purging,
    ShardLoadedStatus
)
from config.server import Server


class ConfirmationView(nextcord.ui.View):
    """UI view for user confirmation with Cancel/Continue buttons.
    
    Provides a simple interface for users to confirm or cancel an action.
    The view automatically disables buttons after selection and cleans up.
    """
    
    def __init__(self):
        super().__init__(timeout=None)
        self.choice = None

        # Create Cancel button
        cancel_button = nextcord.ui.Button(label="Cancel", style=nextcord.ButtonStyle.red)
        cancel_button.callback = self.no_callback
        self.add_item(cancel_button)

        # Create Continue button
        continue_button = nextcord.ui.Button(label="Continue", style=nextcord.ButtonStyle.green)
        continue_button.callback = self.yes_callback
        self.add_item(continue_button)

    async def no_callback(self, interaction: Interaction):
        await self._handle_response(interaction, False)

    async def yes_callback(self, interaction: Interaction):
        await self._handle_response(interaction, True)

    async def _handle_response(self, interaction: Interaction, choice: bool):
        """Process user's choice and clean up the view.
        
        :param interaction: The Discord interaction object
        :type interaction: Interaction
        :param choice: True if user confirmed, False if cancelled
        :type choice: bool
        :return: None
        :rtype: None
        """
        self.choice = choice
        
        # Disable all buttons to prevent further interaction
        for child in self.children:
            if isinstance(child, nextcord.ui.Button):
                child.disabled = True
                
        await interaction.response.edit_message(view=self, delete_after=1.0)
        self.stop()


async def _send_error(interaction: Interaction, title: str, description: str) -> None:
    """Send an error embed to the user.
    
    :param interaction: The Discord interaction
    :type interaction: Interaction
    :param title: Error title
    :type title: str
    :param description: Error description
    :type description: str
    :rtype: None
    """
    embed = nextcord.Embed(title=title, description=description, color=nextcord.Color.red())
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ---------------------------
# Purge Handlers
# ---------------------------

async def _handle_purge_all(interaction: Interaction) -> None:
    """Handle complete channel purge by cloning the channel and deleting the original.
    
    :param interaction: The Discord interaction object
    :type interaction: Interaction
    :return: None
    :rtype: None
    """
    # Validate bot permissions for channel management
    if not interaction.channel.permissions_for(interaction.guild.me).manage_channels:
        await _send_error(
            interaction,
            "Permission Error",
            "InfiniBot needs Manage Channels permission to purge entire channels."
        )
        return

    try:
        # Clone the current channel
        new_channel = await interaction.channel.clone(
            reason="Purging Channel - Cloning original channel."
        )
        # Position the new channel after the original
        await new_channel.edit(
            position=interaction.channel.position + 1,
            reason="Purging Channel - Positioning to maintain order."
        )
    except nextcord.Forbidden:
        await _send_error(
            interaction,
            "Cloning Failed",
            "Missing permissions to clone channel. Please check bot permissions."
        )
        return

    # Update server configurations to use the new channel
    try:
        server = Server(interaction.guild.id)
        _update_server_configurations(server, interaction.channel.id, new_channel.id)
        await _update_system_channel(interaction.guild, interaction.channel, new_channel)
    except Exception as e:
        logging.error(f"Configuration update error: {e}")

    # Delete the original channel
    try:
        await interaction.channel.delete(reason="Purging Channel")
    except nextcord.Forbidden:
        await _send_error(
            interaction,
            "Deletion Failed",
            "Failed to delete original channel. You may need to manually remove cloned channels."
        )
        return

    # Send confirmation message in the new channel
    await new_channel.send(
        embed=nextcord.Embed(
            title="Purged Messages",
            description=f"{interaction.user} has instantly purged {new_channel.mention}",
            color=nextcord.Color.orange(),
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc)
        ),
        view=ui_components.InviteView()
    )

def _update_server_configurations(server: Server, old_id: int, new_id: int) -> None:
    """Update server configurations to replace old channel ID with new channel ID.
    
    :param server: The server configuration object
    :type server: Server
    :param old_id: The ID of the old channel being replaced
    :type old_id: int
    :param new_id: The ID of the new channel to use
    :type new_id: int
    :return: None
    :rtype: None
    """
    # Define configuration paths that store single channel IDs
    config_paths = [
        "profanity_moderation_profile.channel",
        "logging_profile.channel", 
        "leveling_profile.channel",
        "join_message_profile.channel",
        "leave_message_profile.channel",
        "birthdays_profile.channel"
    ]
    
    # Define configuration paths that store lists of channel IDs
    list_paths = [
        "leveling_profile.exempt_channels",
        "join_to_create_vcs.channels"
    ]

    # Helper function to get nested attribute value
    def get_nested_attr(obj, path: str):
        parts = path.split('.')
        for part in parts:
            obj = getattr(obj, part)
        return obj

    # Helper function to set nested attribute value
    def set_nested_attr(obj, path: str, value):
        parts = path.split('.')
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)

    # Update direct channel ID references
    for path in config_paths:
        if get_nested_attr(server, path) == old_id:
            set_nested_attr(server, path, new_id)

    # Update channel ID references in lists
    for path in list_paths:
        items = get_nested_attr(server, path)
        if old_id in items:
            updated_items = [new_id if x == old_id else x for x in items]
            set_nested_attr(server, path, updated_items)

async def _update_system_channel(guild: nextcord.Guild, old_channel: nextcord.TextChannel, new_channel: nextcord.TextChannel) -> None:
    """Update the guild's system channel if it matches the old channel.
    
    :param guild: The Discord guild to update
    :type guild: nextcord.Guild
    :param old_channel: The channel being replaced
    :type old_channel: nextcord.TextChannel
    :param new_channel: The new channel to set as system channel
    :type new_channel: nextcord.TextChannel
    :return: None
    :rtype: None
    """
    if guild.system_channel and guild.system_channel.id == old_channel.id:
        if not guild.me.guild_permissions.manage_guild:
            await utils.send_error_message_to_server_owner(
                guild,
                "Manage Server",
                "InfiniBot needs Manage Server permission to update system channel."
            )
        else:
            await guild.edit(
                system_channel=new_channel,
                reason="Purging Channel - System Channel Transfer"
            )

async def _handle_purge_amount(interaction: Interaction, amount: int) -> None:
    """Handle purging a specific number of messages from the channel.
    
    :param interaction: The Discord interaction object
    :type interaction: Interaction
    :param amount: The number of messages to purge
    :type amount: int
    :return: None
    :rtype: None
    """
    # Check if channel is already being purged
    if is_channel_purging(interaction.guild_id):
        await _send_error(
            interaction,
            "Purging Error",
            "This channel is already being purged."
        )
        return

    # Mark channel as being purged to prevent concurrent operations
    add_channel_to_purging(interaction.guild_id)
    
    try:
        # Perform the message deletion
        deleted = await interaction.channel.purge(limit=amount)
    except Exception as e:
        remove_channel_from_purging(interaction.guild_id)
        logging.error(f"Purge error: {e}")
        await _send_error(
            interaction,
            "Purge Failed",
            "An error occurred during message deletion. Please check bot permissions."
        )
        return
    finally:
        # Brief delay before cleanup to ensure operation completes
        await asyncio.sleep(1)
        remove_channel_from_purging(interaction.guild_id)

    # Send confirmation of successful purge
    await interaction.channel.send(
        embed=nextcord.Embed(
            title="Purged Messages",
            description=f"{interaction.user} purged {len(deleted)} messages in {interaction.channel.mention}",
            color=nextcord.Color.orange(),
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc)
        ),
        view=ui_components.InviteView()
    )

# ---------------------------
# Main Command Handler
# ---------------------------

async def run_purge_command(interaction: Interaction, amount: str) -> None:
    """Handle purge command with proper validation and user confirmation.
    
    :param interaction: The Discord interaction object
    :type interaction: Interaction
    :param amount: The amount to purge ('all' or a number)
    :type amount: str
    :return: None
    :rtype: None
    """
    # Check basic permissions
    if not interaction.channel.permissions_for(interaction.guild.me).manage_messages:
        await _send_error(
            interaction,
            "Permission Error",
            "InfiniBot needs Manage Messages permission to purge messages."
        )
        return
    
    # Check user permissions
    if not await utils.user_has_config_permissions(interaction): 
        return
    
    # Check if feature is enabled
    if not utils.feature_is_active(guild_id=interaction.guild.id, feature="purging"):
        await _send_error(
            interaction,
            "Feature Disabled",
            "Purging has been disabled. Check the dashboard to enable it."
        )
        return
    
    # Check if bot is loaded
    with ShardLoadedStatus() as shards_loaded:
        if not interaction.guild.shard_id in shards_loaded:
            logging.warning(f"Dashboard: Shard {interaction.guild.shard_id} is not loaded. Forwarding to inactive screen for guild {interaction.guild.id}.")
            await _send_error(interaction, ui_components.INFINIBOT_LOADING_EMBED.title, ui_components.INFINIBOT_LOADING_EMBED.description)
            return

    # Validate input
    if not amount or (not amount.isdigit() and amount.lower() != "all") or (amount.isdigit() and int(amount) < 1):
        await _send_error(
            interaction,
            "Invalid Amount",
            "Please specify a positive number or 'all' to purge messages."
        )
        return

    # Handle purge types with confirmation
    if amount.lower() == "all":
        # Create confirmation embed for complete purge
        confirm_embed = nextcord.Embed(
            title="Confirm Complete Purge",
            description=(
                "**WARNING**: This will clone the channel and delete the original!\n"
                "Third-party integrations may be affected. This action cannot be undone.\n\n"
                "For more information: [Check our documentation](https://cypress-exe.github.io/InfiniBot/docs/additional/purging/)"
            ),
            color=nextcord.Color.red()
        )
        confirm_embed.set_footer(text="Use with caution - this is irreversible!")
        
        # Get user confirmation
        view = ConfirmationView()
        await interaction.response.send_message(embed=confirm_embed, view=view, ephemeral=True)
        await view.wait()
        
        if not view.choice:
            return

        await _handle_purge_all(interaction)
    else:
        # Create confirmation embed for message purge
        confirm_embed = nextcord.Embed(
            title="Confirm Message Purge",
            description=(
                f"You're about to delete {amount} messages. This cannot be undone.\n\n"
                f"For more information: [Check our documentation](https://cypress-exe.github.io/InfiniBot/docs/additional/purging/)"
            ),
            color=nextcord.Color.orange()
        )
        
        # Get user confirmation
        view = ConfirmationView()
        await interaction.response.send_message(embed=confirm_embed, view=view, ephemeral=True)
        await view.wait()
        
        if not view.choice:
            return

        await _handle_purge_amount(interaction, int(amount))