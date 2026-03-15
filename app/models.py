"""
models.py — Pydantic models for API request/response validation.

Defines the data shapes that the frontend sends to the backend.
"""

from pydantic import BaseModel
from typing import List, Optional


class ChatMessage(BaseModel):
    """A single message in the chat history."""
    role: str  # "user" or "ai"
    content: str


class ChatRequest(BaseModel):
    """The payload sent by the frontend to the /chat endpoint."""
    message: str
    history: Optional[List[ChatMessage]] = []
