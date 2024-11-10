#!/bin/bash

# Check if "--use-cache" flag is passed
cache_string="--no-cache"
for arg in "$@"; do
  if [ "$arg" == "--use-cache" ]; then
    cache_string=""
    echo "Using cached Docker image..."
    break
  fi
done

# Build the Docker image with optional caching
docker build -f ./.devcontainer/Dockerfile \
  --pull ${cache_string} --force-rm \
  -t infinibot:latest \
  ./
  
# Check if the build was successful
if [ $? != 0 ]; then
  echo "ERROR: Docker build failed."
  exit 1
fi