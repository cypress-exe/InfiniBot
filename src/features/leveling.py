import logging
import math
import re
from typing import Union

import nextcord
from nextcord import Interaction

from components import utils, ui_components
from config.messages.cached_messages import cache_message, get_cached_messages_from_channel
from config.messages.utils import MessageRecord
from config.global_settings import get_bot_load_status, get_global_kill_status
from config.member import Member
from config.server import Server
from features.moderation import get_percent_similar
from modules.custom_types import UNSET_VALUE

# Utility Functions
def compress_string(input_string: str) -> str:
    """
    Remove all non-alphanumeric characters and spaces from a given string.

    :param input_string: The string to compress.
    :type input_string: str
    :return: The compressed string.
    :rtype: str
    """
    # Remove all non-alphanumeric characters and spaces
    compressed = re.sub(r'[^a-zA-Z0-9]', '', input_string)
    return compressed

def get_level_from_points(points: int) -> int:
    """
    Get the level from a given number of points.

    :param points: The number of points to calculate the level from.
    :type points: int
    :return: The level calculated from the given points.
    :rtype: int
    """
    if points <= 0: return 0

    points /= 10
    if points == 0: return 0
    return(math.floor(points ** 0.65)) #levels are calculated by x^0.65

def get_points_from_level(level: int) -> int:
    """
    Get the number of points from a given level.

    :param level: The level to calculate the points from.
    :type level: int
    :return: The number of points calculated from the given level.
    :rtype: int
    """
    if level <= 0: return 0
    
    points = level**(1/0.65)
    points *= 10
    points = math.floor(points)
    
    for _ in range(0, 100):
        if get_level_from_points(points) == level:
            return points
        elif get_level_from_points(points) > level:
            points -= 1
        else:
            points += 1
    
    return(points) #levels are calculated by x^0.65

def get_ranked_members(guild: nextcord.Guild) -> list[list[nextcord.Member, int]]:
    """
    Get a list of ranked members in a guild sorted by level points. (Only includes members with points)  
    Note: Returned list is sorted by points but index does not necessarily represent rank.

    :param guild: The guild to get the ranked members from.
    :type guild: nextcord.Guild
    :return: A list of [int, points] lists sorted by points in descending order.
    :rtype: list[list[int, int]]
    """
    ranked_members:list[list[int, int]] = []
    server = Server(guild.id)

    for member_level_info in server.member_levels:
            ranked_members.append([member_level_info.member_id, member_level_info.points])

    ranked_members = sorted(ranked_members, key=lambda x: (-x[1], f"<@{x[0]}>"))
    return ranked_members

def calculate_rank_for_member(ranked_members: list[list[int, int]], target_member_id: int = None) -> Union[list[tuple[int, int, int]], tuple[int, int]]:
    """
    Calculate ranks for all members or find the rank of a specific member.
    
    :param ranked_members: The list of ranked members from get_ranked_members()
    :type ranked_members: list[list[int, int]]
    :param member_id: Optional member ID to find the specific rank for
    :type member_id: int, optional
    :return: If member_id is provided, returns a tuple (rank, points) for that member,
             otherwise returns a list of (rank, member, points) tuples for all members
    :rtype: list[tuple[int, int, int]] or tuple[int, int]
    """
    results = []
    rank, last_points = 1, None
    
    for index, package in enumerate(ranked_members):
        member_id = package[0]
        points = package[1]
        
        # Update rank if points are less than previous member's points
        if last_points is not None and points < last_points:
            rank += 1
        
        # If we're looking for a specific member and found them
        if target_member_id == member_id:
            return (rank, points)
        
        # Otherwise, add to results list
        results.append((rank, member_id, points))
        last_points = points
    
    # If we were looking for a specific member and didn't find them
    if target_member_id is not None:
        return (0, 0)
        
    return results

def get_member_rank(guild: nextcord.Guild, member_id: int) -> tuple[int, int]:
    """
    Get a member's rank and points in a guild.

    :param guild: The guild to get the rank from.
    :type guild: nextcord.Guild
    :param member_id: The ID of the member to get the rank for.
    :type member_id: int
    :return: A tuple containing (rank, points)
    :rtype: tuple[int, int]
    """
    ranked_members = get_ranked_members(guild)
    return calculate_rank_for_member(ranked_members, target_member_id=member_id)

