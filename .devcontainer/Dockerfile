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

# Test dependencies stage — branches off `dependencies` so the dev group is
# installed before the source is copied, keeping the layer cacheable
FROM dependencies AS test-dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Test stage: the production environment plus pytest. Built by run_tests.bash
# and by CI's docker-parity job (`--target test`).
FROM test-dependencies AS test
COPY . .
ENTRYPOINT []
CMD ["python3", "-m", "pytest"]

# Production stage.
#
# Kept LAST on purpose: Docker builds the final stage when no --target is given,
# so a bare `docker build` must land here and not on `test`. build.bash passes
# --target production explicitly as well; both guards are deliberate.
FROM dependencies AS production

# Copy entrypoint and configure with permissions
COPY ./.devcontainer/entrypoint.sh .
RUN chmod +x entrypoint.sh

# Copy application code (done last for better cache efficiency)
COPY . .

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]
