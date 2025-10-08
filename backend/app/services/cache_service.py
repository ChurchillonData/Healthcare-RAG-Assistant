"""
Cache service for Redis operations
"""

import json
import pickle
from typing import Any, Optional, Union
from datetime import timedelta
import redis
from redis.exceptions import RedisError

from app.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

class CacheService:
    """Redis cache service"""
    
    def __init__(self):
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=False,  # We'll handle encoding/decoding manually
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except RedisError:
            return False
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set cache value"""
        if not self.is_connected():
            return False
        
        try:
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            elif isinstance(value, str):
                serialized_value = value
            else:
                serialized_value = pickle.dumps(value)
            
            if expire:
                self.redis_client.setex(key, expire, serialized_value)
            else:
                self.redis_client.set(key, serialized_value)
            
            return True
        except RedisError as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get cache value"""
        if not self.is_connected():
            return None
        
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            
            # Try to deserialize as JSON first, then pickle
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                try:
                    return pickle.loads(value)
                except (pickle.PickleError, TypeError):
                    return value.decode('utf-8') if isinstance(value, bytes) else value
        
        except RedisError as e:
            logger.error(f"Failed to get cache key {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete cache key"""
        if not self.is_connected():
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except RedisError as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.is_connected():
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except RedisError as e:
            logger.error(f"Failed to check existence of key {key}: {e}")
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key"""
        if not self.is_connected():
            return False
        
        try:
            return bool(self.redis_client.expire(key, seconds))
        except RedisError as e:
            logger.error(f"Failed to set expiration for key {key}: {e}")
            return False
    
    def get_ttl(self, key: str) -> int:
        """Get time to live for key"""
        if not self.is_connected():
            return -1
        
        try:
            return self.redis_client.ttl(key)
        except RedisError as e:
            logger.error(f"Failed to get TTL for key {key}: {e}")
            return -1
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter"""
        if not self.is_connected():
            return None
        
        try:
            return self.redis_client.incrby(key, amount)
        except RedisError as e:
            logger.error(f"Failed to increment key {key}: {e}")
            return None
    
    def set_hash(self, key: str, mapping: dict, expire: Optional[int] = None) -> bool:
        """Set hash values"""
        if not self.is_connected():
            return False
        
        try:
            self.redis_client.hset(key, mapping=mapping)
            if expire:
                self.redis_client.expire(key, expire)
            return True
        except RedisError as e:
            logger.error(f"Failed to set hash {key}: {e}")
            return False
    
    def get_hash(self, key: str) -> Optional[dict]:
        """Get hash values"""
        if not self.is_connected():
            return None
        
        try:
            return self.redis_client.hgetall(key)
        except RedisError as e:
            logger.error(f"Failed to get hash {key}: {e}")
            return None
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern"""
        if not self.is_connected():
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except RedisError as e:
            logger.error(f"Failed to clear pattern {pattern}: {e}")
            return 0
