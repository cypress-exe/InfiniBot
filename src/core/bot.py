import asyncio
import logging
import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands
import os
import time

from components import ui_components, utils
import config.global_settings as global_settings
from config.server import Server
from config.messages import cached_messages, stored_messages
from core import log_manager
from core.api_connections_manager import start_all_api_connections
from core.emoji_manager import cache_application_emojis
from core.log_manager import LogIfFailure
from core.shard_manager import log_and_store_shard_distribution
from core.server_join_and_leave_manager import handle_server_join, handle_server_remove
from core.scheduling import start_scheduler, stop_scheduler
from core.shard_manager import calculate_shard_count
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
import humanfriendly

startup_time = None

# INIT BOT ==============================================================================================================================================================
intents = nextcord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.reactions = True


# Get shard count
shard_count = calculate_shard_count()

bot = commands.AutoShardedBot(intents = intents, 
                            allowed_mentions = nextcord.AllowedMentions(everyone = True), 
                            help_command=None,
                            max_messages=1000,
                            chunk_guilds_at_startup=True,
                            guild_ready_timeout=5,  # 5 second timeout for guilds to be ready (default is 2 seconds)
                            shard_count=shard_count)

def get_bot() -> commands.AutoShardedBot: return bot

connected_shards = set()
post_shards_connected_called = False

@bot.event
async def on_shard_connect(shard_id: int):
    connected_shards.add(shard_id)
    logging.info(f"Shard {shard_id} connected.")

    if len(connected_shards) == bot.shard_count:
        logging.info("All shards are connected.")
        await post_shards_connected()

@bot.event
async def on_shard_disconnect(shard_id: int):
    if shard_id in connected_shards:
        connected_shards.remove(shard_id)
        logging.info(f"Shard {shard_id} disconnected.")
    else:
        logging.warning(f"Shard {shard_id} was not in the connected shards list.")

async def post_shards_connected():
    """
    Called once all shards are started (not necessarily ready with all info cached)

    :return: None
    :rtype: None
    """
    global post_shards_connected_called
    if post_shards_connected_called:
        return
    post_shards_connected_called = True

    # Wait a second
    await asyncio.sleep(1)

    # Update bot ID
    global_settings.update_bot_id(bot)

    # Start API connections
    start_all_api_connections()

    # Update shard distribution
    log_and_store_shard_distribution(bot)

@bot.event
async def on_ready() -> None: # Bot load
    """
    This function is triggered when the bot becomes ready and all shards are ready.
    It waits for the bot to be fully ready, logs the bot's username, sets bot load status,
    starts the scheduler, and optionally logs which guilds are on which shard.

    :return: None
    :rtype: None
    """
    global startup_time
    
    await bot.wait_until_ready()
    logging.info(f"============================== Logged in as: {bot.user.name} with all shards ready. ==============================")
    logging.info(f"Bot is running with {bot.shard_count} shards across {len(bot.guilds)} guilds.")

    # Initialize core systems
    global_settings.set_bot_load_status(True)
    start_scheduler()

    # Initialize the bot's view cache
    init_views(bot)

    # Initialize the bot's emoji cache
    await cache_application_emojis(bot)

    # Print detailed guild info only in debug mode
    if logging.getLevelName(logging.getLogger().getEffectiveLevel()) == "DEBUG":
      for guild in bot.guilds:
          shard_id = guild.shard_id
          logging.debug(f"Guild: {guild.name} (ID: {guild.id}) is on shard {shard_id}")

    # Check if the bot needs to notify on startup
    async def send_startup_notification():
        """
        Sends a startup notification to the specified channel if enabled in the global settings.
        
        :return: None
        :rtype: None
        """
        
        if global_settings.get_configs()['notify-on-startup']['enabled']:
            logging.info("Bot startup notification is enabled. Sending notification to channel...")
            
            # Find channel
            channel_id = global_settings.get_configs()['notify-on-startup']['channel-id']
            if channel_id is None or channel_id == 0:
                logging.warning("No channel ID specified for startup notification. Skipping notification.")
                return

            channel = await utils.get_channel(channel_id, bot=bot)
            if not channel:
                logging.warning(f"Channel with ID {channel_id} not found. Skipping startup notification.")
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
    await send_startup_notification()

    # Log total startup time
    total_startup_time = time.time() - startup_time
    formatted_time = humanfriendly.format_timespan(round(total_startup_time))
    logging.info(f"🚀 STARTUP COMPLETE: Total time {formatted_time} for {len(bot.guilds)} guilds ({len(bot.guilds)/total_startup_time:.1f} guilds/sec)")


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

        # Check if all shards are loaded
        if len(shards_loaded) == bot.shard_count:
            logging.info(f"All {bot.shard_count} shards are loaded.")

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

