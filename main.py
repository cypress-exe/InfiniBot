import socket
import time
import subprocess
import os
import platform

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
file = os.path.join(os.getcwd(), "InfiniBot.py")

if platform.system() == "Windows":
    # Open a new command prompt window and run a command in it
    subprocess.Popen(['cmd.exe', '/c', 'start', 'cmd.exe', '/k', 'python', file])
elif platform.system() == "Linux":
    # Open a new terminal window and run a command in it
    subprocess.run(["gnome-terminal", "--command=python " + file])
else:
    # OS not supported
    print("OS NOT SUPPORTED!!!")
    quit()