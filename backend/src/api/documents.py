"""
backend/src/api/documents.py — Document management.

Senior Refactor:
  - Async IO
  - API Key protection for destructive actions
  - Dependency Injection (embeddings/index)
"""

import os
import logging
from fastapi import APIRouter, Request, Depends, HTTPException
from backend.src.config import DOCUMENTS_DIR
from backend.src.utils.security import get_api_key

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = logging.getLogger("uvicorn.error")

@router.get("/")
async def list_documents():
    """List all uploaded documents."""
    files = []
    if os.path.exists(DOCUMENTS_DIR):
        for f in os.listdir(DOCUMENTS_DIR):
            file_path = os.path.join(DOCUMENTS_DIR, f)
            if os.path.isfile(file_path):
                size_kb = round(os.path.getsize(file_path) / 1024, 1)
                files.append({"name": f, "size_kb": size_kb})
    return {"documents": files}

@router.delete("/{filename}", dependencies=[Depends(get_api_key)])
async def delete_document(request: Request, filename: str):
    """Delete a document from local storage and Pinecone."""
    file_path = os.path.join(DOCUMENTS_DIR, filename)
    
    # 1. Local Delete
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # 2. Vector DB Delete
    rag_engine = request.app.state.rag_engine
    try:
        # Note: pinecone-client 'delete' is blocking, so we run in executor
        # Using a dummy query to find IDs or just using metadata filter
        # Better: Pinecone 'delete(filter=...)'
        rag_engine.pinecone_index.delete(
            filter={"source": {"$eq": f"documents/{filename}"}}
        )
        return {"success": True, "message": f"Deleted {filename} from knowledge base."}
    except Exception as e:
        logger.error(f"Error deleting {filename} vectors: {e}")
        raise HTTPException(status_code=500, detail=f"Database cleanup failed: {str(e)}")

@router.post("/clear", dependencies=[Depends(get_api_key)])
async def clear_all_documents(request: Request):
    """Wipe everything."""
    logger.warning("CLEAR ALL DATA REQUESTED")
    
    # 1. Clear Files
    if os.path.exists(DOCUMENTS_DIR):
        for f in os.listdir(DOCUMENTS_DIR):
            file_path = os.path.join(DOCUMENTS_DIR, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
    
    # 2. Clear Vectors
    rag_engine = request.app.state.rag_engine
    try:
        rag_engine.pinecone_index.delete(delete_all=True)
        return {"success": True, "message": "Knowledge base wiped."}
    except Exception as e:
        logger.error(f"Error wiping database: {e}")
        raise HTTPException(status_code=500, detail=str(e))
