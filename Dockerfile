FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download models to bake them into the image
# This prevents downloading on every container start/scale-up
RUN python -c "from sentence_transformers import CrossEncoder, SentenceTransformer; \
    SentenceTransformer('all-MiniLM-L6-v2'); \
    CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

# Copy application source
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p documents && chmod 777 documents

# Expose port
EXPOSE 8000

# Environment defaults
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Start command
CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
