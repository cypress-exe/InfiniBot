#!/bin/bash

# Follow the logs
tail -f ./generated/logs/$(ls ./generated/logs/ -t | head -n 1)