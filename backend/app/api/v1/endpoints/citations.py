"""
Citation and source management endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_optional_current_user
from app.schemas.citation import CitationResponse, CitationCreate
from app.services.citation_service import CitationService
from app.models.user import User

router = APIRouter()

@router.get("/{citation_id}", response_model=CitationResponse)
async def get_citation(
    citation_id: str,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Get citation details by ID"""
    citation_service = CitationService(db)
    citation = citation_service.get_citation(citation_id)
    
    if not citation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citation not found"
        )
    
    return CitationResponse.from_orm(citation)

@router.get("/document/{document_id}", response_model=List[CitationResponse])
async def get_document_citations(
    document_id: str,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Get all citations for a specific document"""
    citation_service = CitationService(db)
    citations = citation_service.get_document_citations(document_id)
    
    return [CitationResponse.from_orm(citation) for citation in citations]

@router.post("/", response_model=CitationResponse, status_code=status.HTTP_201_CREATED)
async def create_citation(
    citation_data: CitationCreate,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Create a new citation"""
    citation_service = CitationService(db)
    citation = citation_service.create_citation(citation_data)
    
    return CitationResponse.from_orm(citation)

@router.get("/verify/{citation_id}")
async def verify_citation(
    citation_id: str,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Verify citation source accessibility"""
    citation_service = CitationService(db)
    
    verification_result = await citation_service.verify_citation_source(citation_id)
    
    if not verification_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citation not found"
        )
    
    return verification_result

@router.get("/stats/overview")
async def get_citation_stats(
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Get citation statistics overview"""
    citation_service = CitationService(db)
    
    stats = citation_service.get_citation_statistics()
    
    return stats

@router.post("/batch/verify")
async def batch_verify_citations(
    citation_ids: List[str],
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Batch verify multiple citations"""
    citation_service = CitationService(db)
    
    results = await citation_service.batch_verify_citations(citation_ids)
    
    return {"verification_results": results}
