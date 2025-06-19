# Base Python image
FROM mcr.microsoft.com/devcontainers/python:3.13-bullseye AS base

# Set the working directory
WORKDIR /app

# Upgrade pip version
RUN pip install --upgrade pip

# Dependencies stage (better caching)
FROM base AS dependencies
COPY ./.devcontainer/requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM dependencies AS production

# Copy entrypoint and configure with permissions
COPY ./.devcontainer/entrypoint.sh .
RUN chmod +x entrypoint.sh

# Copy application code (done last for better cache efficiency)
COPY . .

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]