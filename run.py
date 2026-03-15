"""
app.py — Legacy entry point (kept for backward compatibility).

The application has been refactored into a modular structure.
See the app/ directory for the full codebase:
  - app/main.py       → FastAPI app + middleware
  - app/config.py     → Configuration & environment variables
  - app/models.py     → Pydantic request/response models
  - app/rag_engine.py → AI pipeline (embeddings, LLM, RAG chain)
  - app/routers/      → API endpoints (chat, upload, documents)

To run:  python -m uvicorn app.main:app
"""

# Re-export the app for backward compatibility
from app.main import app  # noqa: F401
