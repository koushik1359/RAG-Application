"""
routers/documents.py — Document management endpoints.

Provides endpoints for listing, deleting, and clearing documents
from both local storage and the Pinecone vector database.
"""

import os

from fastapi import APIRouter

from app.config import DOCUMENTS_DIR
from app.rag_engine import embeddings, pinecone_index

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/")
async def list_documents():
    """List all uploaded documents in the documents folder."""
    files = []
    if os.path.exists(DOCUMENTS_DIR):
        for f in os.listdir(DOCUMENTS_DIR):
            file_path = os.path.join(DOCUMENTS_DIR, f)
            if os.path.isfile(file_path):
                size_kb = round(os.path.getsize(file_path) / 1024, 1)
                files.append({"name": f, "size_kb": size_kb})
    return {"documents": files}


@router.delete("/{filename}")
async def delete_document(filename: str):
    """Delete a specific document from local storage and Pinecone."""
    file_path = os.path.join(DOCUMENTS_DIR, filename)
    
    # Delete from local storage
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Delete matching vectors from Pinecone
    try:
        dummy_vector = embeddings.embed_query("placeholder")
        results = pinecone_index.query(
            vector=dummy_vector,
            top_k=10000,
            filter={"source": {"$eq": f"documents/{filename}"}},
            include_metadata=False
        )
        
        if results.matches:
            ids_to_delete = [match.id for match in results.matches]
            pinecone_index.delete(ids=ids_to_delete)
            return {"success": True, "message": f"Deleted {filename} and {len(ids_to_delete)} vectors from the database."}
        else:
            return {"success": True, "message": f"Deleted {filename} from local storage. No matching vectors found in database."}
    except Exception as e:
        return {"success": True, "message": f"Deleted {filename} locally. Database cleanup note: {str(e)}"}


@router.post("/clear")
async def clear_all_documents():
    """Wipe all documents from local storage and Pinecone."""
    # Clear local files
    if os.path.exists(DOCUMENTS_DIR):
        for f in os.listdir(DOCUMENTS_DIR):
            file_path = os.path.join(DOCUMENTS_DIR, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
    
    # Clear Pinecone
    try:
        pinecone_index.delete(delete_all=True)
    except Exception as e:
        print(f"Error clearing Pinecone: {e}")
    
    return {"success": True, "message": "All documents and vectors have been cleared."}
