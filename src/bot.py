from nextcord import AuditLogAction, Interaction, SlashOption
from nextcord.ext import commands
import nextcord
import logging

from src.file_manager import JSONFile

from src.dashboard import run_dashboard_command


# INIT BOT ==============================================================================================================================================================
intents = nextcord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.reactions = True

bot = commands.Bot(intents = intents, allowed_mentions = nextcord.AllowedMentions(everyone = True), help_command=None)


@bot.event#------------------------------------------------------------------------
async def on_ready():
  await bot.wait_until_ready()
      
  print(f"Logged in as: {bot.user.name}")
  logging.info(f"Logged in as: {bot.user.name}")
  
  # TO DO: Send a message to INFINIBOT server admin channel saying the bot is loaded.


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