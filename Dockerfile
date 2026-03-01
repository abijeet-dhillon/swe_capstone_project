# syntax=docker/dockerfile:1

FROM python:3.10-slim

# Set working directory
WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libzbar0 \
    sqlite3 \
    libsqlite3-dev \
    tesseract-ocr \
    tesseract-ocr-eng \
    git

# Upgrade pip and related tools
RUN pip install --upgrade pip setuptools wheel

# Copy dependencies
COPY requirements.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Start the API server
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]