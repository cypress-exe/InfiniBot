import logging
import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

from components import ui_components, utils
from config.server import Server
import config.global_settings as global_settings
from config.file_manager import JSONFile
from core import log_manager
from core.log_manager import LogIfFailure
from core.scheduling import start_scheduler, get_scheduler
from features import action_logging, admin_commands, dashboard, dm_commands, join_leave_messages, leveling, moderation, profile


# INIT BOT ==============================================================================================================================================================
intents = nextcord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.reactions = True

bot = commands.AutoShardedBot(intents = intents, 
                            allowed_mentions = nextcord.AllowedMentions(everyone = True), 
                            help_command=None)

@bot.event
async def on_ready() -> None:
    """
    This function is triggered when the bot becomes ready and all shards are ready.
    It waits for the bot to be fully ready, logs the bot's username, sets bot load status,
    starts the scheduler, and optionally logs which guilds are on which shard.

    :return: None
    :rtype: None
    """

    await bot.wait_until_ready()
    logging.info(f"============================== Logged in as: {bot.user.name} with all shards ready. ==============================")

    global_settings.set_bot_load_status(True)
    start_scheduler()

    # Print which guilds are on which shard
    if logging.getLevelName(logging.getLogger().getEffectiveLevel()) == "DEBUG":
      for guild in bot.guilds:
          shard_id = guild.shard_id
          logging.debug(f"Guild: {guild.name} (ID: {guild.id}) is on shard {shard_id}")


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
    get_scheduler().shutdown()
    logging.fatal("InfiniBot is shutting down...")

# SLASH COMMANDS ==============================================================================================================================================================
@bot.slash_command(name = "view", description = "Requires Infinibot Mod", integration_types=[nextcord.IntegrationType.guild_install])
async def view(interaction: Interaction):
    pass

@bot.slash_command(name = "set", description = "Requires Infinibot Mod", integration_types=[nextcord.IntegrationType.guild_install])
async def set(interaction: Interaction):
    pass

@bot.slash_command(name = "create", description = "Requires Infinibot Mod", integration_types=[nextcord.IntegrationType.guild_install])
async def create(interaction: Interaction):
    pass

@bot.slash_command(name = "help", description="Help with the InfiniBot.")
async def help(interaction: Interaction):
    pass

# COMMANDS ================================================================================================================================================================
@bot.slash_command(name = "dashboard", description = "Configure InfiniBot (Requires Infinibot Mod)", integration_types=[nextcord.IntegrationType.guild_install])
async def dashboard_command(interaction: Interaction):
    await dashboard.run_dashboard_command(interaction)

@bot.slash_command(name = "profile", description = "Configure Your Profile In InfiniBot", integration_types=[nextcord.IntegrationType.guild_install])
async def profile_command(interaction: Interaction):
    await profile.run_profile_command(interaction)

@create.subcommand(name = "infinibot_mod_role", description = "Manually trigger InfiniBot to create the Infinibot Mod role")
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


@view.subcommand(name = "my_strikes", description = "View your strikes")
async def my_strikes(interaction: Interaction):
    await moderation.run_my_strikes_command(interaction)

@view.subcommand(name = "member_strikes", description = "View another member's strikes. (Requires Infinibot Mod)")
async def view_member_strikes(interaction: Interaction, member: nextcord.Member):
    await moderation.run_view_member_strikes_command(interaction, member)

@set.subcommand(name = "admin_channel", description = "Use this channel to log strikes. Channel should only be viewable by admins. (Requires Infinibot Mod)")
async def set_admin_channel(interaction: Interaction):
    await moderation.run_set_admin_channel_command(interaction)

@set.subcommand(name = "log_channel", description = "Use this channel for logging. Channel should only be viewable by admins. (Requires Infinibot Mod)")
async def set_log_channel(interaction: Interaction):
    await action_logging.run_set_log_channel_command(interaction)


@bot.slash_command(name = "leaderboard", description = "Get your level and the level of everyone on the server.", integration_types=[nextcord.IntegrationType.guild_install])
async def leaderboard(interaction: Interaction):
    await leveling.run_leaderboard_command(interaction)

