import json
import time
from typing import Any, Dict, Optional

from fastapi import HTTPException, status

from app.config import settings
from app.core.redis_client import redis_client


class IdempotencyService:
    @staticmethod
    def get_key(user_id: int, idempotency_key: str) -> str:
        """Generate idempotency key for Redis"""
        return f"idempotency:{user_id}:{idempotency_key}"

    @staticmethod
    def check_key(user_id: int, idempotency_key: str) -> Optional[dict]:
        """
        Check if idempotency key exists, return cached response if found.
        Also implements double request protection by checking for in-progress requests.
        """
        if not idempotency_key:
            return None

        key = IdempotencyService.get_key(user_id, idempotency_key)
        processing_key = f"{key}:processing"

        # Check if request is currently being processed (double request protection)
        if redis_client.exists(processing_key):
            time.sleep(0.1)
            if redis_client.exists(processing_key):
                # Still processing, return cached response if available
                cached_response = redis_client.get(key)
                if cached_response:
                    try:
                        return json.loads(cached_response)
                    except json.JSONDecodeError:
                        pass
                # If no cached response yet, this is a duplicate concurrent request
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "A request with this idempotency key is already "
                        "being processed"
                    ),
                )

        # Check if key exists (completed request)
        cached_response = redis_client.get(key)
        if cached_response:
            try:
                return json.loads(cached_response)
            except json.JSONDecodeError:
                # Invalid cached data, delete it
                redis_client.delete(key)

        return None

    @staticmethod
    def mark_processing(user_id: int, idempotency_key: str) -> None:
        """Mark a request as being processed (double request protection)"""
        if not idempotency_key:
            return
        
        key = IdempotencyService.get_key(user_id, idempotency_key)
        processing_key = f"{key}:processing"
        
        # Set processing flag with short TTL (5 minutes)
        redis_client.set(processing_key, "1", ttl=300)

    @staticmethod
    def clear_processing(user_id: int, idempotency_key: str) -> None:
        """Clear processing flag"""
        if not idempotency_key:
            return
        
        key = IdempotencyService.get_key(user_id, idempotency_key)
        processing_key = f"{key}:processing"
        redis_client.delete(processing_key)

    @staticmethod
    def store_response(
        user_id: int,
        idempotency_key: str,
        response_data: dict
    ) -> None:
        """
        Store the response data for idempotency
        """
        if not idempotency_key:
            return

        key = IdempotencyService.get_key(user_id, idempotency_key)

        # Store the response
        try:
            response_json = json.dumps(response_data)
            redis_client.set(key, response_json, ttl=settings.IDEMPOTENCY_TTL)
        except Exception:
            # If we can't store, continue without idempotency
            pass

    @staticmethod
    def validate_key(idempotency_key: Optional[str]) -> None:
        """Validate idempotency key format"""
        if idempotency_key and len(idempotency_key) > 255:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Idempotency key must be 255 characters or less"
            )
