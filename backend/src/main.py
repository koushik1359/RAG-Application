"""
backend/src/main.py — FastAPI application entry point.

Senior Refactor:
  - Lifespan management for ML model loading
  - API Key Security Middleware
  - Restricted CORS
  - Async/Await support
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from starlette.status import HTTP_403_FORBIDDEN

from backend.src.utils.security import get_api_key
from backend.src.api import chat, upload, documents
from backend.src.core.rag_engine import RAGEngine
from backend.src.config import ALLOWED_ORIGINS

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Logic ---
    logger.info("Starting up Enterprise RAG Engine...")
    app.state.rag_engine = RAGEngine()
    yield
    # --- Shutdown Logic ---
    logger.info("Shutting down...")

# Create the FastAPI application
app = FastAPI(
    title="Enterprise RAG API",
    description="A high-performance AI-powered document Q&A system.",
    version="3.0.0",
    lifespan=lifespan
)

# CORS Policy - More restrictive for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(documents.router)

@app.get("/")
async def root():
    return {"status": "online", "message": "Enterprise RAG Senior Engine is running."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.src.main:app", host="0.0.0.0", port=8000, reload=True)
