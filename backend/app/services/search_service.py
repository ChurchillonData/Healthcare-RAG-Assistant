"""
Search service for document and knowledge base search
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from app.models.query import SearchQuery
from app.schemas.search import SearchRequest, SearchFilters
from app.services.rag_service import RAGService
from app.core.logging import get_logger

logger = get_logger(__name__)

class SearchService:
    """Search service for document and knowledge base search"""
    
    def __init__(self, db: Session):
        self.db = db
        self.rag_service = RAGService()
    
    async def semantic_search(
        self, 
        query: str, 
        filters: Optional[SearchFilters] = None,
        limit: int = 10, 
        offset: int = 0
    ) -> Dict[str, Any]:
        """Perform semantic search"""
        start_time = datetime.utcnow()
        
        try:
            # Use RAG service to search for relevant documents
            documents = await self.rag_service.search_relevant_documents(query, limit)
            
            # Apply filters if provided
            if filters:
                documents = self._apply_filters(documents, filters)
            
            # Calculate search time
            search_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Format results
            results = {
                "documents": documents,
                "total_results": len(documents),
                "search_time_ms": search_time_ms,
                "suggestions": await self._generate_suggestions(query),
                "filters_applied": filters.dict() if filters else None
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return {
                "documents": [],
                "total_results": 0,
                "search_time_ms": 0,
                "suggestions": [],
                "filters_applied": None
            }
    
    async def get_search_suggestions(self, query: str, limit: int = 10, user_id: Optional[str] = None) -> List[str]:
        """Get search suggestions based on query"""
        try:
            # Get popular queries that start with the input
            suggestions = self.db.query(SearchQuery.query_text).filter(
                SearchQuery.query_text.ilike(f"{query}%")
            ).group_by(
                SearchQuery.query_text
            ).order_by(
                desc(func.count(SearchQuery.id))
            ).limit(limit).all()
            
            return [suggestion[0] for suggestion in suggestions]
            
        except Exception as e:
            logger.error(f"Error getting search suggestions: {e}")
            return []
    
    async def get_available_filters(self) -> Dict[str, Any]:
        """Get available search filters"""
        try:
            # This would typically query your document metadata
            # For now, return mock filter options
            filters = {
                "document_types": [
                    {"value": "journal", "label": "Journal Articles", "count": 1250},
                    {"value": "book", "label": "Books", "count": 340},
                    {"value": "website", "label": "Websites", "count": 890},
                    {"value": "conference", "label": "Conference Papers", "count": 567}
                ],
                "date_ranges": [
                    {"value": "2023-2024", "label": "2023-2024", "count": 450},
                    {"value": "2021-2022", "label": "2021-2022", "count": 380},
                    {"value": "2019-2020", "label": "2019-2020", "count": 290}
                ],
                "languages": [
                    {"value": "en", "label": "English", "count": 2100},
                    {"value": "es", "label": "Spanish", "count": 120},
                    {"value": "fr", "label": "French", "count": 85}
                ]
            }
            
            return filters
            
        except Exception as e:
            logger.error(f"Error getting available filters: {e}")
            return {}
    
    def get_trending_searches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending search queries"""
        try:
            # Get popular searches from the last 7 days
            trending = self.db.query(
                SearchQuery.query_text,
                func.count(SearchQuery.id).label('count')
            ).filter(
                SearchQuery.created_at >= datetime.utcnow() - timedelta(days=7)
            ).group_by(
                SearchQuery.query_text
            ).order_by(
                desc('count')
            ).limit(limit).all()
            
            return [
                {
                    "query": item.query_text,
                    "count": item.count
                }
                for item in trending
            ]
            
        except Exception as e:
            logger.error(f"Error getting trending searches: {e}")
            return []
    
    def log_search_activity(self, user_id: str, query: str, results_count: int):
        """Log search activity"""
        try:
            search_query = SearchQuery(
                user_id=user_id,
                query_text=query,
                results_count=results_count
            )
            
            self.db.add(search_query)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error logging search activity: {e}")
    
    def submit_search_feedback(
        self, 
        search_id: str, 
        user_id: Optional[str], 
        rating: int, 
        feedback: Optional[str] = None
    ) -> bool:
        """Submit feedback for search results"""
        try:
            search_query = self.db.query(SearchQuery).filter(
                SearchQuery.id == search_id
            ).first()
            
            if not search_query:
                return False
            
            search_query.rating = rating
            search_query.feedback_text = feedback
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error submitting search feedback: {e}")
            return False
    
    def _apply_filters(self, documents: List[Dict[str, Any]], filters: SearchFilters) -> List[Dict[str, Any]]:
        """Apply filters to search results"""
        filtered_docs = documents
        
        if filters.document_types:
            filtered_docs = [
                doc for doc in filtered_docs 
                if doc.get('document_type') in filters.document_types
            ]
        
        if filters.authors:
            filtered_docs = [
                doc for doc in filtered_docs 
                if any(author in doc.get('authors', []) for author in filters.authors)
            ]
        
        if filters.min_relevance_score:
            filtered_docs = [
                doc for doc in filtered_docs 
                if doc.get('relevance_score', 0) >= filters.min_relevance_score
            ]
        
        return filtered_docs
    
    async def _generate_suggestions(self, query: str) -> List[str]:
        """Generate search suggestions"""
        # This could use AI to generate related queries
        # For now, return simple variations
        suggestions = []
        
        # Add query variations
        if "health" in query.lower():
            suggestions.extend(["healthcare AI", "medical AI", "health technology"])
        
        if "ai" in query.lower():
            suggestions.extend(["artificial intelligence", "machine learning", "AI applications"])
        
        return suggestions[:5]  # Limit to 5 suggestions
