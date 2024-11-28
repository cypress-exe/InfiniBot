import datetime
import humanfriendly
import logging
import re

import nextcord

from components import utils, ui_components
from config.server import Server
from core import log_manager
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
        strike_count = server.moderation_strikes[member.id].strikes if member.id in server.moderation_strikes else 0
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
                await utils.timeout(member = member, seconds = 0, reason = "Revoking Profanity Moderation Timeout")
                
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
    def generate_regex_pattern(word: str):
        word = word.replace("*", ".")

        if not word.startswith("\""):
            word = r"\w*" + word
        else:
            word = r"\b" + word[1:]

        if not word.endswith("\""):
            word = word + r"\w*"
        else:
            word = word[:-1] + r"\b"

        return word

    regex_patterns = [re.compile(generate_regex_pattern(pattern)) for pattern in database]

    # Check the pattern
    for pattern in regex_patterns:
        match = pattern.search(message)
        if match:
            return match

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
            old_strikes = server.moderation_strikes[member_id].strikes
            server.moderation_strikes.edit(member_id=member_id, strikes=old_strikes + amount, last_strike=datetime.datetime.now())
            updated_strike_count = server.moderation_strikes[member_id].strikes

            if updated_strike_count <= 0:
                server.moderation_strikes.delete(member_id)
                updated_strike_count = 0
                
        else:
            if amount > 0:
                server.moderation_strikes.add(member_id=member_id, strikes=amount, last_strike=datetime.datetime.now())
                updated_strike_count = amount

    return updated_strike_count

async def grant_and_punnish_strike(bot: nextcord.client, guild_id: int, member: nextcord.Member, amount: int, server = None, strike_data = None):
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
        guild = bot.get_guild(guild_id)
        if not guild:
            logging.warning(f"Guild not found for guild_id: {guild_id}. Skipping timeout.")
            return False
        
        if not guild.me.guild_permissions.moderate_members:
            await utils.send_error_message_to_server_owner(guild, "Timeout Members", guild_permission = True)
            return False
        
        reason = (f"Profanity Moderation: User exceeded strike limit of {server.profanity_moderation_profile.max_strikes}." 
                  if (server.profanity_moderation_profile.strike_system_active) else "Profanity Moderation")
        
        timeout_response = await utils.timeout(member, server.profanity_moderation_profile.timeout_seconds, reason = reason)
        if timeout_response.startswith("Success"):
            # The user was successfully timed out. Remove the strike
            if member.id in server.moderation_strikes: server.moderation_strikes.delete(member.id)
            return True

        elif timeout_response == "Failure Forbidden":
            message = f"Failed to timeout {member.mention} for profanity moderation. Missing permissions."
            embed = nextcord.Embed(title = "Failed to Timeout", description = message, color = nextcord.Color.red())

            admin_channel = bot.get_channel(server.profanity_moderation_profile.channel)
            await admin_channel.send(embed = embed)
            return False
        
        else:
            uuid = log_manager.get_uuid_for_logging()
            message = f"Failed to timeout {member.mention} for profanity moderation."
            embed = nextcord.Embed(title = "Failed to Timeout", description = message, color = nextcord.Color.red())
            embed.set_footer(text = f"Error ID: {uuid}")

            admin_channel = bot.get_channel(server.profanity_moderation_profile.channel)
            await admin_channel.send(embed = embed)

            logging.error(f"Error ID: {uuid} - Failed to timeout user ({member.id}) for profanity moderation.")
            return False

    else:
        return True

