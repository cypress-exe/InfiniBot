import logging
import os
import datetime

def create_logging_folder():
    if not os.path.exists("./generated/logs"):
        os.makedirs("./generated/logs")

    date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    test_folder_path = f"./generated/logs/{date}"
    os.makedirs(test_folder_path)

    # Ensure no more than 10 files exist
    if len(os.listdir("./generated/logs")) > 10:
        os.rmdir(f"./generated/logs/{os.listdir('./generated/logs')[0]}")

    return test_folder_path


test_folder_path = create_logging_folder()

logging.basicConfig(filename = f"{test_folder_path}/logfile.log", level = logging.DEBUG,
                    format = "{asctime} - {levelname} - {message}", style = "{", datefmt="%Y-%m-%d %H:%M:%S")
logging.debug("Created logging folder and logging file")