FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for ML packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the Hugging Face models so they don't download on every request
# This makes cold starts much faster on Serverless platforms
RUN python -c "from sentence_transformers import CrossEncoder, SentenceTransformer; \
    SentenceTransformer('all-MiniLM-L6-v2'); \
    CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

# Copy the rest of the application
COPY . .

# Create the documents directory just in case it's not checked into git
RUN mkdir -p documents

# Expose port 8000 for FastAPI
EXPOSE 8000

# Command to run the application using Uvicorn
CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
