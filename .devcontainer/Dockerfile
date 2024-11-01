# Dockerfile
# Use an official lightweight Python image suitable for Raspberry Pi (arm architecture)
FROM arm64v8/python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Optionally upgrade pip
RUN pip install --upgrade pip

# Copy the bot code into the container
COPY . /app

# Install the required Python packages (from requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# Start the bot
CMD ["python", "bot.py"]
