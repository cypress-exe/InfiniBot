import nextcord
from nextcord import Interaction

from components.ui_components import CustomView
from components.utils import get_infinibot_missing_permissions
from config.global_settings import get_configs



class InfiniBotPermissionsReportView(CustomView):
    def __init__(self):
        super().__init__(timeout = None)
        
        support_server_btn = nextcord.ui.Button(label = "Support Server", style = nextcord.ButtonStyle.link, url = get_configs()["links"]["support-server-invite-link"])
        self.add_item(support_server_btn)

        refresh_btn = nextcord.ui.Button(label = "Refresh", style = nextcord.ButtonStyle.gray, custom_id = "refresh_infinibot_permissions_report")
        refresh_btn.callback = lambda interaction: run_check_infinibot_permissions(interaction, edit_message=True)
        self.add_item(refresh_btn)

def create_permissions_report_embed(guild_permissions: list, channel_permissions: list) -> nextcord.Embed | None:
    """
    Create a clean, well-formatted embed for the InfiniBot permissions report.
    
    Args:
        guild_permissions: List of missing guild-level permissions
        channel_permissions: List of tuples containing (channel, missing_permissions_list)
    
    Returns:
        nextcord.Embed: The permissions report embed, or None if all permissions are present
    """
    # Return None if no missing permissions (success case handled elsewhere)
    if not guild_permissions and not channel_permissions:
        return None
    
    embed = nextcord.Embed(
        title="🔒 InfiniBot Permission Report",
        color=nextcord.Color.orange()
    )
    
    # Count total missing permissions
    total_missing = len(guild_permissions) + sum(len(perms) for _, perms in channel_permissions)
    
    # Add main description with summary
    main_description = f"InfiniBot is missing **{total_missing}** permission(s) to function properly.\n"
    
    # Add quick fix tip for many missing permissions
    if total_missing > 5:
        main_description += "\n💡 **Quick Fix:** Give InfiniBot the `Administrator` permission to resolve all issues instantly. Alternatively, proceed with the steps below.\n\n"
    
    embed.description = main_description
    
    # Add server permissions field if any exist
    if guild_permissions:
        # Limit display to prevent embed overflow
        display_perms = guild_permissions[:8]
        remaining_count = len(guild_permissions) - len(display_perms)
        
        permission_text = "\n".join(f"• `{perm}`" for perm in display_perms)
        if remaining_count > 0:
            permission_text += f"\n• *...and {remaining_count} more*"
        
        embed.add_field(
            name="🌐  Server Permissions",
            value=f"Grant these to the **InfiniBot** role:\n{permission_text}",
            inline=False
        )
    
    # Add channel permissions fields if any exist
    if channel_permissions:
        embed.add_field(
            name="📺  Channel Permissions",
            value="Grant InfiniBot these permissions in the below channels.",
            inline=False
        )
        # Group channels by their missing permissions to reduce clutter
        channels_by_perms = {}
        for channel, perms in channel_permissions:
            perms_key = tuple(perms)
            if perms_key not in channels_by_perms:
                channels_by_perms[perms_key] = []
            channels_by_perms[perms_key].append(channel)
        
        # Display up to 2 channel permission groups
        displayed_groups = 0
        
        for perms_tuple, channels in list(channels_by_perms.items())[:2]:
            displayed_groups += 1
            
            # Format channel list (limit to 3 channels per group)
            channel_list = channels[:3]
            remaining_channels = len(channels) - len(channel_list)
            
            channel_names = ", ".join(f"{ch.mention}" for ch in channel_list)
            if remaining_channels > 0:
                channel_names += f" *+{remaining_channels} more*"
            
            # Format permissions list (limit to 4 permissions per group)
            perms_list = list(perms_tuple)[:4]
            remaining_perms = len(perms_tuple) - len(perms_list)
            
            perms_text = "\n".join(f"• `{perm}`" for perm in perms_list)
            if remaining_perms > 0:
                perms_text += f"\n• *...and {remaining_perms} more*"
            
            embed.add_field(
                name=f"**Channels:**",
                value=f"{channel_names}\n**Needed:**\n{perms_text}",
                inline=True
            )
        
        # Add summary if there are more channel groups
        remaining_groups = len(channels_by_perms) - displayed_groups
        if remaining_groups > 0:
            embed.add_field(
                name="📋 Additional Issues",
                value=f"*{remaining_groups} more channel permission group(s) with similar issues.*",
                inline=False
            )
    
    # Add helpful footer
    if total_missing > 1:
        embed.set_footer(text="💡 Tip: Permissions are listed by priority - fix the first ones and others may resolve inherently")
    
    return embed

def create_success_embed() -> nextcord.Embed:
    """
    Create a success embed when all permissions are present.
    
    Returns:
        nextcord.Embed: The success embed
    """
    return nextcord.Embed(
        title="InfiniBot Permission Report",
        description="InfiniBot has every permission it needs! Nice work!",
        color=nextcord.Color.green()
    )

async def run_check_infinibot_permissions(interaction: Interaction, edit_message: bool = False) -> None:
    """
    Check and report InfiniBot's missing permissions in the guild.
    
    Args:
        interaction: The Discord interaction that triggered this command
        edit_message: Whether to edit the existing message or send a new one
    """
    # Get missing permissions from utility function
    guild_permissions, channel_permissions = get_infinibot_missing_permissions(interaction.guild)
    
    # Create appropriate embed based on permission status
    if not guild_permissions and not channel_permissions:
        embed = create_success_embed()
    else:
        embed = create_permissions_report_embed(guild_permissions, channel_permissions)
        # This should never be None here, but adding safety check
        if embed is None:
            embed = create_success_embed()
    
    # Send the response
    if edit_message:
        await interaction.response.edit_message(embed=embed, view=InfiniBotPermissionsReportView())
    else:
        await interaction.response.send_message(
            embed=embed,  
            ephemeral=True,
            view=InfiniBotPermissionsReportView()
        )