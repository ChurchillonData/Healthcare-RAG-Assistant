"""
Analytics service for tracking user behavior and system metrics
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.query import SearchQuery
from app.models.citation import Citation
from app.services.cache_service import CacheService

class AnalyticsService:
    """Analytics service for tracking and reporting metrics"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache = CacheService()
    
    def track_user_activity(self, user_id: str, activity_type: str, metadata: Dict[str, Any] = None):
        """Track user activity"""
        try:
            activity_data = {
                "user_id": user_id,
                "activity_type": activity_type,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            # Store in cache for real-time analytics
            cache_key = f"user_activity:{user_id}:{datetime.utcnow().strftime('%Y%m%d')}"
            self.cache.set_hash(cache_key, activity_data, expire=86400)  # 24 hours
            
            # Could also store in database for long-term analytics
            # self._store_activity_in_db(activity_data)
            
        except Exception as e:
            # Log error but don't fail the request
            print(f"Error tracking user activity: {e}")
    
    def get_user_activity_summary(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Get user activity summary"""
        cache_key = f"user_activity_summary:{user_id}:{days}"
        cached_result = self.cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            # Get conversation count
            conversation_count = self.db.query(Conversation).filter(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.created_at >= datetime.utcnow() - timedelta(days=days)
                )
            ).count()
            
            # Get message count
            message_count = self.db.query(Message).join(Conversation).filter(
                and_(
                    Conversation.user_id == user_id,
                    Message.created_at >= datetime.utcnow() - timedelta(days=days)
                )
            ).count()
            
            # Get search count
            search_count = self.db.query(SearchQuery).filter(
                and_(
                    SearchQuery.user_id == user_id,
                    SearchQuery.created_at >= datetime.utcnow() - timedelta(days=days)
                )
            ).count()
            
            # Get tokens used
            total_tokens = self.db.query(func.sum(Conversation.total_tokens_used)).filter(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.created_at >= datetime.utcnow() - timedelta(days=days)
                )
            ).scalar() or 0
            
            summary = {
                "conversation_count": conversation_count,
                "message_count": message_count,
                "search_count": search_count,
                "total_tokens_used": total_tokens,
                "period_days": days
            }
            
            # Cache for 1 hour
            self.cache.set(cache_key, summary, expire=3600)
            
            return summary
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics"""
        cache_key = "system_metrics"
        cached_result = self.cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            # Total users
            total_users = self.db.query(User).count()
            active_users = self.db.query(User).filter(User.is_active == True).count()
            
            # Total conversations
            total_conversations = self.db.query(Conversation).count()
            
            # Total messages
            total_messages = self.db.query(Message).count()
            
            # Total searches
            total_searches = self.db.query(SearchQuery).count()
            
            # Total citations
            total_citations = self.db.query(Citation).count()
            
            # Recent activity (last 24 hours)
            recent_conversations = self.db.query(Conversation).filter(
                Conversation.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            recent_messages = self.db.query(Message).filter(
                Message.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            recent_searches = self.db.query(SearchQuery).filter(
                SearchQuery.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            metrics = {
                "total_users": total_users,
                "active_users": active_users,
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "total_searches": total_searches,
                "total_citations": total_citations,
                "recent_activity": {
                    "conversations_24h": recent_conversations,
                    "messages_24h": recent_messages,
                    "searches_24h": recent_searches
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Cache for 5 minutes
            self.cache.set(cache_key, metrics, expire=300)
            
            return metrics
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_popular_queries(self, limit: int = 10, days: int = 7) -> List[Dict[str, Any]]:
        """Get popular search queries"""
        cache_key = f"popular_queries:{limit}:{days}"
        cached_result = self.cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            popular_queries = self.db.query(
                SearchQuery.query_text,
                func.count(SearchQuery.id).label('count'),
                func.avg(SearchQuery.rating).label('avg_rating')
            ).filter(
                SearchQuery.created_at >= datetime.utcnow() - timedelta(days=days)
            ).group_by(
                SearchQuery.query_text
            ).order_by(
                desc('count')
            ).limit(limit).all()
            
            result = [
                {
                    "query": query.query_text,
                    "count": query.count,
                    "avg_rating": float(query.avg_rating) if query.avg_rating else None
                }
                for query in popular_queries
            ]
            
            # Cache for 1 hour
            self.cache.set(cache_key, result, expire=3600)
            
            return result
            
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_conversation_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get conversation analytics"""
        cache_key = f"conversation_analytics:{days}"
        cached_result = self.cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            # Average messages per conversation
            avg_messages = self.db.query(
                func.avg(Conversation.message_count)
            ).filter(
                Conversation.created_at >= datetime.utcnow() - timedelta(days=days)
            ).scalar() or 0
            
            # Average tokens per conversation
            avg_tokens = self.db.query(
                func.avg(Conversation.total_tokens_used)
            ).filter(
                Conversation.created_at >= datetime.utcnow() - timedelta(days=days)
            ).scalar() or 0
            
            # Most active users
            active_users = self.db.query(
                Conversation.user_id,
                func.count(Conversation.id).label('conversation_count')
            ).filter(
                Conversation.created_at >= datetime.utcnow() - timedelta(days=days)
            ).group_by(
                Conversation.user_id
            ).order_by(
                desc('conversation_count')
            ).limit(10).all()
            
            analytics = {
                "avg_messages_per_conversation": float(avg_messages),
                "avg_tokens_per_conversation": float(avg_tokens),
                "most_active_users": [
                    {
                        "user_id": str(user.user_id),
                        "conversation_count": user.conversation_count
                    }
                    for user in active_users
                ],
                "period_days": days
            }
            
            # Cache for 1 hour
            self.cache.set(cache_key, analytics, expire=3600)
            
            return analytics
            
        except Exception as e:
            return {"error": str(e)}
    
    def increment_metric(self, metric_name: str, value: int = 1):
        """Increment a counter metric"""
        cache_key = f"metric:{metric_name}"
        self.cache.increment(cache_key, value)
    
    def get_metric(self, metric_name: str) -> Optional[int]:
        """Get a counter metric value"""
        cache_key = f"metric:{metric_name}"
        return self.cache.get(cache_key)
