#!/bin/bash

# Check if "--no-cache" flag is passed
cache_string="--use-cache"
for arg in "$@"; do
  if [ "$arg" == "--no-cache" ]; then
    cache_string=""
    echo "Rebuilding container without caching..."
    break
  fi
done

# Stop (Delete) previous container
./remove_container.bash

# Build new container WITH CACHE
./build.bash ${cache_string}

# Run new container
./run.bash