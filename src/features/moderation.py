import datetime
import humanfriendly
import logging
import re

import nextcord

from components import utils, ui_components
from config.global_settings import discord_bot
from config.server import Server
from modules.custom_types import UNSET_VALUE


# Profanity Moderation ----------------------------------------------------------------------------------------------------------
class IncorrectButtonView(nextcord.ui.View):
  def __init__(self):
    super().__init__(timeout = None)
  
  @nextcord.ui.button(label = 'Mark As Incorrect', style = nextcord.ButtonStyle.blurple, custom_id = "mark_as_incorrect")
  async def event(self, button:nextcord.ui.Button, interaction: nextcord.Interaction):
    embed = interaction.message.embeds[0]
    id = embed.footer.text.split(" ")[-1]
    guild = interaction.guild
    member = guild.get_member(int(id))
    
    if member != None:
        button.label = "Marked as Incorrect"
        button.disabled = True
        
        # We either need to refund a strike, or revoke a timeout.
        # If the user is at 0 strikes now, this says one of two things:
        # They were timed out
        # Or it's been so long that the strike has expired.
        
        server = Server(interaction.guild.id)
        strike_count = server.moderation_strikes[member.id].strikes
        if strike_count != 0:
            # We'll just refund a strike.
            update_strikes_for_member(guild.id, member.id, -1)
            
            embed.title += " - Marked As Incorrect"
            embed.color = nextcord.Color.dark_green()
            await interaction.response.edit_message(embed = embed, view=self)
            return
            
        else:
            # Uh, oh. We need to do some thinking...
            # Has it been past the time that the timeout would have been?
            current_time = datetime.datetime.now(datetime.timezone.utc)
            message_time = interaction.message.created_at
            delta_seconds = (current_time - message_time).seconds
            if delta_seconds <= server.profanity_moderation_profile.timeout_seconds:
                # We can revoke the timeout
                await utils.timeout(member = member, time = 0, reason = "Revoking Profanity Moderation Timeout")
                
                embed.title += " - Marked As Incorrect"
                embed.color = nextcord.Color.dark_green()
                await interaction.response.edit_message(embed = embed, view=self)
                return
            
            else:
                button.label = "No Available Actions"
                await interaction.response.edit_message(view=self)

                await interaction.followup.send(embed = nextcord.Embed(title = "No Available Actions", description = f"No actions available. Previous punishments have expired.", color =  nextcord.Color.red()), ephemeral = True)
                return

    else:
        button.label = "Member no longer exists"
        button.disabled = True
    
    self.stop()

def str_is_profane(message: str, database: list[str]):
    # Normalize both message and database to lowercase
    words = [x.lower() for x in message.split()]
    database = set(x.lower().replace('*', '.*') for x in database)  # Convert wildcards to regex patterns
    
    # Create a single regex pattern from the database
    pattern = re.compile('|'.join(database))
    
    # Check each word against the pattern
    for word in words:
        if pattern.search(word):
            return word  # Return the first profane word found

    return None

def update_strikes_for_member(guild_id:int, member_id:int, amount:int):
    """
    Update the strike count for a member in a server.

    This function updates the strike count for a specified user within a given guild.
    If the profanity moderation strike system is active for the server, it will add or subtract the specified amount of strikes to the user's current strike count. If the updated strike count becomes less than or equal to 0, the user's strike record is removed.

    Parameters:
    ----------
    guild_id : int
        The ID of the guild (server) where the user resides.
    member_id : int
        The ID of the user for whom the strike count needs to be updated.
    amount : int
        The amount by which to update the user's strike count. This can be positive
        (to add strikes) or negative (to remove strikes).

    Returns:
    -------
    int
        The updated strike count for the user. If the user's strike record is removed,
        this will return 0.
    """
    server = Server(guild_id)
    updated_strike_count = 0

    if server.profanity_moderation_profile.strike_system_active:
        if member_id in server.moderation_strikes:
            strike_data = server.moderation_strikes[member_id]
            strike_data.strikes += amount
            strike_data.last_strike = datetime.datetime.now()
            updated_strike_count = strike_data.strikes

            if strike_data.strikes <= 0:
                server.moderation_strikes.delete(member_id)
                updated_strike_count = 0
                
        else:
            if amount > 0:
                server.moderation_strikes.add(member_id=member_id, strikes=amount, last_strike=datetime.datetime.now())
                updated_strike_count = amount

    return updated_strike_count

