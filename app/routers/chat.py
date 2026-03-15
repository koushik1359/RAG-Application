"""
routers/chat.py — Chat endpoint for the RAG pipeline.

Handles incoming user questions, converts chat history to LangChain format,
runs the RAG chain, and returns the answer with source citations.
"""

from fastapi import APIRouter
from langchain_core.messages import HumanMessage, AIMessage

from app.models import ChatRequest
from app.rag_engine import rag_chain

router = APIRouter()


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Process a user question through the RAG pipeline with chat history."""
    print(f"Received question: {request.message}")
    print(f"Chat history length: {len(request.history)}")
    
    # Convert frontend chat history to LangChain message format
    chat_history = []
    for msg in request.history:
        if msg.role == "user":
            chat_history.append(HumanMessage(content=msg.content))
        else:
            chat_history.append(AIMessage(content=msg.content))
    
    # Run the RAG pipeline WITH chat history
    response = rag_chain.invoke({
        "input": request.message,
        "chat_history": chat_history
    })
    
    # Extract the sources so we can send them to the frontend
    sources = []
    for doc in response["context"]:
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", "Unknown")
        sources.append({"source": source, "page": page, "content": doc.page_content})
        
    return {
        "answer": response["answer"],
        "sources": sources
    }
