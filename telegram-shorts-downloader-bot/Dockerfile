# Use official slim Python image
FROM python:3.11-slim

# Install system dependencies: ffmpeg, nodejs, curl
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg nodejs curl && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# Expose port for health check
EXPOSE 10000

# Start command
CMD ["python", "bot.py"]
