# Use an official lightweight Python image suitable for Raspberry Pi (arm architecture)
FROM mcr.microsoft.com/devcontainers/python:bullseye

# Set the working directory in the container
WORKDIR /app

# Copy the rest of the bot code into the container
COPY . .

RUN pip install --upgrade pip

# Install the required Python packages (from requirements.txt)
RUN pip install --no-cache-dir -r ./requirements.txt

ENTRYPOINT ["./entrypoint.sh"]