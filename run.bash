#!/bin/bash

# Check if "-d" flag is passed
deamonted_string=""
for arg in "$@"; do
  if [ "$arg" == "-d" ]; then
    deamonted_string="-d"
    break
  fi
done

# Run the Docker container with optional detached_string mode
docker-compose -f ./.devcontainer/docker-compose.yml up ${deamonted_string}