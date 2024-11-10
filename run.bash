#!/bin/bash

# Check if "-d" flag is passed
detached_string=""
for arg in "$@"; do
  if [ "$arg" == "-d" ]; then
    detached_string="-d"
    break
  fi
done

# Run the Docker container with optional detached_string mode
docker-compose -f ./.devcontainer/docker-compose.yml up ${detached_string}