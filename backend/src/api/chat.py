"""
backend/src/api/chat.py — Chat endpoint.

Updated for Streaming:
  - Uses StreamingResponse
  - Integrates astream_pipeline
"""

import logging
from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage

from backend.src.schemas.chat_schemas import ChatRequest
from backend.src.utils.security import get_api_key

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger("uvicorn.error")

@router.post("/", dependencies=[Depends(get_api_key)])
async def chat_endpoint(request: Request, chat_req: ChatRequest):
    """
    Process a user question through the RAG pipeline with streaming.
    """
    logger.info(f"Processing streaming question: {chat_req.message}")
    
    rag_engine = request.app.state.rag_engine
    
    # Convert chat history to LangChain format
    chat_history = []
    for msg in chat_req.history:
        if msg.role == "user":
            chat_history.append(HumanMessage(content=msg.content))
        else:
            chat_history.append(AIMessage(content=msg.content))
    
    async def event_generator():
        """Generator that yields bytes for the StreamingResponse."""
        async for chunk in rag_engine.astream_pipeline(chat_req.message, chat_history):
            # Yield as utf-8 bytes
            yield f"{chunk}".encode("utf-8")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
