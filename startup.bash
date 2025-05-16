#!/bin/bash

# Used for production server startup

# Pull latest changes from git repository
git pull

# Stop (Delete) previous container
bash ./remove_container.bash

# Build new image (no cache)
bash ./build.bash

# Run new container
bash ./run.bash -d