#!/bin/bash

# Stop (Delete) previous container
./remove_container.bash

# Build new container WITH CACHE
./build.bash -use-cache

# Run new container
./run.bash