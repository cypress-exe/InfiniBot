import socket
import time
import subprocess
import os

# Functions
def is_connected():
    try:
        host = socket.gethostbyname("google.com")
        s = socket.create_connection((host, 80), 2)
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
        print("NO INTERNET!!! Retrying in 2 seconds...")
        time.sleep(2)
    

# Run the bot
print("Starting up InfiniBot...")
file = f"{os.getcwd()}\\InfiniBot.py"

# Open a new command prompt window and run a command in it
subprocess.Popen(['cmd.exe', '/c', 'start', 'cmd.exe', '/k', 'python', file])
        