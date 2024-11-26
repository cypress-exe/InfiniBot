import datetime
import logging
import os
import shutil
import sys

from config.file_manager import JSONFile

def create_logging_folder():
    if not os.path.exists("./generated/logs"):
        os.makedirs("./generated/logs")

    date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    test_folder_path = f"./generated/logs/{date}"
    os.makedirs(test_folder_path)

    # Ensure no more than JSONFile("config")["max_logs_to_keep"] files exist
    while len(os.listdir("./generated/logs")) > JSONFile("config")["max_logs_to_keep"]:
        shutil.rmtree(f"./generated/logs/{os.listdir('./generated/logs')[0]}")

    return test_folder_path


def setup_logging(level=logging.INFO):
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
    logging.root.setLevel(level)

    logging.info("Created logging folder and logging file")

    # Hook up exception logging
    def exception_logger(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, Exception):
            logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        else:
            logging.critical("Critical uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = exception_logger

def change_logging_level(level:str):
    if level.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        raise ValueError("Invalid logging level")
    
    logging.getLogger().setLevel(getattr(logging, level.upper()))
    logging.info(f"Changed logging level to {level.upper()}")