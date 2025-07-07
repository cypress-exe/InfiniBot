import nextcord
import logging

from components import utils
from components.ui_components import CustomView
from config.server import Server

from config.global_settings import get_configs, get_bot_load_status
from features.check_infinibot_permissions import run_check_infinibot_permissions, create_permissions_report_embed
from features.onboarding import run_onboarding_command

# ======================================== SERVER JOIN ========================================
class NewServerJoinView(CustomView):
    def __init__(self):
        super().__init__(timeout = None)
        
        support_server_btn = nextcord.ui.Button(label="Support Server", style=nextcord.ButtonStyle.link, url=get_configs()["links.support-server-invite-link"])
        self.add_item(support_server_btn)
        
        invite_btn = nextcord.ui.Button(label="Add to Your Server", style=nextcord.ButtonStyle.link, url=get_configs()["links.bot-invite-link"])
        self.add_item(invite_btn)
        
        topGG_vote_btn = nextcord.ui.Button(label="Vote for InfiniBot", style=nextcord.ButtonStyle.link, url=get_configs()["links.topgg-review-link"])
        self.add_item(topGG_vote_btn)

        check_permissions_btn = nextcord.ui.Button(label="Check InfiniBot Permissions", style=nextcord.ButtonStyle.gray, custom_id="check_infinibot_permissions")
        check_permissions_btn.callback = run_check_infinibot_permissions
        self.add_item(check_permissions_btn)

        start_onboarding_btn = nextcord.ui.Button(label="Start Onboarding", style=nextcord.ButtonStyle.blurple, custom_id="start_onboarding", row=1)
        start_onboarding_btn.callback = run_onboarding_command
        self.add_item(start_onboarding_btn)

class ResendSetupMessageView(CustomView):
    def __init__(self):
        super().__init__(timeout = None)
        
        resend_setup_message_btn = nextcord.ui.Button(label="Resend Setup Message", style=nextcord.ButtonStyle.blurple, custom_id="resend_setup_message")
        resend_setup_message_btn.callback = handle_resend_setup_message
        self.add_item(resend_setup_message_btn)

        support_server_btn = nextcord.ui.Button(label="Stuck? Go to Support Server", style=nextcord.ButtonStyle.link, url=get_configs()["links.support-server-invite-link"])
        self.add_item(support_server_btn)

async def handle_resend_setup_message(interaction: nextcord.Interaction):
    """
    Handles the resend setup message button click.
    This function is triggered when the user clicks the "Resend Setup Message" button.
    It sends the setup message again to the server owner or a designated channel.

    :param interaction: The interaction object containing information about the button click.
    :type interaction: nextcord.Interaction
    :return: None
    :rtype: None
    """
    guild_id = int(interaction.message.embeds[0].footer.text)
    
    from core.bot import get_bot
    guild = get_bot().get_guild(guild_id)
    
    if guild is None:
        logging.error(f"Guild with ID {guild_id} not found when trying to resend setup message.", exc_info=True)
        raise ValueError(f"Server not found. Please ensure InfiniBot is still in the server.")

    # Send the setup message again
    logging.info(f"Resending setup message to the server {guild.name} (ID: {guild.id}).")
    await handle_server_join(guild)

    # If the code gets here, it means the setup message was successfully resent
    await interaction.response.edit_message(
        embed=nextcord.Embed(
            title="Setup Message Resent",
            description="The setup message has been resent successfully. Please check your server for a message from InfiniBot.",
            color=nextcord.Color.green()
        ),
        view=None
    )

async def handle_server_join(guild: nextcord.Guild) -> None:
    """
    Handles guild join events when InfiniBot is added to a new server.
    
    This function performs the following actions:
    1. Logs the guild join event
    2. Creates necessary roles (InfiniBot Mod role)
    3. Checks bot permissions and generates reports
    4. Sends welcome message with setup information
    5. Falls back to DM if no suitable channel is found
    
    Args:
        guild: The guild that InfiniBot has joined
    """
    logging.info(f"InfiniBot joined server '{guild.name}' (ID: {guild.id})")
    
    # Prepare roles and mentions
    infinibot_mod_role = await utils.get_infinibot_mod_role(guild)
    infinibot_role = utils.get_infinibot_top_role(guild)
    
    infinibot_mod_mention = infinibot_mod_role.mention if infinibot_mod_role else "@InfiniBot Mod"
    infinibot_role_mention = infinibot_role.mention if infinibot_role else "@InfiniBot"
    
    # Build embeds for the welcome message
    embeds = []
    
    # Create welcome embed
    embeds.append(_create_welcome_embed(infinibot_mod_mention, infinibot_role_mention))
    
    # Add permissions report if needed
    permissions_embed = _create_permissions_embed(guild)
    if permissions_embed:
        embeds.append(permissions_embed)
    
    # Add role creation error if needed
    role_error_embed = _create_role_creation_error_embed(guild, infinibot_mod_role)
    if role_error_embed:
        embeds.append(role_error_embed)
    
    # Send message to channel or fallback to DM
    await _send_welcome_message(guild, embeds)

