import asyncio
from collections import defaultdict
import datetime
import humanfriendly
import logging
import math
import re
from typing import List

import nextcord

from components import utils, ui_components
from config.global_settings import get_configs, get_global_kill_status
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


async def check_profanity_moderation_enabled_and_warn_if_not(interaction: nextcord.Interaction):
    """Runs a check whether moderation is active. NOT SILENT!"""
    server = Server(interaction.guild.id)
    if utils.feature_is_active(server = server, feature = "profanity_moderation"):
        return True
    else:
        if get_global_kill_status()["profanity_moderation"]:
            await interaction.response.send_message(embed = nextcord.Embed(title = "Moderation Tools Disabled", description = "Moderation has been disabled by the developers of InfiniBot. This is likely due to an critical instability with it right now. It will be re-enabled shortly after the issue has been resolved.", color = nextcord.Color.red()), ephemeral = True)
            return False
        else:
            await interaction.response.send_message(embed = nextcord.Embed(title = "Moderation Tools Disabled", description = "Moderation has been turned off. Go to the `/dashboard` to turn it back on.", color = nextcord.Color.red()), ephemeral = True)
            return False

# Confirm that a nickname is not in violation of profanity
async def check_and_punish_nickname_for_profanity(bot: nextcord.Client, guild: nextcord.Guild, before: nextcord.Member, after: nextcord.Member):
    """Check to ensure that the edited nickname is in compliance with moderation"""
    
    member = after
    nickname = after.nick
    
    if nickname == None: return
    if member.guild_permissions.administrator: return
    
    server = Server(guild.id)
    
    if not utils.feature_is_active(server = server, feature = "profanity_moderation"): return

    profane_word = str_is_profane(nickname, server.profanity_moderation_profile.filtered_words)
    if profane_word != None:
        
        # Get the audit log
        entry = list(await guild.audit_logs(limit=1).flatten())[0]
        # Confirm that this entry is fresh (within 1 second)
        entry_is_fresh = True
        if (datetime.datetime.now(datetime.timezone.utc) - entry.created_at).seconds > 1: entry_is_fresh = False
        user = entry.user
        
        if entry_is_fresh and user.id == member.id:
            # User is the one who edited their nickname. Give them a strike
            timeout_successful = await grant_and_punish_strike(bot, guild.id, member, 1)
            if not timeout_successful: return

            if server.profanity_moderation_profile.strike_system_active:
                if member.id in server.moderation_strikes:
                    strikes = server.moderation_strikes[member.id].strikes
                else:
                    strikes = 0
            else:
                strikes = 0

        # Wait a second for other processes
        await asyncio.sleep(1)

        # They are in violation. Let's try to change their nickname back
        nickname_removed = False
        try:
            await member.edit(nick = None)
            nickname_removed = True
        except nextcord.errors.Forbidden:
            # Make sure the bot should have been able to do this
            if after.top_role.position < after.guild.me.top_role.position:
                # InfiniBot should have been able to do this. Warn the server owner.
                await utils.send_error_message_to_server_owner(guild = guild, permission = "Manage Nicknames", guild_permission = True)

        if entry_is_fresh and user.id == member.id:
            # DM them
            timeout_time = humanfriendly.format_timespan(server.profanity_moderation_profile.timeout_seconds)
            if strikes == 0: strikes_info = f"\n\nYou were timed out for {timeout_time}"
            else: strikes_info = f"\n\nYou are now at strike {strikes} / {server.profanity_moderation_profile.max_strikes}"
            
            embed = nextcord.Embed(title = "Profanity Detected", description = f"You were flagged for your nickname.\n\n**Server**: {guild.name}\n**Nickname:** {nickname}{strikes_info}", color = nextcord.Color.dark_red())
            embed.set_footer(text = "To opt out of dm notifications, use /opt_out_of_dms")
            await member.send(embed = embed)
            
            # Send a message to the admin channel
            admin_channel_id = server.profanity_moderation_profile.channel
            if admin_channel_id == UNSET_VALUE: return
            admin_channel = guild.get_channel(admin_channel_id)
            if admin_channel == None: return
            if not await utils.check_text_channel_permissions(admin_channel, True, custom_channel_name = f"Admin Channel (#{admin_channel.name})"): return


            description = f"""
            {member.mention} was flagged for their nickname of \"{nickname}\".

            {f"{member.mention} was timed out for {timeout_time}" if strikes == 0 else f"{member.mention} is now at strike {strikes} / {server.profanity_moderation_profile.max_strikes}"}

            {"InfiniBot automatically reverted their nickname to their original name." if nickname_removed else "InfiniBot could not revert their nickname due to lack of permissions."}
            """
            description = utils.standardize_str_indention(description)
            embed =  nextcord.Embed(title = "Profanity Detected", description = description, color = nextcord.Color.dark_red())
            embed.set_footer(text = f"Member ID: {str(member.id)}")
            await admin_channel.send(embed = embed, view = IncorrectButtonView())
        else:
            # User is not the one who edited their nickname

            # Send a message to the admin channel
            admin_channel_id = server.profanity_moderation_profile.channel
            if admin_channel_id == UNSET_VALUE: return
            admin_channel = guild.get_channel(admin_channel_id)
            if admin_channel == None: return
            if not await utils.check_text_channel_permissions(admin_channel, True, custom_channel_name = f"Admin Channel (#{admin_channel.name})"): return

            description = f"""
            {user.mention} edited {member.mention}'s nickname to \"{nickname}\". It was flagged for profanity.

            {"InfiniBot automatically reverted their nickname to their original name." if nickname_removed else "InfiniBot could not revert their nickname due to lack of permissions."}
            """
            description = utils.standardize_str_indention(description)
            embed =  nextcord.Embed(title = "Profanity Detected", description = description, color = nextcord.Color.dark_red())
            embed.set_footer(text = f"Member ID: {str(member.id)}")
            await admin_channel.send(embed = embed)

