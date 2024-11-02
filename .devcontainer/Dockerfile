# Base Python image
FROM mcr.microsoft.com/devcontainers/python:bullseye AS base

# Set the working directory
WORKDIR /app

# Upgrade pip version
RUN pip install --upgrade pip

# Copy the requirements and install dependencies in a separate layer
COPY requirements.txt .

# Install Python dependencies with no pip upgrade
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]