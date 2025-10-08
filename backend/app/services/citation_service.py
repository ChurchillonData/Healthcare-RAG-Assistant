"""
Citation service for managing document citations
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from app.models.citation import Citation
from app.schemas.citation import CitationCreate, CitationVerification
from app.core.logger import get_logger

logger = get_logger(__name__)

class CitationService:
    """Citation service for managing document citations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_citation(self, citation_id: str) -> Optional[Citation]:
        """Get citation by ID"""
        return self.db.query(Citation).filter(Citation.id == citation_id).first()
    
    def get_document_citations(self, document_id: str) -> List[Citation]:
        """Get all citations for a specific document"""
        return self.db.query(Citation).filter(
            Citation.document_id == document_id
        ).order_by(Citation.created_at).all()
    
    def create_citation(self, citation_data: CitationCreate) -> Citation:
        """Create a new citation"""
        db_citation = Citation(
            document_id=citation_data.document_id,
            document_title=citation_data.document_title,
            document_url=citation_data.document_url,
            content=citation_data.content,
            context=citation_data.context,
            page_number=citation_data.page_number,
            section=citation_data.section,
            source_type=citation_data.source_type,
            authors=citation_data.authors,
            publication_date=citation_data.publication_date,
            publisher=citation_data.publisher,
            journal_name=citation_data.journal_name,
            citation_style=citation_data.citation_style,
            doi=citation_data.doi,
            isbn=citation_data.isbn,
            issn=citation_data.issn
        )
        
        self.db.add(db_citation)
        self.db.commit()
        self.db.refresh(db_citation)
        
        return db_citation
    
    async def verify_citation_source(self, citation_id: str) -> Optional[CitationVerification]:
        """Verify citation source accessibility"""
        citation = self.get_citation(citation_id)
        if not citation or not citation.document_url:
            return None
        
        try:
            start_time = datetime.utcnow()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    citation.document_url, 
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                    
                    verification = CitationVerification(
                        is_accessible=response.status == 200,
                        http_status=response.status,
                        response_time_ms=response_time,
                        last_checked=datetime.utcnow(),
                        error_message=None if response.status == 200 else f"HTTP {response.status}",
                        redirect_url=str(response.url) if response.url != citation.document_url else None
                    )
                    
                    # Update citation verification status
                    citation.is_verified = verification.is_accessible
                    citation.verification_date = verification.last_checked
                    citation.verification_notes = verification.error_message
                    
                    self.db.commit()
                    
                    return verification
                    
        except Exception as e:
            logger.error(f"Error verifying citation {citation_id}: {e}")
            
            verification = CitationVerification(
                is_accessible=False,
                http_status=None,
                response_time_ms=None,
                last_checked=datetime.utcnow(),
                error_message=str(e),
                redirect_url=None
            )
            
            # Update citation with error
            citation.is_verified = False
            citation.verification_date = verification.last_checked
            citation.verification_notes = verification.error_message
            
            self.db.commit()
            
            return verification
    
    async def batch_verify_citations(self, citation_ids: List[str]) -> Dict[str, CitationVerification]:
        """Batch verify multiple citations"""
        tasks = []
        for citation_id in citation_ids:
            task = self.verify_citation_source(citation_id)
            tasks.append((citation_id, task))
        
        results = {}
        for citation_id, task in tasks:
            try:
                verification = await task
                results[citation_id] = verification
            except Exception as e:
                logger.error(f"Error in batch verification for {citation_id}: {e}")
                results[citation_id] = CitationVerification(
                    is_accessible=False,
                    http_status=None,
                    response_time_ms=None,
                    last_checked=datetime.utcnow(),
                    error_message=str(e),
                    redirect_url=None
                )
        
        return results
    
    def get_citation_statistics(self) -> Dict[str, Any]:
        """Get citation statistics overview"""
        try:
            total_citations = self.db.query(Citation).count()
            verified_citations = self.db.query(Citation).filter(Citation.is_verified == True).count()
            unverified_citations = total_citations - verified_citations
            
            verification_rate = (verified_citations / total_citations * 100) if total_citations > 0 else 0
            
            # Most cited documents
            most_cited = self.db.query(
                Citation.document_title,
                func.count(Citation.id).label('citation_count')
            ).group_by(
                Citation.document_title
            ).order_by(
                desc('citation_count')
            ).limit(10).all()
            
            # Citations by source type
            by_source_type = self.db.query(
                Citation.source_type,
                func.count(Citation.id).label('count')
            ).group_by(
                Citation.source_type
            ).all()
            
            # Recent verifications
            recent_verifications = self.db.query(Citation).filter(
                Citation.verification_date.isnot(None)
            ).order_by(
                desc(Citation.verification_date)
            ).limit(5).all()
            
            return {
                "total_citations": total_citations,
                "verified_citations": verified_citations,
                "unverified_citations": unverified_citations,
                "verification_rate": round(verification_rate, 2),
                "most_cited_documents": [
                    {
                        "title": item.document_title,
                        "citation_count": item.citation_count
                    }
                    for item in most_cited
                ],
                "citations_by_source_type": {
                    item.source_type: item.count 
                    for item in by_source_type
                },
                "recent_verifications": [
                    {
                        "id": str(citation.id),
                        "title": citation.document_title,
                        "is_verified": citation.is_verified,
                        "verification_date": citation.verification_date
                    }
                    for citation in recent_verifications
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting citation statistics: {e}")
            return {
                "error": str(e),
                "total_citations": 0,
                "verified_citations": 0,
                "unverified_citations": 0,
                "verification_rate": 0
            }
    
    def update_citation_usage(self, citation_id: str):
        """Update citation usage count"""
        citation = self.get_citation(citation_id)
        if citation:
            citation.usage_count += 1
            citation.last_used = datetime.utcnow()
            self.db.commit()
    
    def search_citations(self, query: str, limit: int = 20) -> List[Citation]:
        """Search citations by content or title"""
        return self.db.query(Citation).filter(
            Citation.content.ilike(f"%{query}%") | 
            Citation.document_title.ilike(f"%{query}%")
        ).order_by(
            desc(Citation.usage_count)
        ).limit(limit).all()
    
    def get_citations_by_author(self, author: str, limit: int = 20) -> List[Citation]:
        """Get citations by author"""
        return self.db.query(Citation).filter(
            Citation.authors.contains([author])
        ).order_by(
            desc(Citation.publication_date)
        ).limit(limit).all()
    
    def get_citations_by_source_type(self, source_type: str, limit: int = 20) -> List[Citation]:
        """Get citations by source type"""
        return self.db.query(Citation).filter(
            Citation.source_type == source_type
        ).order_by(
            desc(Citation.created_at)
        ).limit(limit).all()
