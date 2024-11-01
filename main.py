import socket
import time
import os
import shutil
import sys

from src.log_manager import setup_logging, change_logging_level
from src.file_manager import JSONFile
import src.bot as bot

# Functions
def create_environment():
  def create_folder(folder_path):
    if not os.path.exists(folder_path):
      os.makedirs(folder_path)
      print("Created folder: " + folder_path)
  
  def copy_file(source_path, destination_path):
    if not os.path.exists(destination_path):
      shutil.copy(source_path, destination_path)
      print("Copied file: " + source_path + " to " + destination_path)

  def get_token():
    # Check token
    print("Checking token...")
    if not os.path.exists("generated/configure/TOKEN.json"):
      print("Token not found in generated/configure/TOKEN.txt. Please configure your token.")
      print("Please enter discord token (SKIP to skip token configuration):")
      discord_token = input()

      if discord_token.lower() == "skip":
        print("Skipping token configuration.")
        return

      print("Please enter topgg token (leave blank to skip):")
      topgg_token = input()
      if topgg_token == "": topgg_token = "NONE"
      
      JSONFile("TOKEN").add_variable("discord_auth_token", discord_token)
      JSONFile("TOKEN").add_variable("topgg_auth_token", topgg_token)

    else:
      print("Token found! Continuing...")
  
  create_folder("generated")
  create_folder("generated/files")
  create_folder("generated/backups")
  create_folder("generated/configure")
    
  copy_file("defaults/default_profane_words.txt", "generated/configure/default_profane_words.txt")
  copy_file("defaults/special_channel_ids.json", "generated/configure/special_channel_ids.json")

  get_token()

  print("To modify defaults, edit settings file in generated/configure")
  
def configure_logging():
  setup_logging()

  # Change logging level depending on args
  if "--debug" in sys.argv:
    change_logging_level("DEBUG")
    print(">> Launching in debug mode.")

  elif "--info" in sys.argv:
    change_logging_level("INFO")
    print(">> Launching in info mode.")

  elif "--warning" in sys.argv:
    change_logging_level("WARNING")
    print(">> Launching in warning mode.")

  elif "--error" in sys.argv:
    change_logging_level("ERROR")
    print(">> Launching in error mode.")

  elif "--critical" in sys.argv:
    change_logging_level("CRITICAL")
    print(">> Launching in critical mode.")

  else:
    change_logging_level("INFO")
    print(">> Launching in default mode (INFO).")

def check_internet_connection():
  def is_connected():
    try:
      host = socket.gethostbyname("google.com")
      s = socket.create_connection((host, 80), timeout = 2)
      s.close()
      return True
    except:
      pass
    return False


  # Get Internet
  while True:
    if is_connected():
      break
    else:
      print("Fatal Error: No Connection. Retrying in 2 seconds...")
      time.sleep(2)


if __name__ == "__main__":
  print("Creating Environment...")
  create_environment()
  print("Environment created!")

  print("Initializing Logging...")
  configure_logging()
  print("Logging initialized!")

  print("Checking Internet Connection...")
  check_internet_connection()
  print("Connection aquired!")

  print("Starting InfiniBot...")
  bot.run()