import datetime
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
from features import action_logging, admin_commands, dashboard, dm_commands, moderation


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
async def on_ready():
    await bot.wait_until_ready()
    logging.info(f"Logged in as: {bot.user.name} with all shards ready.")

    global_settings.bot_loaded = True

    # Print which guilds are on which shard
    if logging.getLevelName(logging.getLogger().getEffectiveLevel()) == "DEBUG":
      for guild in bot.guilds:
          shard_id = guild.shard_id
          logging.debug(f"Guild: {guild.name} (ID: {guild.id}) is on shard {shard_id}")

    

@bot.event
async def on_shard_ready(shard_id: int):
    """
    Triggered when a specific shard becomes ready.
    Logs the readiness of each shard and performs any necessary actions.
    """
    logging.info(f"Shard {shard_id} is ready.")

    global_settings.shards_loaded.append(shard_id)

    # Optional: Perform shard-specific tasks, such as notifying a server or channel
    # Example:
    # if shard_id == 0:
    #     admin_channel = bot.get_channel(YOUR_ADMIN_CHANNEL_ID)
    #     if admin_channel:
    #         await admin_channel.send(f"Shard {shard_id} is ready.")


# SLASH COMMANDS ==============================================================================================================================================================
@bot.slash_command(name = "view", description = "Requires Infinibot Mod", dm_permission=False)
async def view(interaction: Interaction):
    pass

@bot.slash_command(name = "set", description = "Requires Infinibot Mod", dm_permission=False, guild_ids=[968872260557488158])
async def set(interaction: Interaction):
    pass

@bot.slash_command(name = "create", description = "Requires Infinibot Mod", dm_permission=False, guild_ids=[968872260557488158])
async def create(interaction: Interaction):
    pass

# COMMANDS ================================================================================================================================================================
@bot.slash_command(name = "dashboard", description = "Configure InfiniBot (Requires Infinibot Mod)", dm_permission=False)
async def dashboard_command(interaction: Interaction):
    await dashboard.run_dashboard_command(interaction)

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

# ERROR HANDLING ==============================================================================================================================================================
@bot.event
async def on_application_command_error(interaction: Interaction, error):
    """Handles errors in application commands."""
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
async def on_message(message: nextcord.Message):
    if message == None: return
      
    # DM Commands ---------------------------------------------
    if message.guild == None:
        await dm_commands.check_and_run_dm_commands(bot, message)
        await admin_commands.check_and_run_admin_commands(message)
        return

    # Moderation
    # await checkForExpiration(server)

    # Don't do anything if the message is from a bot
    if message.author.bot:
        return

    # Moderation
    message_is_bad = await moderation.check_and_run_moderation_commands(bot, message)
    
    # if not message_is_bad:
    #     # Give levels
    #     if utils.enabled.Leveling(server = server): await giveLevels(message)
    #     await admin_commands.check_and_run_admin_commands(message)


    # Continue with the Rest of the bot commands
    await bot.process_commands(message)

@bot.event
async def on_raw_message_edit(payload: nextcord.RawMessageUpdateEvent):
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
    
    # If we have it, grab the before message
    before_message = payload.cached_message
    
    # Find the message
    after_message = None
    try:
        history = await channel.history().flatten()
        for message in history:
            if history.index(message) > 500: return # Only check the last 500 messages
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
async def on_raw_message_delete(payload: nextcord.RawMessageDeleteEvent):
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
async def on_member_update(before: nextcord.Member, after: nextcord.Member):
        # Log the update
    with LogIfFailure(feature="action_logging.log_member_update"):
        await action_logging.log_member_update(before, after)
    
    # Check profanity
    if before.nick != after.nick:
        with LogIfFailure(feature="moderation.check_and_punish_nickname_for_profanity"):
            if after.nick != None: await moderation.check_and_punish_nickname_for_profanity(bot, after.guild, before, after)

@bot.event
async def on_member_remove(member: nextcord.Member):
    # Log the removal
    with LogIfFailure(feature="action_logging.log_member_removal"):
        await action_logging.log_member_removal(member.guild, member)

@bot.event
async def on_guild_channel_delete(channel: nextcord.abc.GuildChannel):
    # TODO Delete message info from channels that are deleted.
    pass

# RUN BOT ==============================================================================================================================================================================
def run():
    # Get token
    token = JSONFile("TOKEN")["discord_auth_token"]
    logging.info(f"Running bot with token: {token[:5]}*******...")
    bot.run(token)


if __name__ == "__main__":
    raise Exception("This file is not intended to be run directly. Please run the main.py file instead.")