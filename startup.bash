#!/bin/bash

# Used for production server startup

# Pull latest changes from git repository
git pull

# Stop (Delete) previous container
bash ./remove_container.bash

# Build new image
bash ./build.bash --use-cache

# Run new container
bash ./run.bash -d