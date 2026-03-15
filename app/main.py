"""
main.py — FastAPI application entry point.

Creates the FastAPI app, registers CORS middleware,
and includes all routers. This is the file Uvicorn loads.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat, upload, documents

# Create the FastAPI application
app = FastAPI(
    title="Enterprise RAG API",
    description="An AI-powered document Q&A system using Retrieval-Augmented Generation.",
    version="2.0.0"
)

# Allow the frontend to talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(documents.router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "running", "message": "Enterprise RAG Engine is online."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
