# Base Python image
FROM mcr.microsoft.com/devcontainers/python:3.13-bullseye AS base

# Set the working directory
WORKDIR /app

# Upgrade pip version
RUN pip install --upgrade pip

# Install dependencies
COPY ./.devcontainer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint and configure with permissions
COPY ./.devcontainer/entrypoint.sh .
RUN chmod +x entrypoint.sh

# Copy application code
COPY . .

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]