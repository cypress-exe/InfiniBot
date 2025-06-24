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
from config.global_settings import get_configs, get_global_kill_status, get_bot_load_status
from config.member import Member
from config.server import Server
from core import log_manager
from modules.custom_types import UNSET_VALUE


# Profanity Moderation ----------------------------------------------------------------------------------------------------------
class IncorrectButtonView(ui_components.CustomView):
    """
    Handle the event when the "Mark As Incorrect" button is pressed.

    This method updates the button label to "Marked as Incorrect" and disables it.
    It also processes the necessary actions to either refund a strike or revoke a timeout.
    """
    def __init__(self):
        super().__init__(timeout = None)

        self.add_item(nextcord.ui.Button(label="Learn More", url="https://cypress-exe.github.io/InfiniBot/docs/core-features/moderation/profanity/", style=nextcord.ButtonStyle.link))
  
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

async def check_profanity_moderation_enabled_and_warn_if_not(interaction: nextcord.Interaction) -> bool:
    """
    Runs a check to determine whether profanity moderation is active.

    :param interaction: The interaction object from the Discord event.
    :type interaction: nextcord.Interaction
    :return: True if profanity moderation is active, False otherwise.
    :rtype: bool
    """
    server = Server(interaction.guild.id)
    if utils.feature_is_active(server=server, feature="moderation__profanity"):
        return True
    else:
        if get_global_kill_status()["moderation__profanity"]:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="Moderation Tools Disabled",
                    description=(
                        "Moderation has been disabled by the developers of InfiniBot. "
                        "This is likely due to a critical instability with it right now. "
                        "It will be re-enabled shortly after the issue has been resolved."
                    ),
                    color=nextcord.Color.red()
                ),
                ephemeral=True
            )
            return False
        else:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="Moderation Tools Disabled",
                    description=(
                        "Moderation has been turned off."
                        "Go to the `/dashboard` to turn it back on."
                    ),
                    color=nextcord.Color.red()
                ),
                ephemeral=True
            )
            return False

async def check_and_punish_nickname_for_profanity(bot: nextcord.Client, guild: nextcord.Guild, before: nextcord.Member, after: nextcord.Member) -> None:
    """
    Check and ensure that the edited nickname complies with moderation rules.

    :param bot: The bot client.
    :type bot: nextcord.Client
    :param guild: The guild where the nickname change occurred.
    :type guild: nextcord.Guild
    :param before: The member state before the nickname change.
    :type before: nextcord.Member
    :param after: The member state after the nickname change.
    :type after: nextcord.Member
    
    :return: None
    """
    
    member = after
    nickname = after.nick
    
    if nickname == None: return
    if member.guild_permissions.administrator: return
    
    server = Server(guild.id)
    
    if not utils.feature_is_active(server = server, feature = "moderation__profanity"): return

    profane_word = str_is_profane(nickname, server.profanity_moderation_profile.filtered_words)
    if profane_word != None:
        # Get the audit log
        if not guild.me.guild_permissions.view_audit_log:
            await utils.send_error_message_to_server_owner(guild, "View Audit Log", guild_permission=True)
            return
        entry = await anext(guild.audit_logs(limit=1, action=nextcord.AuditLogAction.member_update), None)
        if entry == None: return

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

def str_is_profane(message: str, database: list[str]) -> str | None:
    """
    Checks if a given string contains any profanity.

    This function checks if a given string contains any profanity based on a given
    database of profane words. The database is a list of strings, where each string
    contains a profane word or phrase. Wildcards (*) are supported in the database
    strings.

    :param message: The string to check for profanity.
    :type message: str
    :param database: A list of strings containing profane words or phrases.
    :type database: list[str]
    :return: The matched profane word or phrase if found, or None if no profanity was found.
    :rtype: str | None
    """

    def generate_regex_pattern(word: str):
        """
        Generates a regular expression pattern from a given string.

        This function generates a regular expression pattern from a given string,
        which is used to match profane words or phrases in a given string.

        :param word: The string to generate a regular expression pattern for.
        :type word: str
        :return: The generated regular expression pattern.
        :rtype: str
        """
        word = word.lower()
        # Handle required wildcards (* = exactly 1 character)
        word = word.replace("*", ".")  
        # Add optional wildcards (? = 0 or 1 characters)
        word = word.replace("?", ".?")  # NEW
        
        # Existing boundary logic
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
            return match.group(0)

    return None

