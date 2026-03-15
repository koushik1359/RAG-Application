"""
routers/upload.py — File upload endpoint.

Handles PDF, DOCX, TXT, and CSV uploads. Saves the file locally,
chunks it, embeds it, and pushes it to Pinecone.
"""

import os
import shutil

from fastapi import APIRouter, UploadFile, File
from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import DOCUMENTS_DIR, SUPPORTED_EXTENSIONS, CHUNK_SIZE, CHUNK_OVERLAP
from app.rag_engine import vectorstore

router = APIRouter()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document into the RAG knowledge base."""
    print(f"Receiving file: {file.filename}")
    
    # Validate file type
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in SUPPORTED_EXTENSIONS:
        return {
            "success": False,
            "message": f"Unsupported file type '{file_ext}'. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        }
    
    # Save the file to the documents folder
    file_path = os.path.join(DOCUMENTS_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    print(f"File saved to {file_path}. Processing...")
    
    try:
        # Choose the right loader based on file extension
        if file_ext == ".pdf":
            loader = PyPDFLoader(file_path)
        elif file_ext == ".docx":
            loader = Docx2txtLoader(file_path)
        elif file_ext == ".csv":
            loader = CSVLoader(file_path)
        elif file_ext == ".txt":
            loader = TextLoader(file_path, encoding="utf-8")
        
        raw_documents = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, 
            chunk_overlap=CHUNK_OVERLAP
        )
        documents = text_splitter.split_documents(raw_documents)
        
        print(f"Split {file.filename} into {len(documents)} chunks. Uploading to Pinecone...")
        
        # Embed and upload to Pinecone
        vectorstore.add_documents(documents)
        
        return {
            "success": True, 
            "message": f"Successfully processed {file.filename} ({file_ext}) and added {len(documents)} chunks to the RAG Engine."
        }
    except Exception as e:
        print(f"Error processing upload: {e}")
        return {
            "success": False,
            "message": str(e)
        }
