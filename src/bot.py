from nextcord import AuditLogAction, Interaction, SlashOption
from nextcord.ext import commands
import nextcord
import logging

from file_manager import JSONFile

from dashboard import run_dashboard_command
from global_settings import shards_loaded, bot_loaded


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
    print(f"Logged in as: {bot.user.name} with all shards ready.")
    logging.info(f"Logged in as: {bot.user.name} with all shards ready.")

    bot_loaded = True

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
    print(f"Shard {shard_id} is ready.")

    shards_loaded.append(shard_id)

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


# RUN BOT ==============================================================================================================================================================================
def run():
  # Get token
  token = JSONFile("TOKEN")["discord_auth_token"]
  logging.info(f"Running bot with token: {token[:5]}*******...")
  bot.run(token)


if __name__ == "__main__":
  raise Exception("This file is not intended to be run directly. Please run the main.py file instead.")