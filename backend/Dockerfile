FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (build-essential needed for compiling C-extensions in some python packages)
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

# Copy root requirements file directly into /app
COPY requirements.txt .

# Install Python requirements cleanly
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend sub-folder specifically
COPY backend /app/backend

# Set Python path so `import backend.X` works perfectly naturally
ENV PYTHONPATH=/app

EXPOSE 8000

# Fire up FastAPI on 0.0.0.0 to securely map it out of the container
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
