"""
config.py — Central configuration for the Enterprise RAG Engine.

Loads environment variables and defines all shared constants.
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# --- API Keys ---
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# --- Pinecone Settings ---
INDEX_NAME = "enterprise-rag"

# --- File Storage ---
DOCUMENTS_DIR = "documents"
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

# --- Supported File Types ---
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".csv"}

# --- LLM Settings ---
LLM_MODEL = "gpt-3.5-turbo"
LLM_TEMPERATURE = 0
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
RETRIEVER_TOP_K = 10  # Retrieve more, then re-rank
RERANKER_TOP_K = 3    # Keep the best 3 after re-ranking
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

# --- Re-Ranker Settings ---
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# --- Security ---
API_KEY = os.getenv("RAG_API_KEY", "rag-admin-secret-2026")

# CORS Settings
# In production, add your Azure Static Web App URL here
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "https://proud-sea-0a1b2c3d.azurestaticapps.net", # Example placeholder
    os.getenv("FRONTEND_URL", "") 
]
# Filter out empty strings
ALLOWED_ORIGINS = [origin for origin in ALLOWED_ORIGINS if origin]

