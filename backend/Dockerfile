FROM python:3.11-slim

# Set working directory to /app
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

# Copy requirements from the build context (which is the backend directory)
COPY requirements.txt .

# Install Python requirements cleanly
RUN pip install --no-cache-dir -r requirements.txt

# Copy all contents of the build context (backend/) into /app/backend
COPY . /app/backend

# Set Python path so `import backend.X` works perfectly naturally
ENV PYTHONPATH=/app

# Expose port 10000 for Render
EXPOSE 10000

# Start FastAPI using Render's PORT environment variable
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
