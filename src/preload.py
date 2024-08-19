import socket
import time
import subprocess
import os
import platform
import shutil

# Functions
def create_environment():
  def create_folder(folder_path):
    if not os.path.exists(folder_path):
      os.makedirs(folder_path)
      print("Created folder: " + folder_path)
  
  def copy_file(source_path, destination_path):
    if not os.path.exists(destination_path):
      shutil.copy(source_path, destination_path)
      print("Copied file: " + source_path + " to " + destination_path)
  
  create_folder("generated")
  create_folder("generated/files")
  create_folder("generated/backups")
  create_folder("generated/configure")
  
  # Check token
  print("Checking token...")
  if not os.path.exists("generated/configure/TOKEN.txt"):
    print("Token not found in generated/configure/TOKEN.txt. Please configure your token.")
    print("Please enter discord token:")
    discord_token = input()
    print("Please enter topgg token (leave blank if nonexistent):")
    topgg_token = input()
    if topgg_token == "": topgg_token = "NONE"
    
    with open("generated/configure/TOKEN.txt", "w") as f:
      f.write(f"{discord_token}\n{topgg_token}")
    print("Token saved!")
  else:
    print("Token found! Continuing...")
    
  copy_file("defaults/default_profane_words.txt", "generated/configure/default_profane_words.txt")
  copy_file("defaults/special_channel_ids.json", "generated/configure/special_channel_ids.json")
  
  print("To modify defaults, edit the files in generated/configure")
  
  

def check_internet_connection():
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
    

def start_infinibot_in_new_terminal():
  if platform.system() == "Windows":
      # Dev server
      infinibot_code_path = os.path.join(os.getcwd(), "src/bot.py")
      
      # Open a new command prompt window and run a command in it
      subprocess.Popen(['cmd.exe', '/c', 'start', 'cmd.exe', '/k', 'python', infinibot_code_path])

  else:
      # OS not supported
      print("OS NOT SUPPORTED!!!")
      quit()

def main():
  print("Checking Internet Connection...")
  check_internet_connection()
  print("Connection aquired!")
  
  print("Creating Environment...")
  create_environment()
  print("Environment created!")
  
  print("Starting InfiniBot...")
  start_infinibot_in_new_terminal()
  print("InfiniBot Started! Quitting...")
  quit()