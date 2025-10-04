"""
Search endpoints for document and knowledge base search
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_optional_current_user
from app.schemas.search import SearchRequest, SearchResponse, SearchFilters
from app.services.search_service import SearchService
from app.models.user import User

router = APIRouter()

@router.post("/documents", response_model=SearchResponse)
async def search_documents(
    search_request: SearchRequest,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Search documents in the knowledge base"""
    try:
        search_service = SearchService(db)
        
        # Perform semantic search
        results = await search_service.semantic_search(
            query=search_request.query,
            filters=search_request.filters,
            limit=search_request.limit,
            offset=search_request.offset
        )
        
        # Log search activity if user is authenticated
        if current_user:
            search_service.log_search_activity(
                user_id=current_user.id,
                query=search_request.query,
                results_count=len(results["documents"])
            )
        
        return SearchResponse(**results)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing search: {str(e)}"
        )

@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=20, description="Number of suggestions"),
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Get search suggestions based on query"""
    search_service = SearchService(db)
    
    suggestions = await search_service.get_search_suggestions(
        query=q,
        limit=limit,
        user_id=current_user.id if current_user else None
    )
    
    return {"suggestions": suggestions}

@router.get("/filters")
async def get_search_filters(
    db: Session = Depends(get_db)
):
    """Get available search filters"""
    search_service = SearchService(db)
    
    filters = await search_service.get_available_filters()
    
    return {"filters": filters}

@router.get("/trending")
async def get_trending_searches(
    limit: int = Query(10, ge=1, le=50, description="Number of trending searches"),
    db: Session = Depends(get_db)
):
    """Get trending search queries"""
    search_service = SearchService(db)
    
    trending = search_service.get_trending_searches(limit=limit)
    
    return {"trending_searches": trending}

@router.post("/feedback")
async def submit_search_feedback(
    search_id: str,
    rating: int = Query(..., ge=1, le=5, description="Rating from 1 to 5"),
    feedback: Optional[str] = Query(None, description="Optional feedback text"),
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Submit feedback for search results"""
    search_service = SearchService(db)
    
    success = search_service.submit_search_feedback(
        search_id=search_id,
        user_id=current_user.id if current_user else None,
        rating=rating,
        feedback=feedback
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search not found"
        )
    
    return {"message": "Feedback submitted successfully"}
