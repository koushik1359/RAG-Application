"""
backend/src/api/upload.py — Document upload endpoint.

Senior Refactor:
  - Clean error handling
  - Dependency Injection (rag_engine)
  - Security (API Key)
"""

import os
import shutil
import logging
import asyncio
from fastapi import APIRouter, UploadFile, File, Request, Depends, HTTPException

from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.src.config import DOCUMENTS_DIR, SUPPORTED_EXTENSIONS, CHUNK_SIZE, CHUNK_OVERLAP
from backend.src.utils.security import get_api_key

router = APIRouter(prefix="/upload", tags=["Upload"])
logger = logging.getLogger("uvicorn.error")

@router.post("/", dependencies=[Depends(get_api_key)])
async def upload_document(request: Request, file: UploadFile = File(...)):
    """Upload and process a document into the RAG knowledge base."""
    logger.info(f"Receiving file: {file.filename}")
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type '{file_ext}'. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    
    file_path = os.path.join(DOCUMENTS_DIR, file.filename)
    
    # Non-blocking file save (shutil isn't async, so we wrap in a thread if needed, 
    # but for prototype small files this is fine)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error saving file.")

    logger.info(f"File saved to {file_path}. Processing...")
    
    try:
        # Load documents based on extension
        if file_ext == ".pdf":
            loader = PyPDFLoader(file_path)
        elif file_ext == ".docx":
            loader = Docx2txtLoader(file_path)
        elif file_ext == ".csv":
            loader = CSVLoader(file_path)
        elif file_ext == ".txt":
            loader = TextLoader(file_path, encoding="utf-8")
        else:
            raise ValueError("Unsupported extension")
        
        # In a senior-grade system, this should be offloaded to a background task (e.g. Celery)
        # For now, we keep it in-process but use sync-to-async execution
        loop = asyncio.get_event_loop()
        raw_documents = await loop.run_in_executor(None, loader.load)
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, 
            chunk_overlap=CHUNK_OVERLAP
        )
        documents = text_splitter.split_documents(raw_documents)
        
        logger.info(f"Split {file.filename} into {len(documents)} chunks. Indexing...")
        
        # Get vectorstore from RAG Engine
        vectorstore = request.app.state.rag_engine.vectorstore
        
        # Async add_documents
        await vectorstore.aadd_documents(documents)
        
        return {
            "success": True, 
            "message": f"Successfully processed {file.filename} and added {len(documents)} context chunks."
        }
    except Exception as e:
        logger.error(f"Error processing upload {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