def update_strikes_for_member(guild_id:int, member_id:int, amount:int):
    """
    Update the strike count for a member in a server.

    This function updates the strike count for a specified user within a given guild.
    If the profanity moderation strike system is active for the server, it will add or subtract the specified amount of strikes to the user's current strike count. If the updated strike count becomes less than or equal to 0, the user's strike record is removed.

    :type guild_id: int
    :param guild_id: The ID of the guild (server) where the user resides.
    :type member_id: int
    :param member_id: The ID of the user for whom the strike count needs to be updated.
    :type amount: int
    :param amount: The amount by which to update the user's strike count. This can be positive
        (to add strikes) or negative (to remove strikes).

    :rtype: int
    :return: The updated strike count for the user. If the user's strike record is removed,
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

async def grant_and_punish_strike(bot: nextcord.Client, guild_id: int, member: nextcord.Member, amount: int, server = None, strike_data = None) -> bool:
    """|coro|
    
    Handle giving or taking a strike to/from a member.
    
    Note: This will grant timeouts.


    ------
    
    ------
    Parameters
    ----------
    :param guild_id: The guild id that you are in.
    :type guild_id: int
    :param member: The the member to give/take a strike to/from.
    :type member: :class:`nextcord.Member`
    :param amount: Positive or negative number of strikes to give/take.
    :type amount: int
        
    Returns
    -------
    :return: If the user was timed out.
    :rtype: bool
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

async def check_and_trigger_profanity_moderation_for_message(
    bot: nextcord.Client, 
    server: Server, 
    message: nextcord.Message, 
    skip_admin_check: bool = False
) -> bool:
    """
    Checks if the given message contains profanity, and punishes the user if it does.

    :param bot: The bot client.
    :type bot: nextcord.Client
    :param server: The server that the message is from.
    :type server: Server
    :param message: The message to check.
    :type message: nextcord.Message
    :param skip_admin_check: If the bot should skip checking if the user is an administrator.
    :type skip_admin_check: bool

    :return: True if a strike was given, False otherwise.
    :rtype: bool
    """
    # Checks
    if not utils.feature_is_active(server=server, feature="moderation__profanity"):
        return False
    if message.channel.type != nextcord.ChannelType.stage_voice and message.channel.is_nsfw():
        logging.debug(f"Skipped profanity check for NSFW / stage channel: {message.channel}. Guild ID: {message.guild.id}") 
        return False

    if not isinstance(message.author, nextcord.Member): 
        logging.warning(f"Tried to check profanity for a non-member: {message.author}. Guild ID: {message.guild.id}")
        return False
    
    if not skip_admin_check and message.author.guild_permissions.administrator:
        logging.debug(f"Skipped profanity check for admin: {message.author}. Guild ID: {message.guild.id}")
        return False
        
    # Message Content
    msg = message.content.lower()

    # Ignore if the message is nothing, or if it is actually just a slash command
    if len(msg) == 0 or msg[0] == "/":
        return False
    
    # Check for profanity
    profane_word = str_is_profane(msg, server.profanity_moderation_profile.filtered_words)
    if profane_word is None:
        return False
    
    # Grant a strike (and maybe timeout)
    action_successful = await grant_and_punish_strike(bot, message.guild.id, message.author, 1)
    
    timed_out = message.author.communication_disabled_until is not None

    if action_successful:
        # Notify the user that they were timed out via DM
        member_settings = Member(message.author.id)
        if member_settings.direct_messages_enabled:
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
                embed = nextcord.Embed(title="Profanity Log", description=description, color=nextcord.Color.red(), timestamp=datetime.datetime.now())
                embed.set_footer(text="To opt out of dm notifications, use /opt_out_of_dms")
                await message.author.send(embed=embed)
                    
            except nextcord.Forbidden:
                pass # The user has dms turned off. It's not a big deal, they just don't get notified.
            except Exception as e:
                logging.error(f"Error sending profanity DM to {message.author}: {e}", exc_info=True)
                logging.info(f"Extra info for above error: {message.author.id=} {message.guild.id=} {timed_out=}")

    # Delete the message
    message_deleted = False
    try:
        await message.delete()
        message_deleted = True
    except nextcord.errors.Forbidden:
        await utils.send_error_message_to_server_owner(message.guild, "Manage Messages", channel=message.channel.name)
    except Exception as e:
        logging.error(f"Error deleting message after profanity check: {e}", exc_info=True)

    # Send message in channel where profane word was sent.
    if await utils.check_text_channel_permissions(message.channel, True):
        description = f"""
        {message.author.mention} was flagged for profanity. {"The message was automatically deleted." if message_deleted else "There was an error deleting the message."}
        
        Contact a server admin for more info.
        """
        description = utils.standardize_str_indention(description)
        embed = nextcord.Embed(title="Profanity Detected", description=description, color=nextcord.Color.dark_red())
        await message.channel.send(embed=embed, view=ui_components.InviteView(), delete_after=10.0)
    
    # Send message to admin channel (if enabled)
    if server.profanity_moderation_profile.channel != UNSET_VALUE:
        admin_channel = message.guild.get_channel(server.profanity_moderation_profile.channel)
        if admin_channel is None: 
            description = f"InfiniBot couldn't find your server's admin channel (Moderation -> Profanity -> Admin Channel). It was either deleted, or the bot does not have permission to view it. Please go to the Moderation -> Profanity page of the `/dashboard` and configure the admin channel."
            await utils.send_error_message_to_server_owner(message.guild, None, message=description, administrator=False)
        elif await utils.check_text_channel_permissions(admin_channel, True, custom_channel_name=f"Admin Channel (#{admin_channel.name})"):
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
            
            embed = nextcord.Embed(title="Profanity Detected", description=description, color=nextcord.Color.dark_red(), timestamp=datetime.datetime.now())
            embed.set_footer(text=f"Member ID: {str(message.author.id)}")
            
            await admin_channel.send(view=view, embed=embed)

    return True


