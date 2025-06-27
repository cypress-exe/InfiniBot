#!/bin/bash

# Follow the logs - finds the most recent log file in date-organized folders
# Structure: ./generated/logs/YYYY-MM-DD/logfile-YYYY-MM-DD-HH-MM-SS.log
tail -f $(find ./generated/logs/ -name "*.log" -type f -printf '%T@ %p\n' | sort -n | tail -n 1 | cut -d' ' -f2-)