import socket
import time
import os
import shutil
import sys

from log_manager import setup_logging, change_logging_level
from file_manager import JSONFile
import logging

# Functions
def create_environment():
  def create_folder(folder_path):
    os.makedirs(folder_path, exist_ok=True)
    logging.info("Created folder: " + folder_path)
  
  def copy_file(source_path, destination_path):
    if not os.path.exists(destination_path):
      shutil.copy(source_path, destination_path)
      logging.info("Copied file: " + source_path + " to " + destination_path)

  def get_token():
    # Check token
    logging.info("Checking token...")
    try:
      # Ensure token config file exists
      if not os.path.exists("generated/configure/TOKEN.json"):
        JSONFile("TOKEN").add_variable("discord_auth_token", None)
        JSONFile("TOKEN").add_variable("topgg_auth_token", None)

        raise Exception("Token config file generated in ./generated/configure/TOKEN.json. Please configure your token!!!")
      else:
        # Add default values for objects if they don't exist
        if "discord_auth_token" not in JSONFile("TOKEN"): JSONFile("TOKEN").add_variable("discord_auth_token", None)
        if "topgg_auth_token" not in JSONFile("TOKEN"): JSONFile("TOKEN").add_variable("topgg_auth_token", None)

        # Ensure token is not None
        if JSONFile("TOKEN")["discord_auth_token"] == None:
          raise Exception("Token not set!!! Please configure your token in ./generated/configure/TOKEN.json")
        else:
          logging.info("Token found! Continuing...")
    except Exception as e:
      print("FATAL ERROR: " + str(e))
      print("Exiting...")
      exit()
  
  create_folder("generated")
  create_folder("generated/files")
  create_folder("generated/backups")
  create_folder("generated/configure")
    
  copy_file("defaults/default_profane_words.txt", "generated/configure/default_profane_words.txt")

  get_token()

  logging.info("To modify defaults, edit settings file in ./generated/configure")
  
def configure_logging():
  setup_logging()

  # Change logging level depending on args
  if "--debug" in sys.argv:
    change_logging_level("DEBUG")
    logging.info(">> Launching in debug mode.")

  elif "--info" in sys.argv:
    change_logging_level("INFO")
    logging.info(">> Launching in info mode.")

  elif "--warning" in sys.argv:
    change_logging_level("WARNING")
    logging.info(">> Launching in warning mode.")

  elif "--error" in sys.argv:
    change_logging_level("ERROR")
    logging.info(">> Launching in error mode.")

  elif "--critical" in sys.argv:
    change_logging_level("CRITICAL")
    logging.info(">> Launching in critical mode.")

  else:
    change_logging_level("INFO")
    logging.info(">> Launching in default mode (INFO).")

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
      logging.info("Fatal Error: No Connection. Retrying in 2 seconds...")
      time.sleep(2)


if __name__ == "__main__":
  logging.info("Creating Environment...")
  create_environment()
  logging.info("Environment created!")

  logging.info("Initializing Logging...")
  configure_logging()
  logging.info("Logging initialized!")

  logging.info("Checking Internet Connection...")
  check_internet_connection()
  logging.info("Connection aquired!")

  logging.info("Starting InfiniBot...")
  import bot
  bot.run()