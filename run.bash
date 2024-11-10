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

# Check if the run was successful
if [ $? != 0 ]; then
  echo "ERROR: Docker run failed."
  exit 1
fi