def add_leaderboard_ranking_to_embed(guild: nextcord.Guild, embed: nextcord.Embed, include_ranked_members: bool = False) -> nextcord.Embed:
    """
    Add a leaderboard ranking to an embed.

    :param guild: The guild to get the leaderboard from.
    :type guild: nextcord.Guild
    :param embed: The embed to add the leaderboard to.
    :type embed: nextcord.Embed
    :param include_ranked_members: Whether or not to include the ranked members in the embed. Defaults to False.
    :type include_ranked_members: bool, optional
    :return: The embed with the leaderboard added.
    :rtype: nextcord.Embed
    """
    ranked_members = get_ranked_members(guild)
    ranked_results = calculate_rank_for_member(ranked_members)

    if len(ranked_results) == 0:
        embed.add_field(
            name="No members found",
            value="There are no members with points in this server. To level up, send messages in the server!",
            inline=False
        )
    
    for index, (rank, member_id, points) in enumerate(ranked_results):
        if index >= 20:
            remaining_members = len(ranked_results) - 20
            embed.add_field(
                name=f"+ {remaining_members} more",
                value="To see a specific member's level, type `/level [member]`",
                inline=False
            )
            break

        level = get_level_from_points(points)

        embed.add_field(
            name=f"#{rank} | Level {level} ({points} pts)",
            value=f"<@{member_id}>",
            inline=False
        )

    if include_ranked_members:
        return embed, ranked_members
    return embed



# Actions
async def daily_leveling_maintenance(bot: nextcord.Client, guild: nextcord.Guild) -> None:
    """
    |coro|

    Execute the midnight leveling action to update member levels and manage leveling-related tasks.

    :param bot: The instance of the bot client.
    :type bot: nextcord.Client
    :param guild: The guild instance where the leveling action is executed.
    :type guild: nextcord.Guild
    :return: None
    :rtype: None
    """
    logging.info(f"Running midnight action for leveling in guild: {guild.name})({guild.id})")
    if get_global_kill_status()["leveling"]:
        logging.warning("Skipping leveling because of global kill status.")
        return
    if get_bot_load_status() == False:
        logging.warning("Skipping leveling because of bot load status.")
        return
    
    try:
        if guild == None: return

        server = Server(guild.id)
        
        # Checks
        if server == None : return
        if server.leveling_profile.active == False: return
        if server.leveling_profile.points_lost_per_day == 0: return
        
        # Go through each member and edit
        for member_level_info in server.member_levels:
            try:
                member = await utils.get_member(guild, member_level_info.member_id, override_failed_cache=True)
                if member == None:
                    logging.warning(f"Member {member_level_info.member_id} not found in guild {guild.id}. Removing from member levels.")
                    # Remove the member if they are not found
                    server.member_levels.delete(member_level_info.member_id)
                    continue

                # Remove the points
                _points = member_level_info.points
                _points -= server.leveling_profile.points_lost_per_day
                if _points < 0:
                    _points = 0

                # Update the member
                server.member_levels.edit(member_level_info.member_id, points = _points)

                await process_level_change(guild, member)

                # Remove the member if they have no points
                if member_level_info.points == 0:
                    server.member_levels.delete(member_level_info.member_id)

            except Exception as err:
                logging.error(f"ERROR when checking levels (member) in server {guild.id}: {err}", exc_info=True)
                continue
        
    except Exception as err:
        logging.error(f"ERROR When checking levels (server) in server {guild.id}: {err}", exc_info=True)

async def check_leveling_enabled_and_warn_if_not(interaction: Interaction, server: Server) -> bool:
    """
    |coro|

    Determines whether or not leveling is enabled for the server. NOT SILENT!

    :param interaction: The interaction object from the Discord event.
    :type interaction: Interaction
    :param server: The server object where leveling is being checked.
    :type server: Server
    :return: Whether or not leveling is enabled.
    :rtype: bool
    """
    if utils.feature_is_active(server = server, feature = "leveling"):
        return True
    else:
        if not get_global_kill_status()["leveling"]:
            await interaction.response.send_message(embed = nextcord.Embed(title = "Leveling has been turned off.", description = "Go to the `/dashboard` to turn it back on.", color = nextcord.Color.red()), ephemeral = True)
            return False
        else:
            await interaction.response.send_message(embed = nextcord.Embed(title = "Leveling Disabled", description = "Leveling has been disabled by the developers of InfiniBot. This is likely due to an critical instability with it right now. It will be re-enabled shortly after the issue has been resolved.", color = nextcord.Color.red()), ephemeral = True)
            return False