@view.subcommand(name = "level", description = "View your or someone else's level.")
async def view_level(interaction: Interaction, member: nextcord.Member = SlashOption(description="The member to view the level of.", required=False)):
    await leveling.run_view_level_command(interaction, member)

@set.subcommand(name = "level", description = "Set levels for any individual (Requires Infinibot Mod)")
async def set_level(interaction: Interaction, 
                    member: nextcord.Member = SlashOption(description="The member to set the level of.", required=True), 
                    level: int = SlashOption(description="The level to set.", required=True)):
    await leveling.run_set_level_command(interaction, member, level)

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
    embed = nextcord.Embed(
        title = "Woops...",
        description = f"An unexpected error occurred while executing the command. If the issue persists, please report it to the support team.",
        color = nextcord.Color.red()
    )
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

    # Moderation
    # await checkForExpiration(server) # TODO - Check for Expiration of Strikes (Do this as a midnight action)
    if message == None: return
      
    # DM Commands ---------------------------------------------
    if message.guild == None:
        with LogIfFailure(feature="dm_commands.check_and_run_dm_commands"):
            await dm_commands.check_and_run_dm_commands(bot, message)
        
        with LogIfFailure(feature="admin_commands.check_and_run_admin_commands"):
            await admin_commands.check_and_run_admin_commands(message)

        return

    # Moderation
    # await checkForExpiration(server) # TODO - Check for Expiration of Strikes (Do this as a midnight action)

    # Don't do anything if the message is from a bot
    if message.author.bot:
        return

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
    
    # If we have it, grab the before message
    before_message = payload.cached_message
    
    # Find the message
    after_message = None
    try:
        async for message in channel.history(limit=500):
            if int(message.id) == int(payload.message_id):
                after_message: nextcord.Message = message
                break
    except:
        return
    
    # Punish profanity (if any)
    with LogIfFailure(feature="moderation.check_and_trigger_profanity_moderation_for_message"):
        await moderation.check_and_trigger_profanity_moderation_for_message(bot, Server(guild.id), after_message)
            
    # Log the message
    with LogIfFailure(feature="action_logging.log_raw_message_edit"):
        await action_logging.log_raw_message_edit(guild, before_message, after_message)

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

    # Log the message
    with LogIfFailure(feature="action_logging.log_raw_message_delete"):
        await action_logging.log_raw_message_delete(bot, guild, channel, message, payload.message_id)

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
    # Trigger the welcome message
    with LogIfFailure(feature="join_leave_messages.trigger_join_message"):
        await join_leave_messages.trigger_join_message(member)

@bot.event
async def on_member_remove(member: nextcord.Member) -> None:
    """
    Handles member removal events.

    :param member: The member that was removed.
    :type member: nextcord.Member
    :return: None
    :rtype: None
    """
    # Trigger the farewell message
    with LogIfFailure(feature="join_leave_messages.trigger_leave_message"):
        await join_leave_messages.trigger_leave_message(member)

    # Remove levels
    with LogIfFailure(feature="leveling.handle_member_removal"):
        leveling.handle_member_removal(member)

    # Log the removal
    with LogIfFailure(feature="action_logging.log_member_removal"):
        await action_logging.log_member_removal(member.guild, member)

@bot.event
async def on_guild_channel_delete(channel: nextcord.abc.GuildChannel) -> None:
    """
    Handles guild channel deletion events.

    :param channel: The channel that was deleted.
    :type channel: nextcord.abc.GuildChannel
    :return: None
    :rtype: None
    """
    # TODO Delete message info from channels that are deleted.
    pass

# RUN BOT ==============================================================================================================================================================================
def run() -> None:
    """
    Runs the bot.

    :return: None
    :rtype: None
    """
    # Get token
    token = JSONFile("TOKEN")["discord_auth_token"]
    logging.info(f"Running bot with token: {token[:5]}*******...")
    bot.run(token)


if __name__ == "__main__":
    raise Exception("This file is not intended to be run directly. Please run the main.py file instead.")