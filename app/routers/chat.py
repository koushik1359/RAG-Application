"""
routers/chat.py — Chat endpoint for the RAG pipeline.

Handles incoming user questions, converts chat history to LangChain format,
runs the RAG chain with re-ranking, and returns the answer with source
citations and performance metrics.
"""

from fastapi import APIRouter
from langchain_core.messages import HumanMessage, AIMessage

from app.models import ChatRequest
from app.rag_engine import run_rag_pipeline

router = APIRouter()


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Process a user question through the RAG pipeline with re-ranking."""
    print(f"\n{'='*60}")
    print(f"Received question: {request.message}")
    print(f"Chat history length: {len(request.history)}")
    
    # Convert frontend chat history to LangChain message format
    chat_history = []
    for msg in request.history:
        if msg.role == "user":
            chat_history.append(HumanMessage(content=msg.content))
        else:
            chat_history.append(AIMessage(content=msg.content))
    
    # Run the full RAG pipeline (retrieve → re-rank → generate)
    result = run_rag_pipeline(request.message, chat_history)
    
    # Extract the sources from re-ranked documents
    sources = []
    for doc in result["context"]:
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", "Unknown")
        sources.append({"source": source, "page": page, "content": doc.page_content})
    
    print(f"{'='*60}\n")
        
    return {
        "answer": result["answer"],
        "sources": sources,
        "performance": result["performance"]
    }
