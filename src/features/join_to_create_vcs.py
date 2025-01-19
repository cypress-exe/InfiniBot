import nextcord

from components import utils
from config.server import Server

async def run_join_to_create_vc_member_update(member: nextcord.Member, before: nextcord.VoiceState, after: nextcord.VoiceState):
    """
    |coro|

    Handles updates to a member's voice state in relation to the 'join to create' voice channels feature.

    :param member: The member whose voice state is being updated.
    :type member: nextcord.Member
    :param before: The voice state of the member before the update.
    :type before: nextcord.VoiceState
    :param after: The voice state of the member after the update.
    :type after: nextcord.VoiceState
    :return: None
    :rtype: None
    """
    
    # Check if the feature is active
    if not utils.feature_is_active(guild_id=member.guild.id, feature="join_to_create_vcs"):
        return
    
    # Exit if there is no channel change
    if before.channel is None and after.channel is None:
        return
    
    # Handle member joining a voice channel
    if after.channel is not None:
        server = Server(member.guild.id)
        voice_channels = server.join_to_create_vcs.channels
        
        # Check if the channel is a join-to-create channel
        if after.channel.id in voice_channels:
            # Ensure bot has necessary permissions
            voice_channel = member.guild.get_channel(after.channel.id)
            if not voice_channel:
                return
            if not voice_channel.permissions_for(member.guild.me).view_channel:
                return
            if not voice_channel.permissions_for(member.guild.me).manage_channels:
                return
                
            # Create a new voice channel in the same category
            category = after.channel.category if after.channel.category else member.guild
            try:
                new_vc = await category.create_voice_channel(name=f"{member.name} Vc")
            except nextcord.errors.Forbidden:
                await utils.send_error_message_to_server_owner(member.guild, "Manage Channels", guild_permission=True)
                return
            
            # Attempt to move the member to the new voice channel
            try:
                await member.move_to(new_vc)
            except nextcord.errors.Forbidden:
                await utils.send_error_message_to_server_owner(member.guild, "Move Members")
                return
    
    # Handle member leaving a voice channel
    if before.channel is not None:
        # Check if the channel is empty and needs deletion
        if not before.channel.members:
            try:
                channel_name_split = before.channel.name.split(" ")
                member_name = " ".join(channel_name_split[:-1])
                if member_name in [member.name for member in member.guild.members] and channel_name_split[-1] == "Vc":
                    # Ensure bot can view the channel before attempting deletion
                    if not before.channel.permissions_for(member.guild.me).view_channel:
                        await utils.send_error_message_to_server_owner(member.guild, "View Channels", channel=f"#{before.channel.name}")
                        return
                    
                    # Delete the voice channel
                    await before.channel.delete()

            except nextcord.errors.Forbidden:
                if not before.channel.permissions_for(member.guild.me).manage_channels:
                    await utils.send_error_message_to_server_owner(member.guild, "Manage Channels", guild_permission=True)
                if not before.channel.permissions_for(member.guild.me).connect:
                    await utils.send_error_message_to_server_owner(member.guild, "Connect", guild_permission=True)
                return