async def check_and_trigger_profanity_moderation_for_message(bot: nextcord.client, server: Server, message: nextcord.Message, skip_admin_check=False):
    # Checks
    if not utils.feature_is_active(server = server, feature = "profanity_moderation"): return
    if message.channel.type != nextcord.ChannelType.stage_voice and message.channel.is_nsfw():
        logging.debug(f"Skipped profanity check for NSFW / stage channel: {message.channel}") 
        return

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
    profane_word = str_is_profane(msg, server.profanity_moderation_profile.filtered_words)
    if profane_word == None: 
        return # No profanity found. Nothing to do.
    
    # Grant a strike (and maybe timeout)
    action_successful = await grant_and_punnish_strike(bot, message.guild.id, message.author, 1)
    
    timed_out = False if message.author.communication_disabled_until == None else True

    if action_successful:
        # Notify the user that they were timed out via DM
        # memberSettings = Member(message.author.id) # TODO When member settings are implemented
        # if memberSettings.dms_enabled:
        if True:
            try:
                # Check if they were timed out, or if it's just a strike
                if timed_out:
                    description = f"""
                    You were flagged for profanity.
                    
                    **Server:** {message.guild.name}
                    **Word:** {profane_word}
                    **Message:** {message.content}
                    
                    You were timed out for {humanfriendly.format_timespan(server.profanity_moderation_profile.timeout_seconds)}.
                    """
                else:
                    # It was just a strike. Tell them.
                    current_strikes = server.moderation_strikes[message.author.id].strikes
                    description = f"""
                    You were flagged for profanity.
                    
                    **Server:** {message.guild.name}
                    **Word:** {profane_word}
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

    # Delete the message
    message_deleted = False
    try:
        await message.delete()
        message_deleted = True
    except nextcord.errors.Forbidden:
        await utils.send_error_message_to_server_owner(message.guild, "Manage Messages", channel = message.channel.name)
    except Exception as e:
        logging.error(f"Error deleting message after profanity check: {e}", exc_info=True)

    # Send message in channel where profane word was sent.
    if await utils.check_text_channel_permissions(message.channel, True):
        description = f"""
        {message.author.mention} was flagged for profanity. {"The message was automatically deleted." if message_deleted else "There was an error deleting the message."}
        
        Contact a server admin for more info.
        """
        description = utils.standardize_str_indention(description)
        embed = nextcord.Embed(title = "Profanity Detected", description = description, color = nextcord.Color.dark_red())
        await message.channel.send(embed = embed, view = ui_components.InviteView(), delete_after = 10.0)
    
    # Send message to admin channel (if enabled)
    if server.profanity_moderation_profile.channel != UNSET_VALUE:
        admin_channel = message.guild.get_channel(server.profanity_moderation_profile.channel)
        if admin_channel == None: 
            description = f"InfiniBot couln't find your server's admin channel (Moderation -> Profanity -> Admin Channel). It was either deleted, or the bot does not have permission to view it. Please go to the Moderation -> Profanity page of the `/dashboard` and configure the admin channel."
            await utils.send_error_message_to_server_owner(message.guild, None, message=description)
        elif await utils.check_text_channel_permissions(admin_channel, True, custom_channel_name = f"Admin Channel (#{admin_channel.name})"):
            view = IncorrectButtonView()

            description = f"""
            {message.author.mention} was flagged for profanity.
            
            **Word:** {profane_word}
            **Message:** {message.content}
            **Channel**: {message.channel.mention}
            
            {"The message was automatically deleted." if message_deleted else "There was an error deleting the message."}
            """

            if timed_out:
                description += f"""
                {message.author.mention} was timed out for {humanfriendly.format_timespan(server.profanity_moderation_profile.timeout_seconds)}.
                """

            if server.profanity_moderation_profile.strike_system_active:
                if message.author.id in server.moderation_strikes:
                    current_strikes = server.moderation_strikes[message.author.id].strikes
                else:
                    current_strikes = 0

                description += f"""
                {message.author.mention} is now at strike {current_strikes} / {server.profanity_moderation_profile.max_strikes}.
                """

            description = utils.standardize_str_indention(description)
            
            embed = nextcord.Embed(title = "Profanity Detected", description = description, color = nextcord.Color.dark_red(), timestamp = datetime.datetime.now())
            embed.set_footer(text = f"Member ID: {str(message.author.id)}")
            
            await admin_channel.send(view = view, embed = embed)
    

async def check_and_trigger_spam_moderation_for_message(message: nextcord.Message, server: Server):
    return


async def check_and_run_moderation_commands(bot: nextcord.client, message: nextcord.Message):
    if message.guild == None: return # Guild not loaded yet.

    if message.author.guild_permissions.administrator: # Don't check profanity for admins
        logging.debug(f"Skipped profanity check for admin in {__name__}: {message.author}")
        return
    
    server = Server(message.guild.id)

    with log_manager.LogIfFailure(feature="check_message_for_profanity"):
        message_is_profane = await check_and_trigger_profanity_moderation_for_message(bot, server, message, skip_admin_check=True)
        if message_is_profane: return

    # Check Invites
    if server.infinibot_settings_profile.delete_invites:
        if "discord.gg/" in message.content.lower(): 
            await message.delete()
            return

    # Check spam
    await check_and_trigger_spam_moderation_for_message(message, server)