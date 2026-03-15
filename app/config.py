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
RETRIEVER_TOP_K = 3
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