# CUSTOM DECORATORS ============================================================================================================================================================
if global_settings.get_environment_type().upper() == "PROD":
    def dev_only_slash_command(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
else:
    dev_only_slash_command = bot.slash_command

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

# Test Commands (ONLY AVAILABLE IN DEV BUILD)
@dev_only_slash_command(name="test", description="A test command for InfiniBot. NOT INCLUDED IN PRODUCTION BUILD.")
async def test(interaction: Interaction):
    # ============================================= <VARIABLES> ==============================================
    DEFER_INTERACTION = True # Provides extra time to run code before returning a response.
    SEND_DEFAULT_EMBED = True # Sends an generic embed response to indicate the command was run successfully.
    # ============================================= </VARIABLES> =============================================
    async def test_items(interaction: Interaction):
        async def send(**kwargs):
            """
            A helper function to send a message in the test command.
            """
            if interaction.response.is_done():
                await interaction.followup.send(**kwargs)
            else:
                await interaction.response.send_message(**kwargs)
    # ======================================= <INSERT TEST CODE HERE> =======================================

        # from features.test import run_test_command
        # await run_test_command(interaction)

    # ======================================= </INSERT TEST CODE HERE> =======================================
        pass

    logging.info(f"Test command invoked by {interaction.user.name} ({interaction.user.id}) in guild {interaction.guild.name} ({interaction.guild.id})")
    logging.info(f"Running test command with DEFER_INTERACTION={DEFER_INTERACTION} and SEND_DEFAULT_EMBED={SEND_DEFAULT_EMBED}")
    if DEFER_INTERACTION: await interaction.response.defer(ephemeral=True)
    await test_items(interaction)

    if SEND_DEFAULT_EMBED:
        embed = nextcord.Embed(title="✅  Test Command  ✅", description="This is a test command.", color=nextcord.Color.blue())
        embed.add_field(
            name="What is this?", 
            value="This command is used for testing purposes. It either does nothing, \
            or maybe runs an operation behind the scenes for testing.", 
            inline=False
            )
        embed.set_footer(text="This command will NOT exist in production.")
        embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)
        
        try:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except nextcord.InteractionResponded:
            # If the response has already been sent, follow up instead
            try:
                await interaction.followup.send(embed=embed, ephemeral=True)
            except Exception as e:
                logging.warning(f"Error sending followup message: {e}")

    logging.info(f"Test command completed successfully.")

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
    if message.author == None: return
    
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
            stored_messages.store_message_in_db(message)

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
    # Skip DM messages (guild_id will be None)
    if payload.guild_id is None:
        return

    edited_message = None
    try:
        # Find guild and channel
        channel = await utils.get_channel(payload.channel_id, bot=bot)
        if channel is None: 
            return

        guild = channel.guild
        if guild is None or not guild.me: 
            return
        
        if not guild.chunked:
            await guild.chunk()
        
        # If we have it, grab the original message
        original_message = payload.cached_message
        if original_message is None:
            # Find db stored message
            original_message = stored_messages.get_message_from_db(payload.message_id)
        
        # Find the message
        edited_message = await utils.get_message(channel, payload.message_id)
        if edited_message is None:
            return
        
        # Update the message's cache
        with LogIfFailure(feature="cached_messages.remove_cached_message & cached_messages.cache_message"):
            cached_messages.remove_cached_message(edited_message.id, channel.id)
            cached_messages.cache_message(edited_message)

        # Punish profanity (if any)
        with LogIfFailure(feature="moderation.check_and_trigger_profanity_moderation_for_message"):
            await moderation.check_and_trigger_profanity_moderation_for_message(bot, Server(guild.id), edited_message)
                
        # Log the message
        with LogIfFailure(feature="action_logging.log_raw_message_edit"):
            await action_logging.log_raw_message_edit(guild, original_message, edited_message)

        # Add the edited message to the database
        with LogIfFailure(feature="stored_messages.store_message_in_db(edited_message)"):
            if utils.feature_is_active(guild_id=guild.id, feature="logging"):
                stored_messages.store_message_in_db(edited_message)

    finally:
        # Update the message in the database
        with LogIfFailure(feature="stored_messages.remove_message_from_db"):
            if utils.feature_is_active(guild_id=payload.guild_id, feature="logging"):
                stored_messages.remove_message_from_db(payload.message_id)

