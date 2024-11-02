#!/bin/bash

# Check if "-usecache" flag is passed
USE_CACHE=true
for arg in "$@"; do
  if [ "$arg" == "-use-cache" ]; then
    USE_CACHE=false
    break
  fi
done

# Build the Docker image with optional caching
if [ "$USE_CACHE" = true ]; then
  docker build -f ./.devcontainer/Dockerfile \
    --pull --no-cache --force-rm \
    -t infinibot:latest \
    ./
else
  docker build -f ./.devcontainer/Dockerfile \
    --pull --force-rm \
    -t infinibot:latest \
    ./
fi

# Check if the build was successful
if [ $? != 0 ]; then
  echo "ERROR: Docker build failed."
  exit 1
fi
