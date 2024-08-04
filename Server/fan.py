#!/usr/bin/python
import sys
import time
from gpiozero import LED
import platform

MAX_TEMPERATURE = 60
MIN_TEMPERATURE = 52

fan = LED(21)

def cpu_temp():
  with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
    return float(f.read())/1000

def main():
  # start fan at the beginning
  is_on = True
  fan.on()
  print("FAN ON")

  while True:
    temp = cpu_temp()
    print(temp)

    if is_on:
      if temp < MIN_TEMPERATURE:
        print("FAN OFF")
        fan.off()
        is_on = False
    else:
      if temp > MAX_TEMPERATURE:
        print("FAN ON")
        fan.on()
        is_on = True

    time.sleep(2.0)

if __name__ == "__main__" and platform.system() == "Linux":
  main()










