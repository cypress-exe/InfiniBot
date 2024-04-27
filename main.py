import socket
import time
import subprocess
import os
import platform

# Functions
def is_connected():
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
        print("Fatal Error: No Connection. Retrying in 2 seconds...")
        time.sleep(2)
    

# Run the bot
print("Starting up InfiniBot...")

if platform.system() == "Windows":
    # This is the development server
    infinibot_code_path = os.path.join(os.getcwd(), "InfiniBot.py")
    
    # Open a new command prompt window and run a command in it
    subprocess.Popen(['cmd.exe', '/c', 'start', 'cmd.exe', '/k', 'python', infinibot_code_path])
    
elif platform.system() == "Linux":
    # This is the production server. We should set our cwd as to not introduce any surprises
    user = os.getenv("USER")
    os.chdir(f"/home/{user}/Desktop/InfiniBot")
    infinibot_code_path = os.path.join(os.getcwd(), "InfiniBot.py")
    
    # Open a new terminal window and run a command in it
    subprocess.call(["x-terminal-emulator", "-e", "python", infinibot_code_path])

    # Also in the production server, the code for the fan needs to run
    fan_code_path = os.path.join(os.getcwd(), "Server/fan.py")
    subprocess.call(["x-terminal-emulator", "-e", "python", fan_code_path])
    print("Launched Fan Script")

else:
    # OS not supported
    print("OS NOT SUPPORTED!!!")
    quit()
