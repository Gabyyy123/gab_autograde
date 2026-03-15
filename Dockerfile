# 1. Use an official Python base image
FROM python:3.13-slim

# 2. Set environment variables to keep Python from buffering and creating .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set the working directory inside the container
WORKDIR /app

# 4. Install SYSTEM dependencies (This is the most important part!)
# We are installing Tesseract OCR directly into the container's OS.
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && apt-get clean

# 5. Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of your project code into the container
COPY . /app/

# Give the script permission to run
RUN chmod +x /app/start.sh

# Run the script when the container starts
CMD ["/app/start.sh"]