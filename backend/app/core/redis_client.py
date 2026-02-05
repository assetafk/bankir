import redis
from typing import Optional
from app.config import settings


class RedisClient:
    _instance: Optional['RedisClient'] = None
    _client: Optional[redis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self._client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

    @property
    def client(self) -> redis.Redis:
        """Get Redis client instance"""
        return self._client

    def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        try:
            return self._client.get(key)
        except redis.RedisError:
            return None

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set value in Redis with optional TTL"""
        try:
            if ttl:
                return self._client.setex(key, ttl, value)
            return self._client.set(key, value)
        except redis.RedisError:
            return False

    def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            return bool(self._client.delete(key))
        except redis.RedisError:
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        try:
            return bool(self._client.exists(key))
        except redis.RedisError:
            return False


# Global Redis client instance
redis_client = RedisClient()
