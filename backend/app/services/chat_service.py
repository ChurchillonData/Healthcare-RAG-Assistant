"""
Chat service for managing conversations and messages
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.conversation import Conversation, Message
from app.schemas.chat import ConversationCreate, ConversationUpdate
from app.utils.helpers import generate_uuid

class ChatService:
    """Chat service for conversation and message management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_conversation(self, conversation_data: ConversationCreate, user_id: str) -> Conversation:
        """Create a new conversation"""
        db_conversation = Conversation(
            id=generate_uuid(),
            user_id=user_id,
            title=conversation_data.title,
            description=conversation_data.description,
            is_public=conversation_data.is_public
        )
        
        self.db.add(db_conversation)
        self.db.commit()
        self.db.refresh(db_conversation)
        
        return db_conversation
    
    def get_conversation(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
        """Get a specific conversation"""
        return self.db.query(Conversation).filter(
            and_(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        ).first()
    
    def get_user_conversations(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Conversation]:
        """Get user's conversations"""
        return self.db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(
            desc(Conversation.updated_at)
        ).offset(offset).limit(limit).all()
    
    def update_conversation(self, conversation_id: str, user_id: str, update_data: ConversationUpdate) -> Optional[Conversation]:
        """Update a conversation"""
        conversation = self.get_conversation(conversation_id, user_id)
        if not conversation:
            return None
        
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(conversation, field, value)
        
        conversation.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(conversation)
        
        return conversation
    
    def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Delete a conversation"""
        conversation = self.get_conversation(conversation_id, user_id)
        if not conversation:
            return False
        
        self.db.delete(conversation)
        self.db.commit()
        return True
    
    def save_message(
        self, 
        conversation_id: str, 
        user_id: str, 
        content: str, 
        role: str = "user",
        message_type: str = "text",
        tokens_used: int = 0,
        model_used: Optional[str] = None,
        citations: Optional[List[Dict[str, Any]]] = None,
        sources_used: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Save a message to a conversation"""
        message = Message(
            id=generate_uuid(),
            conversation_id=conversation_id,
            user_id=user_id,
            content=content,
            role=role,
            message_type=message_type,
            tokens_used=tokens_used,
            model_used=model_used,
            citations=citations,
            sources_used=sources_used,
            metadata=metadata
        )
        
        self.db.add(message)
        
        # Update conversation message count and tokens
        conversation = self.get_conversation(conversation_id, user_id)
        if conversation:
            conversation.message_count += 1
            conversation.total_tokens_used += tokens_used
            conversation.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    def get_conversation_messages(self, conversation_id: str, user_id: str, limit: int = 50) -> List[Message]:
        """Get messages for a conversation"""
        # First verify user owns the conversation
        conversation = self.get_conversation(conversation_id, user_id)
        if not conversation:
            return []
        
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.created_at
        ).limit(limit).all()
    
    def get_conversation_history(self, conversation_id: str, user_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Get conversation history for context"""
        messages = self.get_conversation_messages(conversation_id, user_id, limit)
        
        history = []
        for message in messages:
            history.append({
                "role": message.role,
                "content": message.content
            })
        
        return history
    
    def search_conversations(self, user_id: str, query: str, limit: int = 20) -> List[Conversation]:
        """Search conversations by title or content"""
        # Simple text search - could be enhanced with full-text search
        return self.db.query(Conversation).filter(
            and_(
                Conversation.user_id == user_id,
                Conversation.title.ilike(f"%{query}%")
            )
        ).order_by(
            desc(Conversation.updated_at)
        ).limit(limit).all()
    
    def get_conversation_stats(self, user_id: str) -> Dict[str, Any]:
        """Get conversation statistics for a user"""
        total_conversations = self.db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).count()
        
        total_messages = self.db.query(Message).join(Conversation).filter(
            Conversation.user_id == user_id
        ).count()
        
        total_tokens = self.db.query(Conversation.total_tokens_used).filter(
            Conversation.user_id == user_id
        ).all()
        
        total_tokens_used = sum(token[0] for token in total_tokens if token[0])
        
        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "total_tokens_used": total_tokens_used
        }
