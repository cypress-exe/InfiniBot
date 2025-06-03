#!/bin/bash

# Create environment
if [ ! -f ./.env ]; then
    echo "Creating .env file from template..."
    cp ./.devcontainer/env.template ./.env
fi

# Capture git information for the container
echo "Capturing git information..."
mkdir -p ./generated
git_info_file="./generated/build_info"

# Get git commit hash (fallback to "unknown" if git fails)
if git rev-parse HEAD >/dev/null 2>&1; then
    git_commit=$(git rev-parse HEAD)
else
    git_commit="unknown"
fi

# Get git repository URL (fallback to "unknown" if git fails)
if git config --get remote.origin.url >/dev/null 2>&1; then
    git_remote=$(git config --get remote.origin.url)
else
    git_remote="unknown"
fi

# Get current timestamp (cross-platform)
if command -v date >/dev/null 2>&1; then
    # Unix/Linux/MacOS
    build_timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")
else
    # Fallback if date command is not available
    build_timestamp="unknown"
fi

# Write build info to file
cat > "$git_info_file" << EOF
GIT_COMMIT=$git_commit
GIT_REMOTE=$git_remote
BUILD_TIMESTAMP=$build_timestamp
BUILD_FLAGS=$@
EOF

echo "Build info written to $git_info_file"

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