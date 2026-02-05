import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add unique request ID to each request for tracking"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or use existing request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
