"""
API v1 router configuration
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, chat, search, citations, health

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(citations.router, prefix="/citations", tags=["citations"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
