"""
Search Pydantic schemas
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, validator
import uuid

class SearchFilters(BaseModel):
    """Search filters schema"""
    document_types: Optional[List[str]] = None
    date_range: Optional[Dict[str, str]] = None  # {"start": "2023-01-01", "end": "2023-12-31"}
    authors: Optional[List[str]] = None
    journals: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    language: Optional[str] = None
    min_relevance_score: Optional[float] = None
    
    @validator('min_relevance_score')
    def relevance_score_range(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Relevance score must be between 0 and 1')
        return v

class SearchRequest(BaseModel):
    """Search request schema"""
    query: str
    filters: Optional[SearchFilters] = None
    limit: int = 10
    offset: int = 0
    search_type: str = "semantic"  # "semantic", "keyword", "hybrid"
    sort_by: str = "relevance"  # "relevance", "date", "title"
    sort_order: str = "desc"  # "asc", "desc"
    
    @validator('query')
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Search query cannot be empty')
        return v.strip()
    
    @validator('limit')
    def limit_range(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Limit must be between 1 and 100')
        return v
    
    @validator('search_type')
    def valid_search_type(cls, v):
        valid_types = ["semantic", "keyword", "hybrid"]
        if v not in valid_types:
            raise ValueError(f'Search type must be one of: {valid_types}')
        return v

class SearchResult(BaseModel):
    """Individual search result schema"""
    id: str
    title: str
    content: str
    summary: Optional[str] = None
    document_type: str
    source_url: Optional[str] = None
    authors: Optional[List[str]] = None
    publication_date: Optional[datetime] = None
    journal_name: Optional[str] = None
    relevance_score: float
    citation_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    """Search response schema"""
    query: str
    documents: List[SearchResult]
    total_results: int
    search_time_ms: int
    suggestions: Optional[List[str]] = None
    filters_applied: Optional[SearchFilters] = None
    search_id: str

class SearchSuggestion(BaseModel):
    """Search suggestion schema"""
    text: str
    type: str  # "query", "filter", "correction"
    confidence: float
    usage_count: Optional[int] = None

class SearchAnalytics(BaseModel):
    """Search analytics schema"""
    total_searches: int
    unique_users: int
    popular_queries: List[Dict[str, Any]]
    search_success_rate: float
    average_response_time: float
    most_clicked_results: List[Dict[str, Any]]

class SearchFeedback(BaseModel):
    """Search feedback schema"""
    search_id: str
    rating: int  # 1-5
    feedback_text: Optional[str] = None
    clicked_results: Optional[List[str]] = None
    user_id: Optional[uuid.UUID] = None
    
    @validator('rating')
    def rating_range(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Rating must be between 1 and 5')
        return v