# Spam Moderation ----------------------------------------------------------------------------------------------------------
def check_repeated_words_percentage(text: str, threshold: float = 0.8) -> bool:
    """
    Checks if the percentage of repeated words in a given text exceeds a given threshold.

    :param text: The text to analyze.
    :type text: str
    :param threshold: The minimum percentage of repeated words to trigger the check.
    :type threshold: float, optional
    :return: True if the percentage of repeated words exceeds the threshold, False otherwise.
    :rtype: bool
    """
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

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculates the Levenshtein distance between two strings.

    :param s1: The first string.
    :type s1: str
    :param s2: The second string.
    :type s2: str
    :return: The Levenshtein distance between the two strings.
    :rtype: int
    """
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

def get_percent_similar(s1: str, s2: str) -> float:
    """
    Calculates the percentage similarity between two strings.

    :param s1: The first string.
    :type s1: str
    :param s2: The second string.
    :type s2: str
    :return: The percentage similarity between the two strings, as a float in [0, 1].
    :rtype: float
    """
    # Calculate the Levenshtein distance
    lev_dist = levenshtein_distance(s1, s2)
    
    # Find the maximum possible distance (length of the longer string)
    max_distance = max(len(s1), len(s2))
    
    # Calculate the ratio of Levenshtein distance to maximum distance
    ratio = lev_dist / max_distance
    
    return 1 - ratio

def compare_attachments(attachments_1: List[nextcord.Attachment], attachments_2: List[nextcord.Attachment]) -> bool:
    """
    Checks if any attachments are the same.

    :param attachments_1: The first list of attachments.
    :type attachments_1: List[nextcord.Attachment]
    :param attachments_2: The second list of attachments.
    :type attachments_2: List[nextcord.Attachment]
    :return: True if any attachments are the same, False otherwise.
    :rtype: bool
    """
    # Quick optimizations
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

def normalized_exponential_decay(x: float, k: float = 5) -> float:
    """
    Exponentially decay the input x (0 to 1) normalized to the range [0, 1].
    
    :param x: Input value between 0 and 1.
    :type x: float
    :param k: Decay rate (higher values decay faster).
    :type k: float
    :return: The normalized exponentially decayed value.
    :rtype: float
    """
    return (1 - math.exp(-k * x)) / (1 - math.exp(-k))

async def check_and_trigger_spam_moderation_for_message(message: nextcord.Message, server: Server) -> bool:
    """
    Checks if the given message should trigger spam moderation and punishes the user if it does.

    :param message: The message to check.
    :type message: nextcord.Message
    :param server: The server that the message is from.
    :type server: Server
    :return: True if a strike was given, False otherwise.
    :rtype: bool
    """
    max_messages_to_check = get_configs()["spam-moderation"]["max-messages-to-check"]    # The MAXIMUM messages InfiniBot will try to check for spam
    message_chars_to_check_repetition = get_configs()["spam-moderation"]["message-chars-to-check-repetition"]    # A message requires these many characters before it is checked for repetition

    # If Spam is Enabled
    if not utils.feature_is_active(server=server, feature="moderation__spam"): return False

    # Check if InfiniBot can view the audit log
    if not message.guild.me.guild_permissions.view_audit_log:
        await utils.send_error_message_to_server_owner(message.guild, "View Audit Log", channel=message.channel.name)
        return False

    # Configure limit (the most messages that we're willing to check)
    if server.spam_moderation_profile.score_threshold < max_messages_to_check:
        limit = server.spam_moderation_profile.score_threshold + 1 # Add one because of the existing message
    else:
        limit = max_messages_to_check

    # Get previous messages
    previous_messages = message.channel.history(limit=limit)
    
    # Loop through each previous message and test it
    spam_score = 0
    async for _message in previous_messages:
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
            await utils.timeout(message.author, server.spam_moderation_profile.timeout_seconds, reason=f"Spam Moderation: User exceeded spam message limit of {server.spam_moderation_profile.score_threshold} points.")
            
            # Send them a message (if they want it)
            if Member(message.author.id).direct_messages_enabled:
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
    
        return True

    return False


# Other Moderation ----------------------------------------------------------------------------------------------------------
def contains_discord_invite(message):
    """
    Detects if a message contains a Discord invite link.

    :param message: The message to check.
    :type message: str
    :return: True if a Discord invite link is detected, False otherwise.
    :rtype: bool
    """
    # Regular expression for Discord invite links
    discord_invite_pattern = r"(?:https?://)?(?:www\.)?(?:discord\.gg|discordapp\.com/invite|discord\.com/invite)/[\w-]+"

    # Search for the pattern in the message
    return re.search(discord_invite_pattern, message) is not None

async def check_and_delete_invite_links(message: nextcord.Message) -> bool:
    """
    Checks if the message contains a Discord invite link and deletes it if present.
    Only runs if the server has the "delete_invites" feature enabled.

    :param message: The message to check for invite links.
    :type message: nextcord.Message

    :return: True if an invite link was found and the message was deleted, False otherwise.
    :rtype: bool
    """
    # If invite link deletion is enabled
    if not utils.feature_is_active(guild=message.guild, feature="delete_invite_links"):
        return False

    if message.author.bot: return False
    if message.author.id == message.guild.owner_id: return False
    if message.author.guild_permissions.administrator: return False

    # Check if the message contains an invite link
    if contains_discord_invite(message.content):
        # Delete the message
        try:
            await message.delete()
            return True
        except nextcord.errors.Forbidden:
            await utils.send_error_message_to_server_owner(
                message.guild, "Manage Messages", channel=message.channel.name
            )
            return False

    return False


# Moderation Actions ----------------------------------------------------------------------------------------------------------
async def daily_moderation_maintenance(bot: nextcord.Client, guild: nextcord.Guild) -> None:
    """|coro|

    The midnight action for moderation, handling strikes for profanity moderation.
    If bot is unloaded, the action will be automatically handled and delayed for 30 minutes.

    :param bot: The bot client.
    :type bot: nextcord.Client
    :return: None
    :rtype: None
    """
    logging.info(f"Running midnight action for moderation in guild: {guild.name})({guild.id})")
    if get_global_kill_status()["moderation__profanity"]:
        logging.warning("SKIPPING profanity moderation strike update because of global kill status.")
        return
    if get_bot_load_status() == False:
        logging.warning("SKIPPING profanity moderation strike update because of bot load status.")
        return
    
    try:
        if guild == None: return

        server = Server(guild.id)
        
        # Checks
        if server == None: return
        if server.profanity_moderation_profile.active == False: return
        if server.profanity_moderation_profile.strike_system_active == False: return
        if server.profanity_moderation_profile.strike_expiring_active == False: return
        
        # Go through each member and edit
        for member_strike_info in server.moderation_strikes:
            try:
                member = guild.get_member(member_strike_info.member_id)
                if member == None: # Member is no longer in the server
                    # Remove the member
                    server.member_levels.delete(member_strike_info.member_id)
                    continue

                # Check if the member has strikes
                if (member_strike_info.strikes == 0): 
                    server.moderation_strikes.delete(member_strike_info.member_id)
                    continue

                # Convert string to UTC-aware datetime
                strike_date = datetime.datetime.strptime(
                    member_strike_info.last_strike, 
                    "%Y-%m-%d %H:%M:%S.%f"
                ).replace(tzinfo=datetime.timezone.utc)

                # Determine if within the window for strike removal
                if (strike_date + datetime.timedelta(days = server.profanity_moderation_profile.strike_expire_days) > datetime.datetime.now(datetime.timezone.utc)): 
                    continue

                # Remove a single strike
                _strikes = member_strike_info.strikes
                _strikes -= 1
                if _strikes > 0:
                    # Update the member's record
                    server.moderation_strikes.edit(member_strike_info.member_id, strikes = _strikes, last_strike = datetime.datetime.now())
                    logging.info(f"Member's strike has been removed. Server: {guild.name} ({guild.id})")
                else:
                    # Remove the member's record
                    server.moderation_strikes.delete(member_strike_info.member_id)
                    logging.info(f"Member's record has been removed. Server: {guild.name} ({guild.id})")

            except Exception as err:
                logging.error(f"ERROR when checking profanity moderation (member) in server {guild.id}: {err}", exc_info=True)
                continue
        
    except Exception as err:
        logging.error(f"ERROR When checking profanity moderation (server) in server {guild.id}: {err}", exc_info=True)


# Commands
async def check_and_run_moderation_commands(bot: nextcord.Client, message: nextcord.Message) -> bool:
    """
    Checks if any moderation commands should be run, and runs them if needed.

    :param bot: The bot client.
    :type bot: nextcord.Client
    :param message: The message to check.
    :type message: nextcord.Message

    :return: If the message was flagged for something.
    :rtype: bool
    """
    if message.guild == None: return # Guild not loaded yet.
    if message.author == None: return
    if message.author.bot: return # Don't check messages from bots

    if message.author.guild_permissions.administrator: # Don't check profanity for admins
        logging.debug(f"Skipped profanity check for admin in {__name__}: {message.author}")
        return False
    
    server = Server(message.guild.id)

    with log_manager.LogIfFailure(feature="check_and_trigger_profanity_moderation_for_message"):
        message_is_profane = await check_and_trigger_profanity_moderation_for_message(bot, server, message, skip_admin_check=True)
        if message_is_profane: 
            return True

    # Check Invites
    with log_manager.LogIfFailure(feature="check_and_delete_invite_links"):
        message_is_invite = await check_and_delete_invite_links(message)
        if message_is_invite:
            return True

    # Check spam
    with log_manager.LogIfFailure(feature="check_and_trigger_spam_moderation_for_message"):
        message_is_spam = await check_and_trigger_spam_moderation_for_message(message, server)
        if message_is_spam:
            return True
    
    return False
    
async def run_my_strikes_command(interaction: nextcord.Interaction) -> None:
    """
    Runs the command to view the strikes of the user who invoked it.

    :param interaction: The interaction object from the Discord event.
    :type interaction: nextcord.Interaction

    :return: None
    :rtype: None
    """

    if not await check_profanity_moderation_enabled_and_warn_if_not(interaction): return

    server = Server(interaction.guild.id)
    if interaction.user.id in server.moderation_strikes:
        strike = server.moderation_strikes[interaction.user.id].strikes
    else:
        strike = 0

    await interaction.response.send_message(embed = nextcord.Embed(title = f"My Strikes", description = f"You are at {strike} strike{"s" if strike != 1 else ""}.", 
                                                                   color =  nextcord.Color.blue()), ephemeral = True)

async def run_view_member_strikes_command(interaction: nextcord.Interaction, member: nextcord.Member) -> None:
    """
    Runs the command to view the strikes of a specified member.

    :param interaction: The interaction object from the Discord event.
    :type interaction: nextcord.Interaction
    :param member: The member whose strikes are to be viewed.
    :type member: nextcord.Member

    :return: None
    :rtype: None
    """

    if await utils.user_has_config_permissions(interaction):
        server = Server(interaction.guild.id)
        if not await check_profanity_moderation_enabled_and_warn_if_not(interaction): return

        server = Server(interaction.guild.id)
        if member.id in server.moderation_strikes:
            strike = server.moderation_strikes[member.id].strikes
        else:
            strike = 0

        embed = nextcord.Embed(title = f"View Member Strikes", description = f"{member.mention} is at {str(strike)} strike{"s" if strike != 1 else ""}.", color =  nextcord.Color.blue())
        await interaction.response.send_message(embed = embed, ephemeral = True)

async def run_set_admin_channel_command(interaction: nextcord.Interaction) -> None:
    """
    Runs the command to set the admin channel for moderation updates and alerts.

    :param interaction: The interaction object from the Discord event.
    :type interaction: nextcord.Interaction
    
    :return: None
    :rtype: None
    """

    if await utils.user_has_config_permissions(interaction) and await utils.check_and_warn_if_channel_is_text_channel(interaction):
        server = Server(interaction.guild.id)

        server.profanity_moderation_profile.channel = interaction.channel.id

        embed = nextcord.Embed(title = "Admin Channel Set", description = f"Moderation updates and alerts will now be logged in this channel.\n\n**Ensure Admin-Only Access**\nThis channel lets members report incorrect strikes, so limit access to admins.", color =  nextcord.Color.green())
        embed.set_footer(text = f"Action done by {interaction.user}")
        await interaction.response.send_message(embed = embed, view = ui_components.SupportAndInviteView())