@bot.event
async def on_raw_message_delete(payload: nextcord.RawMessageDeleteEvent) -> None:
    """
    Handles raw message delete events.

    :param payload: The raw message delete event.
    :type payload: nextcord.RawMessageDeleteEvent
    :return: None
    :rtype: None
    """
    # Skip DM messages (guild_id will be None)
    if payload.guild_id is None:
        return
    
    # Create server instance for feature checks
    server = Server(payload.guild_id)
    
    # Check if guild/channel are needed for logging
    if utils.feature_is_active(server=server, feature = "logging"):
        try:
            # Find guild and channel
            guild = bot.get_guild(payload.guild_id)
            if guild is None: 
                return

            channel = await utils.get_channel(payload.channel_id, bot=bot)
            if channel is None: 
                return

            if not guild.chunked:
                await guild.chunk()

            message = payload.cached_message

            if message is None:
                # Find db cached message
                message = stored_messages.get_message_from_db(payload.message_id)
                if message is not None:
                    # Actual values are important instead of object approximations, so replace them
                    message.guild = guild
                    message.channel = channel
                    # Some additional info needs to be fetched
                    await message.fetch("author")

            # Log the message
            with LogIfFailure(feature="action_logging.log_raw_message_delete"):
                await action_logging.log_raw_message_delete(bot, guild, channel, message, payload.message_id)

        finally:
            # Update the message in the database
            with LogIfFailure(feature="stored_messages.remove_message_from_db"):
                stored_messages.remove_message_from_db(payload.message_id)

    # Remove managed message
    with LogIfFailure(feature="managed_messages.delete"):
        server.managed_messages.delete(payload.message_id, fail_silently=True)

    # Remove the message if we're storing it (always do this regardless of logging setting)
    with LogIfFailure(feature="cached_messages.remove_cached_message"):
        cached_messages.remove_cached_message(payload.message_id, payload.channel_id)

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
    logging.info(f"Channel {channel.name} (ID: {channel.id}) was deleted in guild {channel.guild.name} (ID: {channel.guild.id}).")

    cached_messages.remove_cached_messages_from_channel(channel.id)
    stored_messages.remove_db_messages_from_channel(channel.id)
    
    server = Server(channel.guild.id)
    server.managed_messages.delete_all_matching(channel_id=channel.id)
    if channel.id in server.join_to_create_active_vcs:
        server.join_to_create_active_vcs.delete(channel.id)


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
    global startup_time

    # Get token
    token = os.environ['DISCORD_AUTH_TOKEN']
    logging.info(f"Running bot with token: {token[:5]}*******...")

    logging.info(f"Running in {global_settings.get_environment_type()} mode.")
    startup_time = time.time()

    try:
        bot.run(token)
    except nextcord.errors.LoginFailure:
        logging.critical("FATAL: Invalid token. Check your token and try again.")

if __name__ == "__main__":
    raise Exception("This file is not intended to be run directly. Please run the main.py file instead.")