async def grant_xp_for_message(message: nextcord.Message) -> None:
    """
    |coro|

    Manages the distribution of xp (and also levels and level rewards, but indirect). Simply requires a message.

    :param message: The message that triggered the xp distribution.
    :type message: nextcord.Message
    :return: None
    :rtype: None
    """
    MESSAGES_TO_CHECK_FOR_SPAM = 5

    # Confirm that leveling is enabled
    if not utils.feature_is_active(server_id = message.guild.id, feature = "leveling"): return
    
    member = message.author
    if member.bot: return # Don't give xp to bots

    channel = message.channel
    
    server = Server(message.guild.id)
    if message.channel.id in server.leveling_profile.exempt_channels: return

    # Cache message
    cache_message(message, skip_if_exists=True)

    # Anti-spam logic
    previous_messages = get_cached_messages_from_channel(channel.id)[::-1]
    limit = MESSAGES_TO_CHECK_FOR_SPAM + 1
    if len(previous_messages) > limit:
        previous_messages = previous_messages[:limit]

    # printout = [message.content for message in previous_messages]
    # logging.info(f"Previous Messages: {printout}")

    points_multiplier = 1
    forgiveness = 3

    # Skip if we don't have enough messages to compare
    if len(previous_messages) <= 1:
        logging.debug("Not enough previous messages found for spam comparison.")
    else:
        # Skip the first message (current message) and process the rest
        previous_messages_to_check: list[MessageRecord] = previous_messages[1:]
        
        for previous_message in reversed(previous_messages_to_check):
            if previous_message.content is None or previous_message.content == "": 
                continue
            if previous_message.author_id != member.id: 
                continue
            
            # Compare the messages using spam moderation's get_percent_similar (from moderation)
            percent_similar = get_percent_similar(previous_message.content, message.content)

            factor = 1 - percent_similar  # Adjustment factor
            points_multiplier *= factor
            points_multiplier += forgiveness * (points_multiplier/2)  # Gradual increase towards 1
            
            # Keep the multiplier between 0 and 1
            if points_multiplier > 1:
                points_multiplier = 1
            elif points_multiplier < 0:
                points_multiplier = 0

    message_compressed = compress_string(message.content)
    total_points = len(message_compressed) / 10
    
    # Cap points
    if server.leveling_profile.max_points_per_message:
        if total_points > server.leveling_profile.max_points_per_message:
            total_points = server.leveling_profile.max_points_per_message
    
    # Apply multiplier
    total_points *= points_multiplier
    total_points = round(total_points)

    logging.debug(f"Granted {total_points} points.")

    # Get previous level
    if member.id in server.member_levels: original_points = server.member_levels[member.id].points
    else: original_points = 0
    original_level = get_level_from_points(original_points)

    # Get current level
    current_level = get_level_from_points(original_points + total_points)

    # Update points
    if member.id not in server.member_levels:
        server.member_levels.add(member_id = member.id, points = total_points)
    else:
        server.member_levels.edit(member_id = member.id, points = original_points + total_points)
    
    if original_level != current_level: # Ensure that the level has changed (optimization)
        await process_level_change(message.guild, message.author, levelup_announce = True)
  
