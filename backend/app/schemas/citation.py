"""
Citation Pydantic schemas
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, validator
import uuid

class CitationCreate(BaseModel):
    """Citation creation schema"""
    document_id: str
    document_title: str
    document_url: Optional[str] = None
    content: str
    context: Optional[str] = None
    page_number: Optional[int] = None
    section: Optional[str] = None
    source_type: str  # 'journal', 'book', 'website', 'document'
    authors: Optional[List[str]] = None
    publication_date: Optional[datetime] = None
    publisher: Optional[str] = None
    journal_name: Optional[str] = None
    citation_style: str = "apa"
    doi: Optional[str] = None
    isbn: Optional[str] = None
    issn: Optional[str] = None
    
    @validator('source_type')
    def valid_source_type(cls, v):
        valid_types = ["journal", "book", "website", "document", "conference", "report"]
        if v not in valid_types:
            raise ValueError(f'Source type must be one of: {valid_types}')
        return v
    
    @validator('citation_style')
    def valid_citation_style(cls, v):
        valid_styles = ["apa", "mla", "chicago", "harvard", "ieee"]
        if v not in valid_styles:
            raise ValueError(f'Citation style must be one of: {valid_styles}')
        return v

class CitationUpdate(BaseModel):
    """Citation update schema"""
    document_title: Optional[str] = None
    document_url: Optional[str] = None
    content: Optional[str] = None
    context: Optional[str] = None
    page_number: Optional[int] = None
    section: Optional[str] = None
    source_type: Optional[str] = None
    authors: Optional[List[str]] = None
    publication_date: Optional[datetime] = None
    publisher: Optional[str] = None
    journal_name: Optional[str] = None
    citation_style: Optional[str] = None
    doi: Optional[str] = None
    isbn: Optional[str] = None
    issn: Optional[str] = None
    verification_notes: Optional[str] = None

class CitationResponse(BaseModel):
    """Citation response schema"""
    id: uuid.UUID
    document_id: str
    document_title: str
    document_url: Optional[str] = None
    content: str
    context: Optional[str] = None
    page_number: Optional[int] = None
    section: Optional[str] = None
    source_type: str
    authors: Optional[List[str]] = None
    publication_date: Optional[datetime] = None
    publisher: Optional[str] = None
    journal_name: Optional[str] = None
    citation_style: str
    doi: Optional[str] = None
    isbn: Optional[str] = None
    issn: Optional[str] = None
    is_verified: bool
    verification_date: Optional[datetime] = None
    verification_notes: Optional[str] = None
    usage_count: int
    last_used: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class CitationVerification(BaseModel):
    """Citation verification schema"""
    is_accessible: bool
    http_status: Optional[int] = None
    response_time_ms: Optional[int] = None
    last_checked: datetime
    error_message: Optional[str] = None
    redirect_url: Optional[str] = None

class CitationBatchVerify(BaseModel):
    """Batch citation verification schema"""
    citation_ids: List[uuid.UUID]
    verification_results: Dict[str, CitationVerification]

class CitationStats(BaseModel):
    """Citation statistics schema"""
    total_citations: int
    verified_citations: int
    unverified_citations: int
    verification_rate: float
    most_cited_documents: List[Dict[str, Any]]
    citations_by_source_type: Dict[str, int]
    recent_verifications: List[Dict[str, Any]]

class CitationExport(BaseModel):
    """Citation export schema"""
    format: str  # "bibtex", "ris", "csv", "json"
    citation_ids: Optional[List[uuid.UUID]] = None
    include_metadata: bool = True
    
    @validator('format')
    def valid_export_format(cls, v):
        valid_formats = ["bibtex", "ris", "csv", "json", "xml"]
        if v not in valid_formats:
            raise ValueError(f'Export format must be one of: {valid_formats}')
        return v
