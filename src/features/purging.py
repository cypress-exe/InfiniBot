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

# ---------------------------
# Helper Classes
# ---------------------------

class ConfirmationView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.choice = None

        self._create_button("Cancel", nextcord.ButtonStyle.red, self.no_callback)
        self._create_button("Continue", nextcord.ButtonStyle.green, self.yes_callback)

    def _create_button(self, label: str, style: nextcord.ButtonStyle, callback):
        button = nextcord.ui.Button(
            label=label, 
            style=style
        )
        button.callback = callback
        self.add_item(button)

    async def no_callback(self, interaction: Interaction):
        await self._handle_response(interaction, False)

    async def yes_callback(self, interaction: Interaction):
        await self._handle_response(interaction, True)

    async def _handle_response(self, interaction: Interaction, choice: bool):
        self.choice = choice
        self.disable_all_buttons()
        await interaction.response.edit_message(view=self, delete_after=1.0)
        self.stop()

    def disable_all_buttons(self):
        """Disables all buttons in the view"""
        for child in self.children:
            if isinstance(child, nextcord.ui.Button):
                child.disabled = True

# ---------------------------
# Helper Functions
# ---------------------------

async def _send_error(interaction: Interaction, title: str, description: str) -> None:
    """Helper to send error embeds"""
    embed = nextcord.Embed(title=title, description=description, color=nextcord.Color.red())
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)

def _create_confirmation_embed(title: str, description: str) -> nextcord.Embed:
    """Creates a standardized confirmation embed"""
    return nextcord.Embed(
        title=title,
        description=description,
        color=nextcord.Color.orange()
    )

async def _get_user_confirmation(interaction: Interaction, embed: nextcord.Embed) -> bool:
    """Gets user confirmation through a view"""
    view = ConfirmationView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    await view.wait()
    return view.choice or False

# ---------------------------
# Permission Checks
# ---------------------------

async def _check_permissions(interaction: Interaction) -> bool:
    """Validates required permissions and bot status"""
    # User permissions
    if not interaction.user.guild_permissions.manage_messages:
        await _send_error(
            interaction,
            "Permission Error",
            "You need the \"manage messages\" permission to use this command."
        )
        return False

    # Bot shard status
    with ShardLoadedStatus() as shards_loaded:
        if interaction.guild.shard_id not in shards_loaded:
            await _send_error(
                interaction,
                "InfiniBot Still Loading",
                "Please try again in a few minutes."
            )
            return False

    return True

async def _check_feature_status(interaction: Interaction) -> bool:
    """Checks if purging feature is enabled"""
    if not utils.feature_is_active(feature="purging", guild_id=interaction.guild.id):
        await _send_error(
            interaction,
            "Purging Disabled",
            "Purging is temporarily disabled due to stability issues. Please check back later."
        )
        return False
    return True

# ---------------------------
# Purge Handlers
# ---------------------------

async def _handle_purge_all(interaction: Interaction) -> None:
    """Handles complete channel purge through cloning"""
    # Validate bot permissions
    if not interaction.channel.permissions_for(interaction.guild.me).manage_channels:
        await _send_error(
            interaction,
            "Permission Error",
            "InfiniBot needs Manage Channels permission to purge entire channels."
        )
        return

    try:
        # Clone channel
        new_channel = await interaction.channel.clone(
            reason="Purging Channel"
        )
        await new_channel.edit(
            position=interaction.channel.position + 1,
            reason="Purging Channel"
        )
    except nextcord.Forbidden:
        await _send_error(
            interaction,
            "Cloning Failed",
            "Missing permissions to clone channel. Please check bot permissions."
        )
        return

    # Update server configurations
    try:
        server = Server(interaction.guild.id)
        _update_server_configurations(server, interaction.channel.id, new_channel.id)
        await _update_system_channel(interaction.guild, interaction.channel, new_channel)
    except Exception as e:
        logging.error(f"Configuration update error: {e}")

    # Delete original channel
    try:
        await interaction.channel.delete(reason="Purging Channel")
    except nextcord.Forbidden:
        await _send_error(
            interaction,
            "Deletion Failed",
            "Failed to delete original channel. You may need to manually remove cloned channels."
        )
        return

    # Send confirmation message
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
    """Updates server configurations with new channel ID"""
    config_paths = [
        "profanity_moderation_profile.channel",
        "logging_profile.channel",
        "leveling_profile.channel",
        "join_message_profile.channel",
        "leave_message_profile.channel",
        "birthdays_profile.channel"
    ]
    list_paths = [
        "leveling_profile.exempt_channels", 
        "join_to_create_vcs.channels"
    ]

    # Update direct references
    for path in config_paths:
        if _get_nested_attr(server, path) == old_id:
            _set_nested_attr(server, path, new_id)

    # Update list references
    for path in list_paths:
        items = _get_nested_attr(server, path)
        if old_id in items:
            items = [new_id if x == old_id else x for x in items]
            _set_nested_attr(server, path, items)

def _get_nested_attr(obj, path: str):
    parts = path.split('.')
    for part in parts:
        obj = getattr(obj, part)
    return obj

def _set_nested_attr(obj, path: str, value):
    parts = path.split('.')
    for part in parts[:-1]:
        obj = getattr(obj, part)
    setattr(obj, parts[-1], value)

async def _update_system_channel(guild: nextcord.Guild, old_channel: nextcord.TextChannel, new_channel: nextcord.TextChannel) -> None:
    """Updates system channel if needed"""
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
    """Handles purging a specific number of messages"""
    if is_channel_purging(interaction.guild_id):
        await _send_error(
            interaction,
            "Purging Error",
            "This channel is already being purged."
        )
        return

    add_channel_to_purging(interaction.guild_id)
    
    try:
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
        await asyncio.sleep(1)
        remove_channel_from_purging(interaction.guild_id)

    # Send purge confirmation
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
    # Initial validations
    if not await _check_permissions(interaction):
        return

    if not await utils.user_has_config_permissions(interaction):
        return

    if not await _check_feature_status(interaction):
        return

    # Input validation
    if not amount or (not amount.isdigit() and amount.lower() != "all") or (amount.isdigit() and int(amount) < 1):
        await _send_error(
            interaction,
            "Invalid Amount",
            "Please specify a positive number or 'all' to purge messages."
        )
        return

    # Handle purge type
    if amount.lower() == "all":
        confirm_embed = _create_confirmation_embed(
            "Confirm Complete Purge",
            "**WARNING**: This will clone the channel and delete the original!\n"
            "Third-party integrations may be affected. This action cannot be undone."
        )
        confirm_embed.set_footer(text="Use with caution - this is irreversible")
        
        if not await _get_user_confirmation(interaction, confirm_embed):
            return

        await _handle_purge_all(interaction)
    else:
        confirm_embed = _create_confirmation_embed(
            "Confirm Message Purge",
            f"You're about to delete {amount} messages. This cannot be undone."
        )
        
        if not await _get_user_confirmation(interaction, confirm_embed):
            return

        await _handle_purge_amount(interaction, int(amount))