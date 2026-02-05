"""
XSS Protection Middleware
Validates and sanitizes request data to prevent XSS attacks
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from typing import Callable
import logging
import json
from app.core.xss_protection import validate_no_xss_patterns

logger = logging.getLogger(__name__)


class XSSProtectionMiddleware(BaseHTTPMiddleware):
    """Middleware to detect and prevent XSS attacks in request data"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check query parameters for XSS patterns
        for param_name, param_value in request.query_params.items():
            if isinstance(param_value, str) and not validate_no_xss_patterns(param_value):
                logger.warning(f"XSS attempt detected in query parameter: {param_name}")
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid input detected. XSS attempt blocked."}
                )

        # Check headers for XSS patterns (except Authorization which is base64)
        excluded_headers = {'authorization', 'cookie', 'x-request-id'}
        for header_name, header_value in request.headers.items():
            if header_name.lower() not in excluded_headers:
                if isinstance(header_value, str) and not validate_no_xss_patterns(header_value):
                    logger.warning(f"XSS attempt detected in header: {header_name}")
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "Invalid input detected. XSS attempt blocked."}
                    )

        # Check request body for XSS patterns (for JSON requests)
        # After reading request.body() the stream is consumed — we must pass the same body
        # to the next handler or FastAPI will hang waiting for body.
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                body = await request.body()
                try:
                    if body:
                        body_json = json.loads(body)
                        if self._contains_xss_patterns(body_json):
                            logger.warning("XSS attempt detected in request body")
                            return JSONResponse(
                                status_code=400,
                                content={"detail": "Invalid input detected. XSS attempt blocked."}
                            )
                except (json.JSONDecodeError, ValueError):
                    pass
                # Restore body for downstream (FastAPI reads it again for Pydantic)
                async def receive():
                    return {"type": "http.request", "body": body, "more_body": False}
                request = Request(request.scope, receive)

        response = await call_next(request)
        return response

    def _contains_xss_patterns(self, data: any) -> bool:
        """Recursively check data structure for XSS patterns"""
        if isinstance(data, str):
            return not validate_no_xss_patterns(data)
        elif isinstance(data, dict):
            return any(self._contains_xss_patterns(value) for value in data.values())
        elif isinstance(data, list):
            return any(self._contains_xss_patterns(item) for item in data)
        return False
