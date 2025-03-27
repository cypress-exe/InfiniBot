from contextlib import ContextDecorator
import datetime
import logging
import os
import shutil
import sys
import uuid

from config.global_settings import get_configs


class LogIfFailure(ContextDecorator):
    """
    A context manager to log any exceptions that occur while running the code in the context.

    :param feature: The name of the feature to log the error in, defaults to None
    :type feature: str, optional
    :param suppress: Whether to suppress the exception or not, defaults to True
    :type suppress: bool, optional
    :return: The error ID if an exception occurred, None otherwise
    :rtype: str or None
    """
    def __init__(self, feature=None, suppress=True):
        self.error_id = None
        self.feature = feature
        self.suppress = suppress

    def __enter__(self):
        # Generate a new UUID when entering the context
        self.error_id = str(uuid.uuid4())
        return self.error_id  # Return the error ID so it can be used outside the with block

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            # If an error occurs, log it and include the UUID
            logging.error(f"Error occurred {f"in feature: {self.feature}" if self.feature else ""} with ID {self.error_id}: {exc_value}", 
                          exc_info=(exc_type, exc_value, traceback))

        return self.suppress

def get_uuid_for_logging() -> str:
    """
    Generate a UUID for logging purposes.

    :return: A string representation of a UUID.
    :rtype: str
    """
    return str(uuid.uuid4())


def generate_logging_file_name() -> None:
    """
    Creates a new log file name in the generated/logs directory with the current date and time as its name.

    This function returns a name to a new log file in the generated/logs directory with the current date and time as its name.
    It is used to generate a new log file every time the bot is restarted.

    :param: None
    :return: None
    :type: None
    :rtype: None
    """
    if not os.path.exists("./generated/logs"):
        os.makedirs("./generated/logs")

    # Ensure no more than max_logs_to_keep files exist
    max_logs_to_keep = get_configs()["logging"]["max_logs_to_keep"]
    while (len(os.listdir("./generated/logs")) + 1) > max_logs_to_keep:
        logs_in_order = os.listdir("./generated/logs")
        logs_in_order.sort()
        os.remove(f"./generated/logs/{logs_in_order[0]}")
    
    date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    new_logfile_name = f"logfile-{date}.log"

    return new_logfile_name

def setup_logging(level: int = logging.INFO) -> None:
    """
    Set up the logging handlers and logging level.

    :param level: The logging level to set, defaults to logging.INFO
    :type level: int, optional
    :return: None
    :rtype: None
    """
    # Create logging folder
    logfile_name = generate_logging_file_name()
    logfile_path = os.path.join("./generated/logs", logfile_name)
    logfile_path = os.path.abspath(logfile_path)

    # Remove all existing handlers to avoid conflicts
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Set up file handler
    file_handler = logging.FileHandler(logfile_path)
    formatter = logging.Formatter(
        "{asctime} - {levelname} - {funcName} - {message}", 
        style="{", 
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    logging.root.addHandler(file_handler)

    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logging.root.addHandler(console_handler)

    # Set the logging level
    logging.root.setLevel(level)

    logging.info("Created logging file")

    # Hook up exception logging
    def exception_logger(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, Exception):
            logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        else:
            logging.critical("Critical uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = exception_logger

def change_logging_level(level: str) -> None:
    """
    Change the logging level of the root logger.

    :param level: The logging level to set. Must be one of 
                  "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL".
    :type level: str
    :return: None
    :rtype: None
    """
    if level.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        raise ValueError("Invalid logging level")
    
    logging.getLogger().setLevel(getattr(logging, level.upper()))
    logging.info(f"Changed logging level to {level.upper()}")