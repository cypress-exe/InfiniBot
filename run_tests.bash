#!/bin/bash

# Check if --skip-build flag is passed
skip_build=false
for arg in "$@"; do
    if [ "$arg" == "--skip-build" ]; then
        skip_build=true
        break
    fi
done

# Rebuild if needed (unless skipped)
if [ "$skip_build" == "false" ]; then
    ./remove_container.bash
    ./build.bash --use-cache
fi

# Filter out --skip-build from arguments passed to tests
test_args=()
for arg in "$@"; do
    if [ "$arg" != "--skip-build" ]; then
        test_args+=("$arg")
    fi
done

# Run tests directly (skip entrypoint)
docker run --rm \
    --entrypoint "" \
    -v "$(pwd)/./generated:/app/generated" \
    --env-file ./.env \
    infinibot \
    python3 ./src/tests.py "${test_args[@]}"
