"""
Chat Pydantic schemas
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, validator
import uuid

class ChatRequest(BaseModel):
    """Chat request schema"""
    message: str
    conversation_id: Optional[uuid.UUID] = None
    conversation_history: Optional[List[Dict[str, str]]] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    
    @validator('message')
    def message_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()
    
    @validator('temperature')
    def temperature_range(cls, v):
        if v is not None and (v < 0 or v > 2):
            raise ValueError('Temperature must be between 0 and 2')
        return v

class ChatResponse(BaseModel):
    """Chat response schema"""
    response: str
    citations: List[Dict[str, Any]] = []
    conversation_id: Optional[uuid.UUID] = None
    tokens_used: Optional[int] = None
    ai_model: Optional[str] = None
    response_time_ms: Optional[int] = None

class ConversationCreate(BaseModel):
    """Conversation creation schema"""
    title: str
    description: Optional[str] = None
    is_public: bool = False
    
    @validator('title')
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

class ConversationUpdate(BaseModel):
    """Conversation update schema"""
    title: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None

class ConversationResponse(BaseModel):
    """Conversation response schema"""
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: Optional[str] = None
    is_public: bool
    message_count: int
    total_tokens_used: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: List['MessageResponse'] = []
    
    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    """Message response schema"""
    id: uuid.UUID
    conversation_id: uuid.UUID
    user_id: uuid.UUID
    content: str
    role: str
    message_type: str
    tokens_used: int
    ai_model: Optional[str] = None
    temperature: Optional[int] = None
    citations: Optional[List[Dict[str, Any]]] = None
    sources_used: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ChatSession(BaseModel):
    """Chat session schema"""
    session_id: str
    user_id: Optional[uuid.UUID] = None
    conversation_id: Optional[uuid.UUID] = None
    created_at: datetime
    last_activity: datetime
    message_count: int

class TypingIndicator(BaseModel):
    """Typing indicator schema"""
    is_typing: bool
    user_id: Optional[uuid.UUID] = None
    conversation_id: uuid.UUID
