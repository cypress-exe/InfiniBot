from contextlib import ContextDecorator
import datetime
import logging
import os
import sys
import time
import uuid

from config.global_settings import get_configs

base_path = "./generated/logs/"

def update_base_path(new_path: str) -> None:
    """
    Updates the base path for JSON files.

    :param new_path: The new base path.
    :type new_path: str
    :return: None
    :rtype: None
    """
    global base_path
    base_path = new_path

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
    Creates a new log file name in the base_path directory with the current date and time as its name.

    This function returns a name to a new log file in the base_path directory with the current date and time as its name.
    It is used to generate a new log file every time the bot is restarted.

    :param: None
    :return: None
    :type: None
    :rtype: None
    """
    if not os.path.exists(base_path):
        os.makedirs(base_path)

    # Ensure no more than max-logs-to-keep files exist
    max_logs_to_keep = get_configs()["logging"]["max-logs-to-keep"]
    while (len(os.listdir(base_path)) + 1) > max_logs_to_keep:
        logs_in_order = os.listdir(base_path)
        logs_in_order.sort()
        os.remove(os.path.join(base_path, logs_in_order[0]))
    
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
    logfile_path = os.path.join(base_path, logfile_name)
    logfile_path = os.path.abspath(logfile_path)

    # Remove all existing handlers to avoid conflicts
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Custom formatter class to handle microseconds
    class CustomFormatter(logging.Formatter):
        def formatTime(self, record, datefmt=None):
            ct = self.converter(record.created)
            if datefmt:
                # Create datetime object with microseconds
                dt = datetime.datetime.fromtimestamp(record.created)
                # Get the formatted string and truncate microseconds to 3 digits (milliseconds)
                s = dt.strftime(datefmt)
                # Replace the 6-digit microseconds with 3-digit milliseconds
                if '.%f' in datefmt:
                    microseconds = dt.microsecond
                    milliseconds = microseconds // 1000  # Convert to milliseconds
                    s = s.replace(f"{microseconds:06d}", f"{milliseconds:03d}")
            else:
                t = time.strftime("%Y-%m-%d %H:%M:%S", ct)
                s = "%s.%03d" % (t, record.msecs)
            return s

    # Set up file handler
    file_handler = logging.FileHandler(logfile_path)
    formatter = CustomFormatter(
        "{asctime} - {levelname} - {funcName} - {message}", 
        style="{", 
        datefmt=r"%Y-%m-%d %H:%M:%S.%f"
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