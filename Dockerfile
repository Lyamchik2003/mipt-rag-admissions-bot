# Quick Docker image for MAX_hackaton RAG bot
# Builds a minimal image that runs the aiomax bot.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy source code
COPY . /app

# Default command
CMD ["python", "bot_pooling.py"]
