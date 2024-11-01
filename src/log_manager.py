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
    test_folder_path = os.path.abspath(test_folder_path)

    # Remove all existing handlers to avoid conflicts
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Set up file handler
    log_file_path = os.path.join(test_folder_path, "logfile.log")
    file_handler = logging.FileHandler(log_file_path)
    formatter = logging.Formatter("{asctime} - {levelname} - {message}", style="{", datefmt="%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(formatter)
    logging.root.addHandler(file_handler)

    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logging.root.addHandler(console_handler)

    # Set the logging level
    logging.root.setLevel(logging.INFO)

    logging.info("Created logging folder and logging file")
    print(f"Created folder: {test_folder_path}")

def change_logging_level(level):
    if level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        raise ValueError("Invalid logging level")
    
    if level == "DEBUG":
        logging.getLogger().setLevel(logging.DEBUG)
        logging.info("Changed logging level to DEBUG")

    elif level == "INFO":
        logging.getLogger().setLevel(logging.INFO)
        logging.info("Changed logging level to INFO")

    elif level == "WARNING":
        logging.getLogger().setLevel(logging.WARNING)
        logging.warning("Changed logging level to WARNING")

    elif level == "ERROR":
        logging.getLogger().setLevel(logging.ERROR)
        logging.error("Changed logging level to ERROR")

    elif level == "CRITICAL":
        logging.getLogger().setLevel(logging.CRITICAL)
        logging.critical("Changed logging level to CRITICAL")