"""
Chat endpoints for AI conversations
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_active_user, get_optional_current_user
from app.schemas.chat import ChatRequest, ChatResponse, ConversationCreate, ConversationResponse, MessageResponse
from app.services.chat_service import ChatService
from app.services.rag_service import RAGService
from app.models.user import User

router = APIRouter()

@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation"""
    chat_service = ChatService(db)
    conversation = chat_service.create_conversation(conversation_data, current_user.id)
    return ConversationResponse.from_orm(conversation)

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's conversations"""
    chat_service = ChatService(db)
    conversations = chat_service.get_user_conversations(current_user.id)
    return [ConversationResponse.from_orm(conv) for conv in conversations]

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    chat_request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Send a message to the AI assistant"""
    try:
        chat_service = ChatService(db)
        rag_service = RAGService()
        
        # Get relevant context using RAG
        relevant_docs = await rag_service.search_relevant_documents(chat_request.message)
        
        # Generate AI response
        ai_response = await rag_service.generate_response(
            query=chat_request.message,
            context_documents=relevant_docs,
            conversation_history=chat_request.conversation_history
        )
        
        # Save conversation if user is authenticated
        if current_user:
            background_tasks.add_task(
                chat_service.save_message,
                chat_request.conversation_id,
                current_user.id,
                chat_request.message,
                ai_response["response"],
                relevant_docs
            )
        
        return ChatResponse(
            response=ai_response["response"],
            citations=ai_response["citations"],
            conversation_id=chat_request.conversation_id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat request: {str(e)}"
        )

@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific conversation"""
    chat_service = ChatService(db)
    conversation = chat_service.get_conversation(conversation_id, current_user.id)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return ConversationResponse.from_orm(conversation)

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation"""
    chat_service = ChatService(db)
    success = chat_service.delete_conversation(conversation_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return {"message": "Conversation deleted successfully"}
