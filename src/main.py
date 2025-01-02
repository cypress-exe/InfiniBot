import logging
import os
import shutil
import socket
import time

from config.file_manager import JSONFile
from config.global_settings import get_configs
from core.log_manager import setup_logging, change_logging_level

# Functions
def create_environment():
    """
    Creates the environment required for InfiniBot to run.

    :return: None
    :rtype: None
    """
    def create_folder(folder_path):
        """
        Creates the specified folder.

        :param folder_path: The path to the folder to be created.
        :type folder_path: str
        :return: None
        :rtype: None
        """
        os.makedirs(folder_path, exist_ok=True)
        logging.info("Created folder: " + folder_path)
    
    def copy_file(source_path, destination_path):
        """
        Copies a file from the source path to the destination path if the destination path does not exist.

        :param source_path: The path to the source file to be copied.
        :type source_path: str
        :param destination_path: The path where the file should be copied.
        :type destination_path: str
        :return: None
        :rtype: None
        """

        if not os.path.exists(destination_path):
            shutil.copy(source_path, destination_path)
            logging.info("Copied file: " + source_path + " to " + destination_path)

    def get_token():
        """
        Gets the token from the user.

        :return: The token provided by the user.
        :rtype: str
        """
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
            logging.critical("FATAL ERROR: " + str(e))
            logging.critical("Exiting...")
            exit()
    
    create_folder("generated")
    create_folder("generated/files")
    create_folder("generated/backups")
    create_folder("generated/configure")
        
    copy_file("defaults/default_profane_words.txt", "generated/configure/default_profane_words.txt")

    get_token()

    logging.info("To modify defaults, edit settings file in ./generated/configure")
    
def configure_logging():
    """
    Sets up the logging system for InfiniBot.

    :return: None
    :rtype: None
    """
    setup_logging()

    # Change logging level depending on configurations
    log_level = get_configs()["logging"]["log_level"]
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