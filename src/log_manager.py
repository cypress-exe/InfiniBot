import logging
import os
import shutil
import datetime

def create_logging_folder():
    if not os.path.exists("./generated/logs"):
        os.makedirs("./generated/logs")

    date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    test_folder_path = f"./generated/logs/{date}"
    os.makedirs(test_folder_path)

    # Ensure no more than 10 files exist
    if len(os.listdir("./generated/logs")) > 10:
        shutil.rmtree(f"./generated/logs/{os.listdir('./generated/logs')[0]}")

    return test_folder_path


def setup_logging():
    test_folder_path = create_logging_folder()

    logging.basicConfig(filename = f"{test_folder_path}/logfile.log", level = logging.INFO,
                        format = "{asctime} - {levelname} - {message}", style = "{", datefmt="%Y-%m-%d %H:%M:%S")
    logging.debug("Created logging folder and logging file")

def change_logging_level(level):
    if level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        raise ValueError("Invalid logging level")
    
    if level == "DEBUG":
        logging.getLogger().setLevel(logging.DEBUG)
    elif level == "INFO":
        logging.getLogger().setLevel(logging.INFO)
    elif level == "WARNING":
        logging.getLogger().setLevel(logging.WARNING)
    elif level == "ERROR":
        logging.getLogger().setLevel(logging.ERROR)
    elif level == "CRITICAL":
        logging.getLogger().setLevel(logging.CRITICAL)

    logging.getLogger().setLevel(level)