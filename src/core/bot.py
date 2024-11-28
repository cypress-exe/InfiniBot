import datetime
import logging
import nextcord
from nextcord import AuditLogAction, Interaction, SlashOption
from nextcord.ext import commands

from components import ui_components, utils
from config.server import Server
import config.global_settings as global_settings
from config.file_manager import JSONFile
from core import log_manager
from features.admin_commands import check_and_run_admin_commands
from features.dashboard import run_dashboard_command
from features.dm_commands import check_and_run_dm_commands
from features.moderation import check_and_run_moderation_commands


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
@bot.slash_command(name = "dashboard", description = "Configure InfiniBot (Requires Infinibot Mod)", dm_permission=False)
async def dashboard(interaction: Interaction):
    await run_dashboard_command(interaction)

@bot.slash_command(name = "create_infinibot_mod_role", description = "Manually trigger InfiniBot to create the Infinibot Mod role", dm_permission=False)
async def create_infinibot_mod_role(interaction: Interaction):
    await utils.check_server_for_infinibot_mod_role(interaction)

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
        await check_and_run_dm_commands(bot, message)
        await check_and_run_admin_commands(message)
        return

    # Moderation
    # await checkForExpiration(server)

    # Don't do anything if the message is from a bot
    if message.author.bot:
        return

    # Moderation
    message_is_profane = await check_and_run_moderation_commands(bot, message)
    
    # if not message_is_profane:
    #     # Give levels
    #     if utils.enabled.Leveling(server = server): await giveLevels(message)
    #     await check_and_run_admin_commands(message)


    # Continue with the Rest of the bot commands
    await bot.process_commands(message)

# RUN BOT ==============================================================================================================================================================================
def run():
    # Get token
    token = JSONFile("TOKEN")["discord_auth_token"]
    logging.info(f"Running bot with token: {token[:5]}*******...")
    bot.run(token)


if __name__ == "__main__":
    raise Exception("This file is not intended to be run directly. Please run the main.py file instead.")