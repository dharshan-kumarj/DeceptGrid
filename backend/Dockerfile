# Base image for production-grade security (slim)
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /app

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m deceptuser && chown -R deceptuser:deceptuser /app
USER deceptuser

# Expose ports (8000 for main API, 8001 for OTP Gateway if run in same container)
EXPOSE 8000
EXPOSE 8001

# Command is overridden by docker-compose for each service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