def str_is_profane(message: str, database: list[str]):
    def generate_regex_pattern(word: str):
        word = word.lower()
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

    message = message.lower()
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

async def grant_and_punish_strike(bot: nextcord.Client, guild_id: int, member: nextcord.Member, amount: int, server = None, strike_data = None):
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
        logging.debug(f"Skipped profanity check for NSFW / stage channel: {message.channel}. Guild ID: {message.guild.id}") 
        return

    if not isinstance(message.author, nextcord.Member): 
        logging.warning(f"Tried to check profanity for a non-member: {message.author}. Guild ID: {message.guild.id}")
        return
    
    if not skip_admin_check:
        if message.author.guild_permissions.administrator: # Don't check profanity for admins
            logging.debug(f"Skipped profanity check for admin: {message.author}. Guild ID: {message.guild.id}")
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
    action_successful = await grant_and_punish_strike(bot, message.guild.id, message.author, 1)
    
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



def check_repeated_words_percentage(text, threshold=0.8):
    words = re.findall(r'\w+', text.lower())  # Convert text to lowercase and extract words
    counts = defaultdict(lambda: 0)  # Dictionary to store word counts
    
    # Remove symbols from the words
    words = [re.sub(r'\W+', '', word) for word in words]

    # Iterate over the words and count their occurrences
    last_words = []
    for word in words:
        if word not in last_words:
            counts[word] += 0.5
        else:
            counts[word] += 1
        last_words.insert(0, word)
        if len(last_words) >= 5:
            last_words.pop(3)
        
    # Calculate the total number of words and the number of repeated words
    total_words = len(words)
    if total_words == 0: return False
    repeated_words = sum(count for count in counts.values() if count > 0.5)

    # Calculate the percentage of repeated words
    repeated_percentage = repeated_words / total_words

    # Check if the percentage exceeds the threshold
    return repeated_percentage >= threshold