async def grant_and_punnish_strike(guild_id, member: nextcord.Member, amount: int, server = None, strike_data = None):
    """|coro|
    
    Handle giving or taking a strike to/from a member.
    
    Note: This will grant timeouts.

    ------
    Parameters
    ------
    guild_id : `int`
        The guild id that you are in.
    member : `nextcord.Member`
        The the member to give/take a strike to/from.
    amount : `int`
        Positive or negative number of strikes to give/take.
        
    Returns
    ------
    `bool`
        If the user was timed out.
    """
    updated_strike_count = update_strikes_for_member(guild_id, member.id, amount)
        
    # Check if they should be timed out
    server = Server(guild_id)

    timeout = False
    if not server.profanity_moderation_profile.strike_system_active:
        timeout = True # If the strike system is disabled, one infraction is enough to timeout
    elif updated_strike_count >= server.profanity_moderation_profile.max_strikes:
        timeout = True

    if timeout:
        # Check Permissions
        guild = discord_bot.get_guild(guild_id)
        if not guild:
            logging.warning(f"Guild not found for guild_id: {guild_id}. Skipping timeout.")
            return False
        
        if not guild.me.guild_permissions.moderate_members:
            await utils.send_error_message_to_server_owner(guild, "Timeout Members", guild_permission = True)
            return False
        
        reason = (f"Profanity Moderation: User exceeded strike limit of {server.profanity_moderation_profile.max_strikes}." 
                  if (server.profanity_moderation_profile.strike_system_active) else "Profanity Moderation")
        
        if await utils.timeout(member, server.profanity_moderation_profile.timeout_seconds, reason = reason):
            # The user was successfully timed out. Remove the strike
            server.moderation_strikes.delete(member.id)
        
        else:
            uuid = utils.get_uuid_for_logging()
            message = f"Failed to timeout {member.mention} for profanity moderation."
            embed = nextcord.Embed(title = "Failed to Timeout", description = message, color = nextcord.Color.red())
            embed.set_footer(text = f"Error ID: {uuid}")

            admin_channel = discord_bot.get_channel(server.profanity_moderation_profile.channel)
            await admin_channel.send(embed = embed)

            logging.error(f"Error ID: {uuid} - Failed to timeout user ({member.id}) for profanity moderation.")

    return False

