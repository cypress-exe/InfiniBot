import logging
import os
import shutil
import socket
import time

from config.global_settings import get_configs
from core.log_manager import setup_logging, change_logging_level

# Functions
def create_environment():
    """
    Creates the environment required for InfiniBot to run.
    """
    def create_folder(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        logging.info(f"Created folder: {folder_path}")
    
    def copy_file(source_path, destination_path):
        if not os.path.exists(destination_path):
            shutil.copy(source_path, destination_path)
            logging.info(f"Copied file: {source_path} to {destination_path}")

    def get_token():
        """
        Validates that required environment variables exist
        """
        logging.info("Checking environment variables for tokens...")
        environment_vars = [
            ('DISCORD_AUTH_TOKEN', True), # Required
            ('TOPGG_AUTH_TOKEN', False)
        ]

        # Ensure existence
        missing_vars = [var[0] for var in environment_vars if not os.environ.get(var[0])]
        if missing_vars:
            error_msg = f"Some environment variables don't exist: {', '.join(missing_vars)}"
            logging.warning(error_msg)

        unset_vars = [var[0] for var in environment_vars if var[1] and os.environ.get(var[0]).lower() in ["", "none", "missing"]]
        if unset_vars:
            error_msg = "Some required environment variables are unset or missing."
            logging.critical("Missing required environment variables: " + ", ".join(unset_vars))
            logging.critical("Exiting...")

            time.sleep(0.1) # Give time for logging so that error is visible at bottom

            print("="*100)
            print(f"FATAL ERROR: {error_msg}")
            print("EXITING...")
            print("="*100)

            exit()

        logging.info("All required tokens found in environment variables! Continuing...")
    
    # Create directory structure
    create_folder("generated")
    create_folder("generated/files")
    create_folder("generated/backups")
    create_folder("generated/configure")
    
    # Copy default files
    copy_file("defaults/default_profane_words.txt", "generated/configure/default_profane_words.txt")
    copy_file("defaults/default_jokes.json", "generated/files/jokes.json")

    # Validate environment variables
    get_token()

    logging.info("To modify defaults, edit settings files in ./generated/configure")
    
def configure_logging():
    """
    Sets up the logging system for InfiniBot.

    :return: None
    :rtype: None
    """
    setup_logging()

    # Change logging level depending on configurations
    log_level = get_configs()["logging"]["log-level"]
    if log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        logging.warning("Invalid logging level in config.json. Defaulting to INFO.")
        log_level = "INFO"

    change_logging_level(log_level)

    logging.info(f"Logging level set to {log_level}")

def check_internet_connection():
    """
    Checks if the host running InfiniBot has a valid internet connection.

    :return: True if the host has a valid internet connection, False otherwise.
    :rtype: bool
    """
    def is_connected():
        """
        Checks if the host running InfiniBot has a valid internet connection.

        :param: None
        :return: True if the host has a valid internet connection, False otherwise.
        :rtype: bool
        """
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

    logging.info("Starting Database...")
    import core.db_manager as db_manager
    db_manager.init_database()
    logging.info("Database started!")

    logging.info("Starting InfiniBot...")
    import core.bot as bot
    bot.run()