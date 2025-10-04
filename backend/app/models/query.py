"""
Search query database model
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base

class SearchQuery(Base):
    """Search query model for tracking user searches"""
    
    __tablename__ = "search_queries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50), default="semantic", nullable=False)  # 'semantic', 'keyword', 'hybrid'
    
    # Search parameters
    filters = Column(JSON, nullable=True)  # Applied search filters
    limit = Column(Integer, default=10, nullable=False)
    offset = Column(Integer, default=0, nullable=False)
    
    # Results
    results_count = Column(Integer, default=0, nullable=False)
    results_ids = Column(JSON, nullable=True)  # Array of result document IDs
    
    # Performance metrics
    response_time_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, default=0, nullable=False)
    
    # User feedback
    rating = Column(Integer, nullable=True)  # 1-5 star rating
    feedback_text = Column(Text, nullable=True)
    clicked_results = Column(JSON, nullable=True)  # Array of clicked result IDs
    
    # Session information
    session_id = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<SearchQuery(id={self.id}, query_text={self.query_text[:50]}..., user_id={self.user_id})>"