async def check_message_for_profanity(server: Server, message: nextcord.Message, skip_admin_check=False):
    # Checks
    if not utils.feature_is_active(server = server, feature = "profanity_moderation"): return
    if message.channel.type != nextcord.ChannelType.stage_voice and message.channel.is_nsfw():
        logging.debug(f"Skipped profanity check for NSFW channel: {message.channel}") 
        return # Don't check profanity in NSFW channels or stage channels

    if not isinstance(message.author, nextcord.Member): 
        logging.warning(f"Tried to check profanity for a non-member: {message.author}")
        return
    
    if not skip_admin_check:
        if message.author.guild_permissions.administrator: # Don't check profanity for admins
            logging.debug(f"Skipped profanity check for admin: {message.author}")
            return
        
    # Message Content
    msg = message.content.lower()

    # Ignore if the message is nothing, or if it is actually just a slash command
    if len(msg) == 0 or msg[0] == "/":
        return
    
    # Check for profanity -------------------------------------------------------------------
    result = str_is_profane(msg, server.profanity_moderation_profile.filtered_words)
    if result != None:
        # If they are in violation and need to be punished...
        # Give them a strike (and perhaps a timeout)
        action_successful = await grant_and_punnish_strike(message.guild.id, message.author, 1)
        
        timed_out = False if message.author.timed_out_until == None else True

        if action_successful:
            # DM them (if they want)
            # memberSettings = Member(message.author.id) # TODO When member settings are implemented
            # if memberSettings.dms_enabled:
            if True:
                try:
                    # Check if they were timed out, or if it's just a strike
                    if timed_out:
                        # They were timed out. Tell them.
                        # Format the seconds in a human readable way
                        description = f"""
                        You were flagged for profanity.
                        
                        **Server:** {message.guild.name}
                        **Word:** {result}
                        **Message:** {message.content}
                        
                        You were timed out for {humanfriendly.format_timespan(server.profanity_moderation_profile.timeout_seconds)}.
                        """
                        description = utils.standardize_str_indention(description)
                        embed = nextcord.Embed(title = "Profanity Log", description = description, color = nextcord.Color.red(), timestamp = datetime.datetime.now())
                        embed.set_footer(text = "To opt out of dm notifications, use /opt_out_of_dms")
                        await message.author.send(embed = embed)
                        
                    else:
                        # It was just a strike. Tell them.
                        current_strikes = server.moderation_strikes[message.author.id].strikes
                        description = f"""
                        You were flagged for profanity.
                        
                        **Server:** {message.guild.name}
                        **Word:** {result}
                        **Message:** {message.content}
                        
                        You are now at strike {current_strikes} / {server.profanity_moderation_profile.max_strikes}.
                        """
                        description = utils.standardize_str_indention(description)
                        embed = nextcord.Embed(title = "Profanity Log", description = description, color = nextcord.Color.red(), timestamp = datetime.datetime.now())
                        embed.set_footer(text = "To opt out of dm notifications, use /opt_out_of_dms")
                        await message.author.send(embed = embed)
                        
                except nextcord.Forbidden:
                    pass #the user has dms turned off. It's not a big deal, they just don't get notified.
                except Exception as e:
                    logging.error(f"Error sending profanity DM to {message.author}: {e}", exc_info=True)
            
            # Send message in channel where bad word was sent.
            if await utils.check_text_channel_permissions(message.channel, True):
                description = f"""
                {message.author.mention} was flagged for profanity. The message was automatically deleted.
                
                Contact a server admin for more info.
                """
                description = utils.standardize_str_indention(description)
                embed = nextcord.Embed(title = "Profanity Detected", description = description, color = nextcord.Color.dark_red())
                await message.channel.send(embed = embed, view = ui_components.InviteView(), delete_after = 10.0)
            
            # Send message to admin channel (if enabled)
            if server.profanity_moderation_profile.channel != UNSET_VALUE:
                admin_channel = message.guild.get_channel(server.profanity_moderation_profile.channel)
                if admin_channel == None: 
                    logging.warning(f"Could not find admin channel for server {message.guild.name} ({message.guild.id})")
                elif await utils.check_text_channel_permissions(admin_channel, True, custom_channel_name = f"Admin Channel (#{admin_channel.name})"):
                    view = IncorrectButtonView()

                    description = f"""
                    {message.author.mention} was flagged for profanity.
                    
                    **Word:** {result}
                    **Message:** {message.content}
                    **Channel**: {message.channel.mention}
                    
                    This message was automatically deleted.
                    """

                    if timed_out:
                        description += f"""
                        {message.author.mention} was timed out for {humanfriendly.format_timespan(server.profanity_moderation_profile.timeout_seconds)}.
                        """

                    if server.profanity_moderation_profile.strike_system_active:
                        description += f"""
                        {message.author.mention} is now at strike {action_successful} / {server.profanity_moderation_profile.max_strikes}.
                        """

                    description = utils.standardize_str_indention(description)
                    
                    embed = nextcord.Embed(title = "Profanity Detected", description = description, color = nextcord.Color.dark_red(), timestamp = datetime.datetime.now())
                    embed.set_footer(text = f"Member ID: {str(message.author.id)}")
                    
                    await admin_channel.send(view = view, embed = embed)
        
        # Delete the message
        try:
            await message.delete()
        except nextcord.errors.Forbidden:
            await utils.send_error_message_to_server_owner(message.guild, "Manage Messages", channel = message.channel.name)
        except Exception as e:
            logging.error(f"Error deleting message after profanity check: {e}", exc_info=True)





async def check_message_for_spam(message):
    return


async def check_and_run_moderation_commands(message: nextcord.Message):
    if message.guild == None: return # Guild not loaded yet.

    # if message.author.guild_permissions.administrator: # Don't check profanity for admins
    #     logging.debug(f"Skipped profanity check for admin in {__name__}: {message.author}")
    #     return
    
    server = Server(message.guild.id)

    logging.info(server.moderation_strikes[message.author.id].strikes)
    server.moderation_strikes.edit(message.author.id, strikes=0)

    message_is_profane = await check_message_for_profanity(server, message, skip_admin_check=True)
        

    # # Other Things
    # if not message_is_profane:
    #     # Check Invites
    #     if server.delete_invites_enabled and not message.author.guild_permissions.administrator:
    #         if "discord.gg/" in message.content.lower(): await message.delete()
    #     # Check spam
    #     if utils.enabled.SpamModeration(server = server) and not message.author.guild_permissions.administrator:
    #         await checkSpam(message, server)