from contextlib import ContextDecorator
import datetime
import logging
import os
import re
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


def organize_log_files() -> list:
    """
    Organizes log files into date-based folder structure and removes old files.
    
    Creates a folder structure like:
    - logs/2025-06-27/logfile-2025-06-27-14-30-15.log
    - logs/2025-06-28/logfile-2025-06-28-09-15-30.log
    
    Also moves any existing log files in the root directory to their appropriate folders.
    Removes folders (and their contents) older than the configured number of days.
    
    :return: List of messages describing what actions were taken
    :rtype: list
    """
    messages = []
    
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    
    max_days_to_keep = get_configs()["logging.max-logs-days-to-keep"]
    cutoff_time = time.time() - (max_days_to_keep * 24 * 60 * 60)  # Convert days to seconds
    
    # First, reorganize any loose .log files in the root directory
    for filename in os.listdir(base_path):
        filepath = os.path.join(base_path, filename)
        
        # Skip if it's a directory
        if os.path.isdir(filepath):
            continue
            
        # Only process .log files
        if not filename.endswith('.log'):
            continue
            
        # Extract date from filename (format: logfile-YYYY-MM-DD-HH-MM-SS.log)
        try:
            # Remove 'logfile-' prefix and '.log' suffix, then extract date part
            date_part = filename.replace('logfile-', '').replace('.log', '')
            # Split by '-' and take first 3 parts (YYYY-MM-DD)
            date_components = date_part.split('-')[:3]
            date_folder = '-'.join(date_components)  # YYYY-MM-DD
            
            # Create the date folder if it doesn't exist
            date_folder_path = os.path.join(base_path, date_folder)
            if not os.path.exists(date_folder_path):
                os.makedirs(date_folder_path)
                
            # Move the file to the date folder
            new_filepath = os.path.join(date_folder_path, filename)
            os.rename(filepath, new_filepath)
            messages.append(f"Reorganized log file: moved {filename} to {date_folder}/")
            
        except (ValueError, IndexError) as e:
            # If we can't parse the date from filename, leave it in root and log warning
            messages.append(f"Could not parse date from log filename '{filename}', leaving in root directory: {e}")
    
    # Now clean up old date folders
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        
        # Only process directories that look like dates (YYYY-MM-DD format)
        if not os.path.isdir(item_path):
            continue
            
        try:
            # Parse the folder name as a date
            folder_date = datetime.datetime.strptime(item, "%Y-%m-%d")
            folder_timestamp = folder_date.timestamp()
            
            # If the folder is older than cutoff, remove it entirely
            if folder_timestamp < cutoff_time:
                import shutil
                shutil.rmtree(item_path)
                messages.append(f"Removed old log folder: {item}")
                
        except ValueError:
            # If folder name doesn't match date format, skip it
            messages.append(f"Found non-date folder in logs directory: {item}")
    
    return messages


def generate_logging_file_name() -> tuple:
    """
    Creates a new log file name in the base_path directory with the current date and time as its name.

    This function returns a name to a new log file in the base_path directory with the current date and time as its name.
    It is used to generate a new log file every time the bot is restarted. It also organizes existing log files
    into date-based folders and removes old files.

    :param: None
    :return: Tuple containing (full path to the new log file, list of organization messages)
    :rtype: tuple
    """
    # Organize existing log files and clean up old ones
    organization_messages = organize_log_files()
    
    # Generate the new log file name and path
    date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    new_logfile_name = f"logfile-{date}.log"
    
    # Create today's folder
    today_folder = datetime.datetime.now().strftime("%Y-%m-%d")
    today_folder_path = os.path.join(base_path, today_folder)
    
    if not os.path.exists(today_folder_path):
        os.makedirs(today_folder_path)
    
    # Return the full path to the new log file and organization messages
    return os.path.join(today_folder_path, new_logfile_name), organization_messages

def setup_logging(level: int = logging.INFO) -> None:
    """
    Set up the logging handlers and logging level.

    :param level: The logging level to set, defaults to logging.INFO
    :type level: int, optional
    :return: None
    :rtype: None
    """
    # Create logging folder and get the full path to the new log file
    logfile_path, organization_messages = generate_logging_file_name()
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
    
    # Now log all the organization messages that were collected before logging was set up
    for message in organization_messages:
        if "Could not parse" in message or "Found non-date folder" in message:
            logging.warning(message)
        else:
            logging.info(message)

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