def _create_welcome_embed(infinibot_mod_mention: str, infinibot_role_mention: str) -> nextcord.Embed:
    """Create the main welcome embed with setup instructions."""
    configs = get_configs()
    
    welcome_message = f"""
    Hello! I'm InfiniBot! Here's what you need to know:
    
    🎯 **Quick Setup:**
    1) Assign the role {infinibot_mod_mention} to anyone for exclusive admin features!
    2) Ensure the {infinibot_role_mention} role is positioned high up in the roles hierarchy, or give InfiniBot the Administrator permission
    
    🚀 **Get Started:**
    Click "Start Onboarding" below to configure your server!
    
    📞 **Need Help?**
    Join our support server or contact us:
    • Support: {configs["links.support-server-invite-link"]}
    • Email: {configs["links.support-email"]}
    """
    
    # Clean up indentation for mobile compatibility
    welcome_message = utils.standardize_str_indention(welcome_message)
    
    return nextcord.Embed(
        title="🎉 Welcome to InfiniBot!",
        description=welcome_message,
        color=nextcord.Color.gold()
    )

def _create_permissions_embed(guild: nextcord.Guild) -> nextcord.Embed | None:
    """Create permissions report embed if there are missing permissions."""
    missing_global_perms, missing_channel_perms = utils.get_infinibot_missing_permissions(guild)
    return create_permissions_report_embed(missing_global_perms, missing_channel_perms)

def _create_role_creation_error_embed(guild: nextcord.Guild, infinibot_mod_role: nextcord.Role | None) -> nextcord.Embed | None:
    """Create error embed if InfiniBot Mod role couldn't be created."""
    if guild.me.guild_permissions.manage_roles or infinibot_mod_role is not None:
        return None
    
    return nextcord.Embed(
        title="⚠️ Role Creation Issue",
        description=(
            "InfiniBot couldn't create the **InfiniBot Mod** role due to missing permissions.\n\n"
            "**To fix this:**\n"
            "• Grant InfiniBot the `Manage Roles` permission\n"
            "• The role will appear automatically once permission is granted"
        ),
        color=nextcord.Color.orange()
    )

async def _send_welcome_message(guild: nextcord.Guild, embeds: list[nextcord.Embed]) -> None:
    """Send welcome message to a suitable channel or fallback to DM."""
    view = NewServerJoinView()
    channel = await utils.get_available_channel(guild)
    
    if channel is not None:
        # Successfully found a channel to send to
        await channel.send(embeds=embeds, view=view)
        logging.info(f"Welcome message sent to #{channel.name} in '{guild.name}'")
    else:
        # Fallback: Send DM to server owner
        await _send_fallback_dm(guild, view)

async def _send_fallback_dm(guild: nextcord.Guild, view: NewServerJoinView) -> None:
    """Send fallback DM to server owner when no suitable channel is found."""
    try:
        fallback_embed = nextcord.Embed(
            title="🤖 InfiniBot Joined Your Server",
            description=(
                "InfiniBot has joined your server but couldn't find a suitable channel for the setup message.\n\n"
                "**To resolve this:**\n"
                "• Ensure InfiniBot can view and send messages in at least one channel\n"
                "• Click the button below to resend the setup message once fixed"
            ),
            color=nextcord.Color.red()
        )
        fallback_embed.set_footer(text=str(guild.id))
        
        await guild.owner.send(embed=fallback_embed, view=ResendSetupMessageView())
        logging.info(f"Fallback DM sent to owner of '{guild.name}' due to no accessible channels")
        
    except Exception as err:
        logging.error(
            f"Failed to send welcome message or fallback DM for guild '{guild.name}' (ID: {guild.id}): {err}",
            exc_info=True
        )

# ======================================== SERVER LEAVE ========================================
async def handle_server_remove(guild: nextcord.Guild):
    """
    Handles guild removal events.
    This function is triggered when the bot is removed from a guild. It performs the following actions:
    1. Logs the guild removal event.
    2. Deletes the server's data from the database.

    :param guild: The guild that the bot has been removed from.
    :type guild: nextcord.Guild
    :return: None
    :rtype: None
    """

    # Don't run if InfiniBot is still loading
    if not get_bot_load_status():
        logging.info(f"Skipping server removal handling for {guild.name} (ID: {guild.id}) because InfiniBot is still loading.")
        return
    
    logging.info(f"InfiniBot has been removed from the server {guild.name} (ID: {guild.id}).") # Info log for now. Maybe change to debug later.
    
    # Remove all other server data
    Server(guild.id).remove_all_data()