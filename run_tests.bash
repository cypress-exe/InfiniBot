#!/bin/bash

# Rebuild if needed
./remove_container.bash
./build.bash --use-cache

# Run tests directly (skip entrypoint)
docker run --rm \
    --entrypoint "" \
    -v "$(pwd)/./generated:/app/generated" \
    --env-file ./.env \
    infinibot \
    python3 ./src/tests.py "$@"
