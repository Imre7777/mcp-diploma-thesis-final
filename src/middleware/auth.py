"""
Authentication Middleware for Scalekit OAuth 2.1

This middleware handles JWT token validation and role extraction from Scalekit tokens.
"""

import logging
from typing import Optional, List
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Public endpoints that don't require authentication
PUBLIC_ENDPOINTS = [
    "/health",
    "/auth/login",
    "/auth/callback",
    "/auth/logout",
]

# Development endpoints (can be disabled in production)
DEV_PUBLIC_ENDPOINTS = [
    "/docs",
    "/openapi.json",
    "/redoc",
]


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce authentication on all endpoints except public ones.
    
    Public endpoints:
    - /health: Health check (required for monitoring)
    - /auth/*: Authentication flow endpoints
    
    Protected endpoints:
    - /mcp: MCP tool calls (requires authentication)
    - /sse: Server-Sent Events (requires authentication)
    - /docs: API documentation (protected in production)
    """
    
    def __init__(self, app, debug: bool = False):
        """
        Initialize authentication middleware.
        
        Args:
            app: FastAPI application
            debug: If True, allow access to /docs without auth
        """
        super().__init__(app)
        self.debug = debug
        self.security = HTTPBearer(auto_error=False)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process each request and enforce authentication.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response from handler or 401 Unauthorized
        """
        # Check if endpoint is public
        if self._is_public_endpoint(request.path):
            return await call_next(request)
        
        # Check if endpoint is dev-only public
        if self.debug and self._is_dev_endpoint(request.path):
            logger.debug(f"Allowing access to dev endpoint: {request.path}")
            return await call_next(request)
        
        # Extract and validate token
        token = self._extract_token(request)
        if not token:
            logger.warning(f"No authentication token for protected endpoint: {request.path}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Please log in.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate token and extract user info
        # TODO: Implement JWT validation (Week 2, Day 2-3)
        user_info = await self._validate_token(token)
        if not user_info:
            logger.warning(f"Invalid token for endpoint: {request.path}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Attach user info to request state
        request.state.user = user_info
        
        return await call_next(request)
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public (no auth required)."""
        return any(path.startswith(endpoint) for endpoint in PUBLIC_ENDPOINTS)
    
    def _is_dev_endpoint(self, path: str) -> bool:
        """Check if endpoint is dev-only public."""
        return any(path.startswith(endpoint) for endpoint in DEV_PUBLIC_ENDPOINTS)
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """
        Extract JWT token from Authorization header.
        
        Args:
            request: HTTP request
            
        Returns:
            Token string or None if not present
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        
        # Handle "Bearer <token>" format
        if auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix
        
        return None
    
    async def _validate_token(self, token: str) -> Optional[dict]:
        """
        Validate JWT token and extract user information.
        
        This will be implemented in Week 2, Day 2-3 with Scalekit JWT validation.
        
        Args:
            token: JWT token string
            
        Returns:
            User info dict with role, email, etc. or None if invalid
        """
        # TODO: Implement Scalekit JWT validation
        # For now, return None (all tokens invalid until we implement validation)
        logger.debug("Token validation not yet implemented")
        return None


# Helper function to get current user from request
def get_current_user(request: Request) -> dict:
    """
    Get authenticated user from request state.
    
    Args:
        request: FastAPI request
        
    Returns:
        User info dict
        
    Raises:
        HTTPException: If user not authenticated
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return request.state.user


def get_user_role(request: Request) -> str:
    """
    Get user's role from request.
    
    Args:
        request: FastAPI request
        
    Returns:
        User's role (student, teacher, admin)
    """
    user = get_current_user(request)
    return user.get("role", "student")  # Default to student