async def process_level_change(guild: nextcord.Guild, member: nextcord.Member, levelup_announce: bool = False, silent = False) -> None:
    """
    |coro|

    Handles the distribution of levels and level rewards.

    :param guild: The guild object where the level change is happening.
    :type guild: nextcord.Guild
    :param member: The member object whose level is being changed.
    :type member: nextcord.Member
    :param levelup_announce: Whether or not to announce the level-up in the leveling channel.
    :type levelup_announce: bool
    :param silent: Whether or not to show the level-up message.
    :type silent: bool
    :return: None
    :rtype: None
    """
    server = Server(guild.id)

    if member is None: return

    # Get points
    if member.id in server.member_levels: points = server.member_levels[member.id].points
    else: points = 0
    level = get_level_from_points(points)

    member_settings = Member(member.id)
      
    # Level-up message
    if levelup_announce and (not silent):
        if server.leveling_profile.channel != None:
            _continue = True
            
            leveling_channel_id = server.leveling_profile.channel
            if leveling_channel_id == None: _continue = False # Level messages are disabled
            elif leveling_channel_id == UNSET_VALUE: leveling_channel = guild.system_channel # Use the system messages channel
            else: leveling_channel = guild.get_channel(leveling_channel_id) # Use the leveling channel
            
            if leveling_channel == None: _continue = False # Either the system messages channel is not set, or the leveling channel does not exist
            if not await utils.check_text_channel_permissions(leveling_channel, auto_warn=True, custom_channel_name="the leveling channel"): _continue = False

            if _continue:
                embed: nextcord.Embed = server.leveling_profile.level_up_embed.to_embed()

                # Get member's current rank
                rank, _ = get_member_rank(guild, member.id)
                
                embed = utils.apply_generic_replacements(embed, member, guild, custom_replacements={
                    "[level]": str(level),
                    "[points]": str(points),
                    "[rank]": f"#{rank}",
                    })
                embeds = [embed]
                
                # Get the card (if needed)
                if server.leveling_profile.allow_leveling_cards:
                    if member_settings.level_up_card_enabled:
                        card_embed = member_settings.level_up_card_embed.to_embed()
                        card = utils.apply_generic_replacements(card_embed, member, guild, custom_replacements={"[level]": str(level)}, skip_channel_replacement=True)
                        embeds.append(card)
                
                # Send message
                await leveling_channel.send(embeds = embeds)
             
    # Level-Reward messages
    if utils.feature_is_active(server_id = guild.id, feature = "level_rewards"):
        member_role_ids = [role.id for role in member.roles if role.name != "@everyone"]
        for level_reward in server.level_rewards:
            if level_reward.level <= level:
                # We need to give them this role.
                if not level_reward.role_id in member_role_ids:
                    try:
                        role = guild.get_role(level_reward.role_id)
                        if role == None: continue
                        await member.add_roles(role, reason = "Level Reward")
                    except nextcord.errors.Forbidden:
                        await utils.send_error_message_to_server_owner(guild, "Manage Roles", guild_permission = True)
                        return
                    
                    # Send a notifications
                    if not silent:
                        # DM Them
                        if member_settings.direct_messages_enabled:
                            embed = nextcord.Embed(title = f"Congratulations! You leveled up in {guild.name}!", description = f"As a result, you were granted the role `@{role.name}`. Keep your levels up, or else you might lose it!", color = nextcord.Color.purple())
                            embed.set_footer(text = "To opt out of dm notifications, use /opt_out_of_dms")
                            try:
                                await member.send(embed = embed)
                            except nextcord.errors.Forbidden:
                                # DMs are disabled
                                pass
                    
            else:
                # We need to remove the role
                if level_reward.role_id in member_role_ids:
                    try:
                        role = guild.get_role(level_reward.role_id)
                        if role == None: continue
                        await member.remove_roles(role, reason = "Level Reward")
                    except nextcord.errors.Forbidden:
                        await utils.send_error_message_to_server_owner(guild, "Manage Roles", guild_permission = True)
                        return
                    
                    # Send a notifications
                    if not silent:
                        # DM Them
                        if member_settings.direct_messages_enabled:
                            embed = nextcord.Embed(title = f"Oh, no! You lost a level in {guild.name}!", description = f"As a result, the role `@{role.name}` has been revoked. Bring your levels back up, and earn back your role!", color = nextcord.Color.purple())
                            embed.set_footer(text = "To opt out of dm notifications, use /opt_out_of_dms")
                            try:
                                await member.send(embed = embed)
                            except nextcord.errors.Forbidden:
                                # DMs are disabled
                                pass

