# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install ffmpeg and system dependencies
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Expose port (optional)
EXPOSE 10000

# Start the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
