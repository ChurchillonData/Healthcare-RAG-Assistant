"""
Citation database model
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base

class Citation(Base):
    """Citation model for tracking document sources"""
    
    __tablename__ = "citations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(String(255), nullable=False, index=True)
    document_title = Column(String(500), nullable=False)
    document_url = Column(String(1000), nullable=True)
    
    # Citation content
    content = Column(Text, nullable=False)  # The actual text being cited
    context = Column(Text, nullable=True)  # Surrounding context
    page_number = Column(Integer, nullable=True)
    section = Column(String(255), nullable=True)
    
    # Source information
    source_type = Column(String(50), nullable=False)  # 'journal', 'book', 'website', 'document'
    authors = Column(JSON, nullable=True)  # Array of author names
    publication_date = Column(DateTime, nullable=True)
    publisher = Column(String(255), nullable=True)
    journal_name = Column(String(255), nullable=True)
    
    # Citation metadata
    citation_style = Column(String(50), default="apa", nullable=False)
    doi = Column(String(255), nullable=True)
    isbn = Column(String(255), nullable=True)
    issn = Column(String(255), nullable=True)
    
    # Verification status
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_date = Column(DateTime, nullable=True)
    verification_notes = Column(Text, nullable=True)
    
    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)
    last_used = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Citation(id={self.id}, document_title={self.document_title}, source_type={self.source_type})>"
