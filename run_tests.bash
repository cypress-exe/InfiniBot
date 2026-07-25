#!/bin/bash
# Runs the test suite inside the Docker image, matching CI's environment.
#
# For day-to-day development use `uv run pytest` on the host instead — same
# suite, no container build. This script exists to catch drift between the host
# venv and the shipped image.
#
# Extra arguments pass straight through to pytest:
#   ./run_tests.bash --skip-build -k server
#   ./run_tests.bash --skip-build -m "not slow"

set -euo pipefail

# Check if --skip-build flag is passed; everything else goes to pytest
skip_build=false
pytest_args=()
for arg in "$@"; do
    if [ "$arg" == "--skip-build" ]; then
        skip_build=true
    else
        pytest_args+=("$arg")
    fi
done

# Remove old container if it exists. Non-fatal: the test run uses `docker run
# --rm` with no name, so a leftover dev container cannot conflict with it.
./remove_container.bash || true

# Rebuild the test-stage image if needed (unless skipped)
if [ "$skip_build" == "false" ]; then
    ./build.bash --use-cache --target test
fi

# No ./generated bind mount: tests write only to pytest's tmp_path. The old
# harness mounted it, which is how ./generated/test-files ended up root-owned
# on the host after a run.
#
# --network none: the suite must never reach the real Discord API. It needs no
# network, and .env carries a valid token.
docker run --rm \
    --network none \
    --entrypoint "" \
    --env-file ./.env \
    infinibot:test \
    python3 -m pytest "${pytest_args[@]}"
