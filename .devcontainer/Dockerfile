# Base Python image
FROM mcr.microsoft.com/devcontainers/python:3.13-bullseye AS base

# Install uv (https://docs.astral.sh/uv/guides/integration/docker/)
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /bin/

# Set the working directory
WORKDIR /app

# Compile bytecode at install time, use the base image's Python,
# and put the project venv first on PATH so `python3` resolves to it
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH"

# Dependencies stage (better caching)
FROM base AS dependencies
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Production stage
FROM dependencies AS production

# Copy entrypoint and configure with permissions
COPY ./.devcontainer/entrypoint.sh .
RUN chmod +x entrypoint.sh

# Copy application code (done last for better cache efficiency)
COPY . .

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]
