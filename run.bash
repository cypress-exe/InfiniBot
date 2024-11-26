#!/bin/bash

# Check if "-d" flag is passed
daemon_arg=""
for arg in "$@"; do
    if [ "$arg" == "-d" ]; then
        daemon_arg="-d"
        break
    fi
done

# Run the Docker container with optional detached_string mode
docker-compose -f ./.devcontainer/docker-compose.yml up ${daemon_arg}