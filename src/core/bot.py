import logging
import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands
import os
import json

from components import ui_components, utils
import config.global_settings as global_settings
from config.server import Server
from config import stored_messages
from core import log_manager
from core.api_connections_manager import start_all_api_connections
from core.log_manager import LogIfFailure
from core.server_join_and_leave_manager import handle_server_join, handle_server_remove
from core.scheduling import start_scheduler, stop_scheduler
from core.view_manager import init_views

from features import (
    about,
    action_logging,
    admin_commands,
    autobans,
    check_infinibot_permissions,
    dashboard,
    default_roles,
    dm_commands,
    embeds,
    help_commands,
    join_leave_messages,
    join_to_create_vcs,
    jokes,
    leveling,
    moderation,
    motivational_statements,
    onboarding,
    profile,
    purging,
    reaction_roles,
    role_messages
)

from features.options_menu import entrypoint_ui

# INIT BOT ==============================================================================================================================================================
intents = nextcord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.reactions = True

# Calculate optimal shard count based on configuration and previous data
def calculate_shard_count():
    """Calculate optimal shard count based on configuration and stored guild data"""
    try:
        # Check if sharding is enabled in config
        if not global_settings.get_configs()["sharding"]["enabled"]:
            logging.info("Auto-sharding is disabled in configuration. Using Discord's recommendation.")
            return None
        
        guilds_per_shard = global_settings.get_configs()["sharding"]["guilds-per-shard"]
        
        # Try to read previous guild count from shard_config.json
        shard_config_path = os.path.join("generated", "configure", "shard_config.json")
        previous_guild_count = 0
        
        try:
            with open(shard_config_path, 'r') as f:
                shard_data = json.load(f)
                previous_guild_count = shard_data.get("last_guild_count", 0)
        except (FileNotFoundError, json.JSONDecodeError):
            logging.info("No previous shard data found. Will calibrate on first startup.")
            return None
        
        if previous_guild_count == 0:
            logging.info("No previous guild count data. Will calibrate on first startup.")
            return None
        
        # Calculate optimal shard count
        calculated_shards = max(1, (previous_guild_count // guilds_per_shard) + 1)
        logging.info(f"Calculated {calculated_shards} shards for {previous_guild_count} guilds ({guilds_per_shard} guilds per shard)")
        
        return calculated_shards
        
    except Exception as e:
        logging.warning(f"Error calculating shard count: {e}. Using Discord's recommendation.")
        return None

# Get shard count
shard_count = calculate_shard_count()

if shard_count:
    bot = commands.AutoShardedBot(intents = intents, 
                                allowed_mentions = nextcord.AllowedMentions(everyone = True), 
                                help_command=None,
                                shard_count=shard_count)
    logging.info(f"Using calculated shard count: {shard_count}")
else:
    bot = commands.AutoShardedBot(intents = intents, 
                                allowed_mentions = nextcord.AllowedMentions(everyone = True), 
                                help_command=None)
    logging.info("Using Discord's automatic shard recommendation")

def get_bot() -> commands.AutoShardedBot: return bot

@bot.event
async def on_ready() -> None: # Bot load
    """
    This function is triggered when the bot becomes ready and all shards are ready.
    It waits for the bot to be fully ready, logs the bot's username, sets bot load status,
    starts the scheduler, and optionally logs which guilds are on which shard.

    :return: None
    :rtype: None
    """

    await bot.wait_until_ready()
    logging.info(f"============================== Logged in as: {bot.user.name} with all shards ready. ==============================")
    logging.info(f"Bot is running with {bot.shard_count} shards across {len(bot.guilds)} guilds.")

    global_settings.set_bot_load_status(True)
    global_settings.update_bot_id(bot)
    start_scheduler()
    start_all_api_connections()
    init_views(bot)

    # Log shard distribution and save data for next startup
    shard_guild_counts = {}
    total_guilds = len(bot.guilds)
    
    for guild in bot.guilds:
        shard_id = guild.shard_id
        if shard_id not in shard_guild_counts:
            shard_guild_counts[shard_id] = 0
        shard_guild_counts[shard_id] += 1
    
    # Save guild count data for next startup
    try:
        shard_config_path = os.path.join("generated", "configure", "shard_config.json")
        os.makedirs(os.path.dirname(shard_config_path), exist_ok=True)
        
        shard_data = {
            "last_guild_count": total_guilds,
            "last_shard_count": bot.shard_count,
            "last_updated": "2025-06-24",
            "guilds_per_shard_config": global_settings.get_configs()["sharding"]["guilds-per-shard"]
        }
        
        with open(shard_config_path, 'w') as f:
            json.dump(shard_data, f, indent=2)
            
        logging.info(f"Saved guild count data: {total_guilds} guilds across {bot.shard_count} shards")
        
    except Exception as e:
        logging.warning(f"Could not save shard data: {e}")
    
    # Display shard distribution
    logging.info("Shard distribution:")
    max_guilds_per_shard = 0
    for shard_id in sorted(shard_guild_counts.keys()):
        guild_count = shard_guild_counts[shard_id]
        max_guilds_per_shard = max(max_guilds_per_shard, guild_count)
        logging.info(f"  Shard {shard_id}: {guild_count} guilds")
    
    # Intelligent recommendations
    if global_settings.get_configs()["sharding"]["enabled"]:
        guilds_per_shard = global_settings.get_configs()["sharding"]["guilds-per-shard"]
        optimal_shards = max(1, (total_guilds // guilds_per_shard) + 1)
        
        if max_guilds_per_shard > guilds_per_shard * 1.5:  # 50% over target
            logging.warning(f"⚠️  HIGH SHARD LOAD: Some shards have {max_guilds_per_shard} guilds (target: {guilds_per_shard}). Consider restarting - next startup will use {optimal_shards} shards.")
        elif bot.shard_count < optimal_shards:
            logging.info(f"💡 SCALING SUGGESTION: Current: {bot.shard_count} shards, Optimal: {optimal_shards} shards. Restart to apply.")
        elif bot.shard_count > optimal_shards * 1.5:  # Over-sharded
            logging.info(f"💡 OPTIMIZATION: You might be over-sharded. Current: {bot.shard_count}, Optimal: {optimal_shards}. Restart to optimize.")
        else:
            logging.info(f"✅ SHARD COUNT: Optimal ({bot.shard_count} shards for {total_guilds} guilds)")
    else:
        logging.info(f"ℹ️  AUTO-SHARDING: Disabled in config. Using Discord's recommendation ({bot.shard_count} shards)")

    # Print detailed guild info only in debug mode
    if logging.getLevelName(logging.getLogger().getEffectiveLevel()) == "DEBUG":
      for guild in bot.guilds:
          shard_id = guild.shard_id
          logging.debug(f"Guild: {guild.name} (ID: {guild.id}) is on shard {shard_id}")

    # Check if the bot needs to notify on startup
    if global_settings.get_configs()['notify-on-startup']['enabled']:
        logging.info("Bot startup notification is enabled. Notifying server owner...")
        
        # Find channel
        channel_id = global_settings.get_configs()['notify-on-startup']['channel-id']
        if channel_id is None or channel_id == 0:
            logging.warning("No channel ID specified for startup notification. Skipping notification.")
            return
        
        channel = bot.get_channel(channel_id)

        if channel is None:
            logging.error(f"Channel with ID {channel_id} not found. Please check the channel ID in the configuration.")
            return
        
        # Send notification
        embed = nextcord.Embed(
            title = "InfiniBot is online!",
            description = "InfiniBot has successfully started and is active on all guilds.",
            color = nextcord.Color.green()
        )
        try:
            await channel.send(embed=embed)
            logging.info("Startup notification sent successfully.")
        except nextcord.Forbidden:
            logging.error(f"Failed to send startup notification in channel {channel.name} (ID: {channel.id}). Check permissions.")
    else:
        logging.info("Bot startup notification is disabled. Skipping notification.")


@bot.event
async def on_shard_ready(shard_id: int) -> None:
    """
    Triggered when a specific shard becomes ready. Logs the readiness of each shard
    and performs any necessary actions.
    
    :param shard_id: The ID of the shard that is ready.
    :type shard_id: int
    :return: None
    :rtype: None
    """
    logging.info(f"Shard {shard_id} is ready.")

    with global_settings.ShardLoadedStatus() as shards_loaded:
        shards_loaded.append(shard_id)

    # Optional: Perform shard-specific tasks, such as notifying a server or channel
    # Example:
    # if shard_id == 0:
    #     admin_channel = bot.get_channel(YOUR_ADMIN_CHANNEL_ID)
    #     if admin_channel:
    #         await admin_channel.send(f"Shard {shard_id} is ready.")

@bot.event
async def on_close() -> None:
    """
    Triggered when the bot's connection is about to be closed.

    :return: None
    :rtype: None
    """
    global_settings.set_bot_load_status(False)
    stop_scheduler()
    logging.fatal("InfiniBot is shutting down...")

# SLASH COMMANDS ==============================================================================================================================================================
@bot.slash_command(name="view", description="Requires Infinibot Mod", contexts=[nextcord.InteractionContextType.guild])
async def view(interaction: Interaction): pass

@bot.slash_command(name="set", description="Requires Infinibot Mod", contexts=[nextcord.InteractionContextType.guild])
async def set(interaction: Interaction): pass

@bot.slash_command(name="create", description="Requires Infinibot Mod", contexts=[nextcord.InteractionContextType.guild])
async def create(interaction: Interaction): pass

@bot.slash_command(name="help", description="Get help with InfiniBot")
async def help(interaction: Interaction): 
    await help_commands.run_help_command(interaction)

@bot.slash_command(name="about", description="View bot version, repository, and documentation links")
async def info(interaction: Interaction):
    await about.run_bot_about_command(interaction)

# SERVER COMMANDS ================================================================================================================================================================
@bot.slash_command(name="dashboard", description="Configure InfiniBot (Requires Infinibot Mod)", contexts=[nextcord.InteractionContextType.guild])
async def dashboard_command(interaction: Interaction):
    await dashboard.run_dashboard_command(interaction)

@bot.slash_command(name="profile", description="Configure Your Profile In InfiniBot")
async def profile_command(interaction: Interaction):
    await profile.run_profile_command(interaction)

@create.subcommand(name="infinibot-mod-role", description="Manually trigger InfiniBot to create the Infinibot Mod role")
async def create_infinibot_mod_role(interaction: Interaction):
    role_created = await utils.check_server_for_infinibot_mod_role(interaction.guild)

    if role_created:
        embed = nextcord.Embed(title = "InfiniBot Mod role created!", 
                               description="InfiniBot Mod role has been created. Assign the role to yourself and your admins to unlock all of InfiniBot's features.",
                               color = nextcord.Colour.green())
        await interaction.response.send_message(embed = embed, ephemeral = True)
    else:
        embed = nextcord.Embed(title = "Error creating InfiniBot Mod role.",
                               description="InfiniBot Mod role either already exists or could not be created. Please try again, or contact the support team if the issue persists.",
                               color = nextcord.Colour.red())
        await interaction.response.send_message(embed = embed, ephemeral = True, view=ui_components.SupportView())

# Moderation Commands
@view.subcommand(name="my-strikes", description="View your strikes")
async def my_strikes(interaction: Interaction):
    await moderation.run_my_strikes_command(interaction)

@view.subcommand(name="member-strikes", description="View another member's strikes. (Requires Infinibot Mod)")
async def view_member_strikes(interaction: Interaction, member: nextcord.Member):
    await moderation.run_view_member_strikes_command(interaction, member)

@set.subcommand(name="admin-channel", description="Use this channel to log strikes. Channel should only be viewable by admins. (Requires Infinibot Mod)")
async def set_admin_channel(interaction: Interaction):
    await moderation.run_set_admin_channel_command(interaction)

@set.subcommand(name="log-channel", description="Use this channel for logging. Channel should only be viewable by admins. (Requires Infinibot Mod)")
async def set_log_channel(interaction: Interaction):
    await action_logging.run_set_log_channel_command(interaction)

# Leveling Commands
@bot.slash_command(name="leaderboard", description="Get your level and the level of everyone on the server.", contexts=[nextcord.InteractionContextType.guild])
async def leaderboard(interaction: Interaction):
    await leveling.run_leaderboard_command(interaction)

@view.subcommand(name="level", description="View your or someone else's level.")
async def view_level(interaction: Interaction, member: nextcord.Member = SlashOption(description="The member to view the level of.", required=False)):
    await leveling.run_view_level_command(interaction, member)

@set.subcommand(name="level", description="Set levels for any individual (Requires Infinibot Mod)")
async def set_level(interaction: Interaction, 
                    member: nextcord.Member = SlashOption(description="The member to set the level of.", required=True), 
                    level: int = SlashOption(description="The level to set.", required=True)):
    await leveling.run_set_level_command(interaction, member, level)

# Reaction Role Commands
REACTIONROLETYPES = ["Letters", "Numbers", "Custom"]
@create.subcommand(name="reaction-role", description="Legacy: Create a message allowing users to add/remove roles by themselves. (Requires Infinibot Mod)")
async def reaction_role_command(interaction: Interaction, type: str = SlashOption(choices=["Letters", "Numbers"]), 
                              mention_roles: bool = SlashOption(name="mention-roles", description="Mention the roles with @mention", required=False, default=True)):
    await reaction_roles.run_reaction_role_command(interaction, type, mention_roles)

@create.subcommand(name="custom-reaction-role", description="Legacy: Create a reaction role with customized emojis. (Requires Infinibot Mod)")
async def custom_reaction_role_command(interaction: Interaction, options: str = SlashOption(description="Format: \"👍 = @Member, 🥸 = @Gamer\""), 
                                    mentionRoles: bool = SlashOption(name="mention_roles", description="Mention the roles with @mention", required = False, default = True)):   
    await reaction_roles.run_custom_reaction_role_command(interaction, options, mentionRoles)

# Embed Commands
@create.subcommand(name = "embed", description = "Create a beautiful embed!")
async def create_embed(interaction: Interaction, role: nextcord.Role = SlashOption(description = "Role to Ping", required = False)):
    await embeds.run_create_embed_command(interaction, role)

# Role Message Commands
@create.subcommand(name = "role_message", description = "Create a message allowing users to add/remove roles by themselves. (Requires Infinibot Mod)")
async def create_role_message(interaction: Interaction):
    await role_messages.run_role_message_command(interaction)

# MISC
@bot.slash_command(name="motivational_statement", description="Get, uh, a motivational statement...")
async def motivational_statement(interaction: Interaction):
    await motivational_statements.run_motivational_statement(interaction)

@bot.slash_command(name="joke", description="Get a joke")
async def jokeCommand(interaction: Interaction):
    await jokes.run_joke_command(interaction)

@bot.slash_command(name="purge", description="Purge any channel (requires manage messages permission and Infinibot Mod)", contexts=[nextcord.InteractionContextType.guild])
async def purge(interaction: Interaction, amount: str=SlashOption(description="The amount of messages you want to delete. \"All\" purges the whole channel")):
    await purging.run_purge_command(interaction, amount)

@bot.slash_command(name="onboarding", description="Configure InfiniBot for the first time (Requires InfiniBot Mod)", contexts=[nextcord.InteractionContextType.guild])
async def onboarding_command(interaction: Interaction):
    await onboarding.run_onboarding_command(interaction)

@bot.slash_command(name="check_infinibot_permissions", description="Check InfiniBot's permissions to help diagnose issues.", contexts=[nextcord.InteractionContextType.guild])
async def check_infinibot_permissions_command(interaction: Interaction):
    """
    Check InfiniBot's permissions to help diagnose issues.
    
    :param interaction: The interaction in which the command was invoked.
    :type interaction: :class:`~nextcord.Interaction`
    :return: None
    :rtype: None
    """
    await check_infinibot_permissions.run_check_infinibot_permissions(interaction)

# DM Commands
@bot.slash_command(name="opt_out_of_dms", description="Opt out of receiving DMs from InfiniBot. You can opt back in at any time.", contexts=[nextcord.InteractionContextType.bot_dm])
async def opt_out_of_dms(interaction: Interaction):
    """
    Opt out of receiving DMs from InfiniBot. You can opt back in at any time.
    
    :param interaction: The interaction in which the command was invoked.
    :type interaction: :class:`~nextcord.Interaction`
    :return: None
    :rtype: None
    """
    await dm_commands.run_opt_out_of_dms_command(interaction)

@bot.slash_command(name="opt_into_dms", description="Opt into receiving DMs from InfiniBot. You can opt out at any time.", contexts=[nextcord.InteractionContextType.bot_dm])
async def opt_into_dms(interaction: Interaction):
    """
    Opt in to receiving DMs from InfiniBot. You can opt out at any time.
    
    :param interaction: The interaction in which the command was invoked.
    :type interaction: :class:`~nextcord.Interaction`
    :return: None
    :rtype: None
    """
    await dm_commands.run_opt_into_dms_command(interaction)

# MESSAGE & USER COMMANDS ============================================================================================================================================================== 
@bot.message_command(name="Options")
async def message_command_options(interaction: Interaction, message: nextcord.Message):
    await entrypoint_ui.run_message_command(interaction, message)

@bot.user_command(name="Options")
async def user_command_options(interaction: Interaction, user: nextcord.User):
    await entrypoint_ui.run_member_command(interaction, user)

# ERROR HANDLING ==============================================================================================================================================================
@bot.event
async def on_application_command_error(interaction: Interaction, error) -> None:
    """
    Handles errors in application commands.

    :param interaction: The interaction in which the error occurred.
    :type interaction: :class:`~nextcord.Interaction`
    :param error: The error that occurred during the command execution.
    :type error: :class:`Exception`
    :return: None
    :rtype: None
    """
    # Generate a unique ID for the error
    error_id = log_manager.get_uuid_for_logging()

    # Log the error with the unique ID
    logging.error(f"Error ID: {error_id} - Unhandled exception in application command", exc_info=error)

    # Send a user-friendly error message
    embed = ui_components.INFINIBOT_ERROR_EMBED
    embed.set_footer(text = f"Command Execution - Error ID: {error_id}")
    try:
        await interaction.response.send_message(embed=embed, ephemeral=True, view=ui_components.SupportView())
    except Exception:
        # If the response has already been sent or there's another issue, follow up instead
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True, view=ui_components.SupportView())
            
# CALLBACKS ==============================================================================================================================================================
@bot.event
async def on_message(message: nextcord.Message) -> None:
    """
    Handles incoming messages.

    :param message: The message that was sent.
    :type message: nextcord.Message
    :return: None
    :rtype: None
    """
    if message == None: return
    
    # DM Commands ---------------------------------------------
    if message.guild == None:
        with LogIfFailure(feature="dm_commands.check_and_run_dm_commands"):
            await dm_commands.check_and_run_dm_commands(bot, message)
        
        with LogIfFailure(feature="admin_commands.check_and_run_admin_commands"):
            await admin_commands.check_and_run_admin_commands(message)
        return

    # Don't do anything if the message is from a bot
    if message.author.bot:
        return

    # Store message if logging enabled
    with LogIfFailure(feature="stored_messages.store_message"):
        if utils.feature_is_active(guild = message.guild, feature = "logging"):
            stored_messages.store_message(message)

    # Moderation
    message_is_flagged_for_moderation = False
    with LogIfFailure(feature="moderation.check_and_run_moderation_commands"):
        message_is_flagged_for_moderation = await moderation.check_and_run_moderation_commands(bot, message)
    
    if not message_is_flagged_for_moderation:
        with LogIfFailure(feature="leveling.grant_xp_for_message"):
            await leveling.grant_xp_for_message(message)

        with LogIfFailure(feature="admin_commands.check_and_run_admin_commands"):
            await admin_commands.check_and_run_admin_commands(message)


    # Continue with the Rest of the bot commands
    await bot.process_commands(message)

@bot.event
async def on_raw_message_edit(payload: nextcord.RawMessageUpdateEvent) -> None:
    """
    Handles raw message edit events.

    :param payload: The raw message edit event.
    :type payload: nextcord.RawMessageUpdateEvent
    :return: None
    :rtype: None
    """
    guild = None
    for _guild in bot.guilds:
        if _guild.id == payload.guild_id:
            guild = _guild
            break
    if guild == None: return

    # Find the channel
    channel = None
    for channel in guild.channels:
        if channel.id == payload.channel_id:
            channel = channel
            break
    if channel == None: return
    
    if not channel.permissions_for(guild.me).read_message_history:
        await utils.send_error_message_to_server_owner(guild, "View Message History", channel = f"one or more channels (including #{channel.name})")
        return
    if not guild.me.guild_permissions.view_audit_log:
        await utils.send_error_message_to_server_owner(guild, "View Audit Log", guild_permission = True)
        return
    
    # If we have it, grab the original message
    original_message = payload.cached_message
    if original_message == None:
        # Find db cached message
        original_message = stored_messages.get_message(payload.message_id)
    
    # Find the message
    edited_message = None
    try:
        async for message in channel.history(limit=500):
            if int(message.id) == int(payload.message_id):
                edited_message: nextcord.Message = message
                break
    except:
        return
    
    # Punish profanity (if any)
    with LogIfFailure(feature="moderation.check_and_trigger_profanity_moderation_for_message"):
        await moderation.check_and_trigger_profanity_moderation_for_message(bot, Server(guild.id), edited_message)
            
    # Log the message
    with LogIfFailure(feature="action_logging.log_raw_message_edit"):
        await action_logging.log_raw_message_edit(guild, original_message, edited_message)

    # Update the message in the database
    with LogIfFailure(feature="stored_messages.store_message"):
        if utils.feature_is_active(guild = guild, feature = "logging"):
            stored_messages.remove_message(payload.message_id)
            stored_messages.store_message(edited_message)

@bot.event
async def on_raw_message_delete(payload: nextcord.RawMessageDeleteEvent) -> None:
    """
    Handles raw message delete events.

    :param payload: The raw message delete event.
    :type payload: nextcord.RawMessageDeleteEvent
    :return: None
    :rtype: None
    """
    # Find the message (CSI Time!)
    message = None
    guild = None
    for _guild in bot.guilds:
        if _guild.id == payload.guild_id:
            guild = _guild
            break
    if guild == None: return

    channel = None
    for _channel in guild.channels:
        if _channel.id == payload.channel_id:
            channel = _channel
            break
    
    if channel == None: return

    message = payload.cached_message

    if message == None:
        # Find db cached message
        message = stored_messages.get_message(payload.message_id)
        if (message is not None):
            # Actual values are important instead of object approximations, so replace them
            message.guild = guild
            message.channel = channel
            # Some additional info needs to be fetched
            await message.fetch("author")

    # Log the message
    with LogIfFailure(feature="action_logging.log_raw_message_delete"):
        await action_logging.log_raw_message_delete(bot, guild, channel, message, payload.message_id)

    # Remove the message if we're storing it
    with LogIfFailure(feature="stored_messages.remove_message"):
        if utils.feature_is_active(guild = guild, feature = "logging"):
            stored_messages.remove_message(payload.message_id)

    with LogIfFailure(feature="managed_messages.delete"):
        if utils.feature_is_active(guild = guild, feature = "logging"):
            Server(guild.id).managed_messages.delete(payload.message_id, fail_silently=True)

@bot.event
async def on_member_update(before: nextcord.Member, after: nextcord.Member) -> None:
    """
    Handles member update events.

    :param before: The member before the update.
    :type before: nextcord.Member
    :param after: The member after the update.
    :type after: nextcord.Member
    :return: None
    :rtype: None
    """
    
    # Log the update
    with LogIfFailure(feature="action_logging.log_member_update"):
        await action_logging.log_member_update(before, after)
    
    # Check profanity
    if before.nick != after.nick:
        with LogIfFailure(feature="moderation.check_and_punish_nickname_for_profanity"):
            if after.nick != None: await moderation.check_and_punish_nickname_for_profanity(bot, after.guild, before, after)

@bot.event
async def on_member_join(member: nextcord.Member) -> None:
    """
    Handles member join events.

    :param member: The member that joined.
    :type member: nextcord.Member
    :return: None
    :rtype: None
    """
    # Run AutoBan checks
    with LogIfFailure(feature="autobans.check_and_run_autoban_for_member"):
        if await autobans.check_and_run_autoban_for_member(member):
            return

    # Trigger the welcome message
    with LogIfFailure(feature="join_leave_messages.trigger_join_message"):
        await join_leave_messages.trigger_join_message(member)

    # Add default roles
    with LogIfFailure(feature="default_roles.add_roles_for_new_member"):
        await default_roles.add_roles_for_new_member(member)

@bot.event
async def on_member_remove(member: nextcord.Member) -> None:
    """
    Handles member removal events.

    :param member: The member that was removed.
    :type member: nextcord.Member
    :return: None
    :rtype: None
    """
    if member.id == bot.user.id: return # Don't do anything if WE are removed
    if member.guild == None: return # Can't do anything if the guild is None

    # Verify that the member was not autobanned
    if autobans.member_has_autoban(member):
        logging.info(f"Member {member.id} ({member.name}) was autobanned, skipping leave message and removal handling.")
        
        # Log the removal
        with LogIfFailure(feature="action_logging.log_member_removal"):
            await action_logging.log_member_removal(member.guild, member)
        return

    # Trigger the farewell message
    with LogIfFailure(feature="join_leave_messages.trigger_leave_message"):
        await join_leave_messages.trigger_leave_message(member)

    # Remove levels
    with LogIfFailure(feature="leveling.handle_member_removal"):
        await leveling.handle_member_removal(member)

    # Log the removal
    with LogIfFailure(feature="action_logging.log_member_removal"):
        await action_logging.log_member_removal(member.guild, member)

@bot.event
async def on_guild_join(guild: nextcord.Guild) -> None:
    """
    Handles guild join events.

    :param guild: The guild that was joined.
    :type guild: nextcord.Guild
    :return: None
    :rtype: None
    """
    await handle_server_join(guild)

@bot.event
async def on_guild_remove(guild: nextcord.Guild) -> None:
    """
    Handles guild removal events.

    :param guild: The guild that was removed.
    :type guild: nextcord.Guild
    :return: None
    :rtype: None
    """
    await handle_server_remove(guild)

@bot.event
async def on_guild_channel_delete(channel: nextcord.abc.GuildChannel) -> None:
    """
    Handles guild channel deletion events.

    :param channel: The channel that was deleted.
    :type channel: nextcord.abc.GuildChannel
    :return: None
    :rtype: None
    """
    stored_messages.remove_messages_from_channel(channel.id)
    Server(channel.guild.id).managed_messages.delete_all_matching(channel_id = channel.id)

@bot.event
async def on_voice_state_update(member: nextcord.Member, before: nextcord.VoiceState, after: nextcord.VoiceState) -> None:
    """
    Handles voice state update events.

    :param member: The member whose voice state was updated.
    :type member: nextcord.Member
    :param before: The voice state before the update.
    :type before: nextcord.VoiceState
    :param after: The voice state after the update.
    :type after: nextcord.VoiceState
    :return: None
    :rtype: None
    """
    # Trigger join to create vc update
    await join_to_create_vcs.run_join_to_create_vc_member_update(member, before, after)

@bot.event
async def on_raw_reaction_add(payload: nextcord.RawReactionActionEvent):
    await reaction_roles.run_raw_reaction_add(payload, bot)

# RUN BOT ==============================================================================================================================================================================
def run() -> None:
    """
    Runs the bot.

    :return: None
    :rtype: None
    """

    # Get token
    token = os.environ['DISCORD_AUTH_TOKEN']
    logging.info(f"Running bot with token: {token[:5]}*******...")

    try:
        bot.run(token)
    except nextcord.errors.LoginFailure:
        logging.critical("FATAL: Invalid token. Check your token and try again.")

if __name__ == "__main__":
    raise Exception("This file is not intended to be run directly. Please run the main.py file instead.")