async def handle_member_removal(member: nextcord.Member):
    """
    Handles the removal of a member from the server.

    :param member: The member object that was removed from the server.
    :type member: nextcord.Member
    :return: None
    :rtype: None
    """
    server = Server(member.guild.id)
    if utils.feature_is_active(server = server, feature = "leveling"):
        if member.id in server.member_levels:
            server.member_levels.delete(member.id)

# Commands
async def run_leaderboard_command(interaction: Interaction):
    """
    Executes the leaderboard command, displaying the level leaderboard for the server.

    :param interaction: The interaction object from the Discord event.
    :type interaction: Interaction

    :return: None
    :rtype: None
    """
    server = Server(interaction.guild.id)
    if not await check_leveling_enabled_and_warn_if_not(interaction, server): return
    
    embed = nextcord.Embed(title="Leaderboard", color=nextcord.Color.blue())
    embed = add_leaderboard_ranking_to_embed(interaction.guild, embed)

    embed.description = "\n\nTo learn more about leveling, visit [this link](https://cypress-exe.github.io/InfiniBot/docs/core-features/leveling/)."
    
    await interaction.response.send_message(embed=embed, view=ui_components.InviteView())
    
async def run_view_level_command(interaction: Interaction, member: nextcord.Member):
    """
    |coro|

    Executes the command to view the level of another member.

    :param interaction: The interaction object from the Discord event.
    :type interaction: Interaction
    :param member: The member whose level is to be viewed.
    :type member: nextcord.Member

    :return: None
    :rtype: None
    """
    server = Server(interaction.guild.id)
    if not await check_leveling_enabled_and_warn_if_not(interaction, server): return

    _member = member if member != None else interaction.user
    
    if _member.id in server.member_levels:
        member_level_info = server.member_levels[_member.id]
        points = member_level_info.points
    else:
        points = 0
        
    level = get_level_from_points(points)
    
    # Get member's rank
    rank, _ = get_member_rank(interaction.guild, _member.id)
    rank_text = f"(Rank #{rank})" if rank > 0 else "(Not ranked)"
    
    description = f"""
    {_member.mention} is at level {str(level)} {rank_text} (points: {str(points)})

    To learn more about leveling, visit [this link](https://cypress-exe.github.io/InfiniBot/docs/core-features/leveling/).
    """

    description = utils.standardize_str_indention(description)
    await interaction.response.send_message(embed = nextcord.Embed(title = "View Level", description = description, color = nextcord.Color.blue()), ephemeral=True, view = ui_components.InviteView())

async def run_set_level_command(interaction: Interaction, member: nextcord.Member, new_level: int):
    """
    |coro|

    Executes the command to set a new level for a specified member.

    :param interaction: The interaction object from the Discord event.
    :type interaction: Interaction
    :param member: The member whose level is to be set.
    :type member: nextcord.Member
    :param new_level: The new level to set for the member.
    :type new_level: int

    :return: None
    :rtype: None
    """
    server = Server(interaction.guild.id)
    if not await check_leveling_enabled_and_warn_if_not(interaction, server): return

    if await utils.user_has_config_permissions(interaction):
        if new_level < 0:
            await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "\"Level\" needs to be a positive number.", color = nextcord.Color.red()), ephemeral=True)
            return
        
        if new_level > 9999:
            await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "\"Level\" needs to be less than or equal to 9999.", color = nextcord.Color.red()), ephemeral=True)
            return

        # Get previous level
        if member.id in server.member_levels: original_points = server.member_levels[member.id].points
        else: original_points = 0
        original_level = get_level_from_points(original_points)

        # Get new points
        new_points = get_points_from_level(new_level)

        # Update points
        if member.id not in server.member_levels:
            server.member_levels.add(member_id = member.id, points = new_points)
        else:
            server.member_levels.edit(member_id = member.id, points = new_points)
        
        description = f"""
        {member.mention} is now at level {str(new_level)} (points: {str(new_points)})

        To learn more about leveling, visit [this link](https://cypress-exe.github.io/InfiniBot/docs/core-features/leveling/).
        """
        description = utils.standardize_str_indention(description)
        embed = nextcord.Embed(title = "Level Changed", description = description, color = nextcord.Color.green())
        embed.set_footer(text=f"Action done by {interaction.user}")

        await interaction.response.send_message(embed = embed)
        if original_level != new_level: await process_level_change(interaction.guild, member)
