import datetime
import nextcord

from components import utils
from config.member import Member
from config.server import Server
from modules.custom_types import UNSET_VALUE


async def trigger_join_message(member: nextcord.Member) -> None:
    """
    |coro|

    Trigger the join message functionality.
    
    :param member: The member that has joined. This is a required parameter.
    :type member: nextcord.Member
    :return: None
    :rtype: None
    """
    
    server = Server(member.guild.id)

    if utils.feature_is_active(server = server, feature = "join_messages"): # Check if join messages are enabled
        if server.join_message_profile.channel != UNSET_VALUE: # Find join channel
            channel_id = server.join_message_profile.channel
            channel = member.guild.get_channel(channel_id) or await member.guild.fetch_channel(channel_id)
            if channel == None:
                await utils.send_error_message_to_server_owner(
                    member.guild,
                    None,
                    message=(
                        f"InfiniBot is unable to find your join message channel. "
                        f"The join message channel #{channel_id} either no longer exists, "
                        f"or is hidden from InfiniBot."
                    )
                )
                return
        else:
            if member.guild.system_channel != None:
                channel = member.guild.system_channel
            else:
                return
        
        # Double check permissions
        if channel and not await utils.check_text_channel_permissions(channel, True, custom_channel_name = f"Join Message Channel (#{channel.name})"):
            return
            
        # Send message
        join_message_embed: nextcord.Embed = server.join_message_profile.embed.to_embed()
        join_message_embed = utils.apply_generic_replacements(join_message_embed, member, member.guild)
        join_message_embed.timestamp = datetime.datetime.now()
        embeds = [join_message_embed]
        
        # Join Card (If enabled)
        if server.join_message_profile.allow_join_cards:
            member_data = Member(member.id)
            if member_data.join_card_enabled:
                card = member_data.join_card_embed.to_embed()
                card = utils.apply_generic_replacements(card, member, member.guild, skip_channel_replacement=True)
                embeds.append(card)
        
        await channel.send(embeds = embeds)
            
async def trigger_leave_message(member: nextcord.Member) -> None:
    """
    |coro|

    Trigger the leave message functionality.
    
    :param member: The member that has left. This is a required parameter.
    :type member: nextcord.Member
    :return: None
    :rtype: None
    """
    if member == None: return
    if member.guild == None: return
    if member.guild.id == None: return
    
    server = Server(member.guild.id)
            
    if utils.feature_is_active(server = server, feature = "leave_messages"): # Check if leave messages are enabled
        if server.leave_message_profile.channel != UNSET_VALUE: # Find join channel
            channel_id = server.leave_message_profile.channel
            channel = member.guild.get_channel(channel_id) or await member.guild.fetch_channel(channel_id)
            if channel == None:
                await utils.send_error_message_to_server_owner(
                    member.guild,
                    None,
                    message=(
                        f"InfiniBot is unable to find your leave message channel. "
                        f"The leave message channel #{channel_id} either no longer exists, "
                        f"or is hidden from InfiniBot."
                    )
                )
                return
        else:
            if member.guild.system_channel != None:
                channel = member.guild.system_channel
            else:
                return
        
        # Double check permissions
        if channel and not await utils.check_text_channel_permissions(channel, True, custom_channel_name = f"Leave Message Channel (#{channel.name})"):
            return
            
        # Send message
        leave_message_embed: nextcord.Embed = server.leave_message_profile.embed.to_embed()
        leave_message_embed = utils.apply_generic_replacements(leave_message_embed, member, member.guild)
        leave_message_embed.timestamp = datetime.datetime.now()
        
        await channel.send(embed = leave_message_embed)