def levenshtein_distance(s1, s2):
    # ChatGPT :)
    # Create a matrix to store the distances
    len_s1, len_s2 = len(s1), len(s2)
    matrix = [[0] * (len_s2 + 1) for _ in range(len_s1 + 1)]

    # Initialize the matrix
    for i in range(len_s1 + 1):
        matrix[i][0] = i
    for j in range(len_s2 + 1):
        matrix[0][j] = j

    # Fill the matrix with the Levenshtein distance
    for i in range(1, len_s1 + 1):
        for j in range(1, len_s2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            matrix[i][j] = min(matrix[i - 1][j] + 1,  # Deletion
                               matrix[i][j - 1] + 1,  # Insertion
                               matrix[i - 1][j - 1] + cost)  # Substitution

    return matrix[len_s1][len_s2]

def get_percent_similar(s1, s2):
    # Calculate the Levenshtein distance
    lev_dist = levenshtein_distance(s1, s2)
    
    # Find the maximum possible distance (length of the longer string)
    max_distance = max(len(s1), len(s2))
    
    # Calculate the ratio of Levenshtein distance to maximum distance
    ratio = lev_dist / max_distance
    
    return 1 - ratio

def compare_attachments(attachments_1: List[nextcord.Attachment], attachments_2: List[nextcord.Attachment]):
        # quick optimizations
        if not attachments_1 or not attachments_2:
            return False
        if attachments_1 == attachments_2:
            return True

        for attachment_1 in attachments_1:
            for attachment_2 in attachments_2:
                if (
                    attachment_1.url == attachment_2.url
                    or (
                        attachment_1.filename == attachment_2.filename
                        and attachment_1.width == attachment_2.width
                        and attachment_1.height == attachment_2.height
                        and attachment_1.size == attachment_2.size
                    )
                ):
                    return True
        return False

def normalized_exponential_decay(x, k=5):
    """
    Exponentially decay the input x (0 to 1) normalized to the range [0, 1].
    
    Parameters:
        x (float): Input value between 0 and 1.
        k (float): Decay rate (higher values decay faster).
    
    Returns:
        float: The normalized exponentially decayed value.
    """
    return (1 - math.exp(-k * x)) / (1 - math.exp(-k))

async def check_and_trigger_spam_moderation_for_message(message: nextcord.Message, server: Server):
    max_messages_to_check = get_configs()["spam_moderation"]["max_messages_to_check"]    # The MAXIMUM messages InfiniBot will try to check for spam
    message_chars_to_check_repetition = get_configs()["spam_moderation"]["message_chars_to_check_repetition"]    # A message requires these many characters before it is checked for repetition

    # If Spam is Enabled
    if not utils.feature_is_active(server = server, feature = "spam_moderation"): return

    # Check if InfiniBot can view the audit log
    if not message.guild.me.guild_permissions.view_audit_log:
        await utils.send_error_message_to_server_owner(message.guild, "View Audit Log", channel=message.channel.name)
        return

    # Configure limit (the most messages that we're willing to check)
    if server.spam_moderation_profile.score_threshold < max_messages_to_check:
        limit = server.spam_moderation_profile.score_threshold + 1 # Add one because of the existing message
    else:
        limit = max_messages_to_check

    # Get previous messages
    previous_messages = await message.channel.history(limit=limit).flatten()
    
    # Loop through each previous message and test it
    spam_score = 0
    for _message in previous_messages:
        if spam_score >= server.spam_moderation_profile.score_threshold:
            break
        
        
        message_time = _message.created_at
        time_now = datetime.datetime.now(datetime.timezone.utc)
        time_difference = time_now - message_time
        time_difference_in_seconds = time_difference.total_seconds()

        if server.spam_moderation_profile.time_threshold_seconds == 0:
            within_time_window = True
        else:
            within_time_window = time_difference_in_seconds <= server.spam_moderation_profile.time_threshold_seconds

        score_addition = 0
        if within_time_window:
            if _message.author.bot: continue
            if _message.author.id != message.author.id: continue

            if _message.id != message.id: # If it's not the same message
                if _message.content == message.content:
                    score_addition += 25 # Weighted more
                else:
                    similarity = get_percent_similar(_message.content, message.content)
                    if similarity >= 0.6:
                        score_addition += similarity * 20

            if len(_message.content) < 10:
                impact = 1 if _message.id == message.id else 0.5
                score_addition += 7 * impact

            # Check word count percentage
            if _message.content and len(_message.content) >= message_chars_to_check_repetition and check_repeated_words_percentage(_message.content):
                impact = 1 if _message.id == message.id else 0.1
                score_addition += 0.25 * len(_message.content) * impact
            
            # Check message attachments
            if compare_attachments(_message.attachments, message.attachments):
                score_addition += 30

            # Cap score_addition at 50
            if score_addition > 50:
                score_addition = 50

            impact = 1 if _message.id == message.id else normalized_exponential_decay(x=1-(time_difference_in_seconds / server.spam_moderation_profile.time_threshold_seconds), k=10) # Exponential decay
            spam_score += score_addition * impact
            logging.debug(f"{spam_score=}")

        else:
            break # If this message is outside of the time threshold window, previous ones will be too. Break out of the loop.

    # Punnish the member (if needed)
    if spam_score >= server.spam_moderation_profile.score_threshold:
        try:
            # Time them out
            await utils.timeout(message.author, server.spam_moderation_profile.timeout_seconds, reason=f"Spam Moderation: User exceeded spam message limit of {server.spam_moderation_profile.score_threshold}.")
            
            # Send them a message (if they want it)
            # if Member(message.author.id).dms_enabled: # TODO
            if True:
                timeout_time_ui_text = humanfriendly.format_timespan(server.spam_moderation_profile.timeout_seconds)
                await message.author.send(
                    embed=nextcord.Embed(
                        title="Spam Timeout",
                        description=f"You were flagged for spamming in \"{message.guild.name}\". You have been timed out for {timeout_time_ui_text}.\n\nPlease contact the admins if you think this is a mistake.",
                        color=nextcord.Color.red(),
                    )
                )
        except nextcord.errors.Forbidden:
            await utils.send_error_message_to_server_owner(message.guild, "Timeout Members", guild_permission=True)


async def check_and_run_moderation_commands(bot: nextcord.client, message: nextcord.Message):
    if message.guild == None: return # Guild not loaded yet.

    if message.author.guild_permissions.administrator: # Don't check profanity for admins
        logging.debug(f"Skipped profanity check for admin in {__name__}: {message.author}")
        return
    
    server = Server(message.guild.id)

    with log_manager.LogIfFailure(feature="check_and_trigger_profanity_moderation_for_message"):
        message_is_profane = await check_and_trigger_profanity_moderation_for_message(bot, server, message, skip_admin_check=True)
        if message_is_profane: return True

    # Check Invites
    if server.infinibot_settings_profile.delete_invites:
        if "discord.gg/" in message.content.lower(): 
            await message.delete()
            return True

    # Check spam
    with log_manager.LogIfFailure(feature="check_and_trigger_spam_moderation_for_message"):
        await check_and_trigger_spam_moderation_for_message(message, server)
        return True
    
async def run_my_strikes_command(interaction: nextcord.Interaction):
    if not await check_profanity_moderation_enabled_and_warn_if_not(interaction): return

    server = Server(interaction.guild.id)
    if interaction.user.id in server.moderation_strikes:
        strike = server.moderation_strikes[interaction.user.id]
    else:
        strike = 0

    await interaction.response.send_message(embed = nextcord.Embed(title = f"My Strikes", description = f"You are at {str(strike)} strike(s)", 
                                                                   color =  nextcord.Color.blue()), ephemeral = True)

async def run_view_member_strikes_command(interaction: nextcord.Interaction, member: nextcord.Member):
    if await utils.user_has_config_permissions(interaction):
        server = Server(interaction.guild.id)
        if not await check_profanity_moderation_enabled_and_warn_if_not(interaction): return

        server = Server(interaction.guild.id)
        if member.id in server.moderation_strikes:
            strike = server.moderation_strikes[member.id]
        else:
            strike = 0

        embed = nextcord.Embed(title = f"View Member Strikes", description = f"{member.mention} is at {str(strike)} strike(s).", color =  nextcord.Color.blue())
        await interaction.response.send_message(embed = embed, ephemeral = True)

async def run_set_admin_channel_command(interaction: nextcord.Interaction):
   if await utils.user_has_config_permissions(interaction) and await utils.check_and_warn_if_channel_is_text_channel(interaction):
        server = Server(interaction.guild.id)

        server.profanity_moderation_profile.channel = interaction.channel.id

        embed = nextcord.Embed(title = "Admin Channel Set", description = f"Moderation updates and alerts will now be logged in this channel.\n\n**Ensure Admin-Only Access**\nThis channel lets members report incorrect strikes, so limit access to admins.", color =  nextcord.Color.green())
        embed.set_footer(text = f"Action done by {interaction.user}")
        await interaction.response.send_message(embed = embed, view = ui_components.SupportAndInviteView())