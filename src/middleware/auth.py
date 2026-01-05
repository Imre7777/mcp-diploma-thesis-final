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

# Scalekit client import
try:
    from auth.scalekit_client import ScalekitClient
    SCALEKIT_AVAILABLE = True
except ImportError:
    SCALEKIT_AVAILABLE = False
    ScalekitClient = None

logger = logging.getLogger(__name__)

# Public endpoints that don't require authentication
PUBLIC_ENDPOINTS = [
    "/health",
    "/auth/login",
    "/auth/callback",
    "/auth/logout",
    "/.well-known/",  # OAuth metadata discovery
]

# Development endpoints (can be disabled in production)
DEV_PUBLIC_ENDPOINTS = [
    "/docs",
    "/openapi.json",
    "/redoc",
]

# Default role mapping from Scalekit roles to our internal roles
SCALEKIT_ROLE_MAPPING = {
    "student": "student",
    "teacher": "teacher",
    "admin": "admin",
}


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce authentication on all endpoints except public ones.
    
    Public endpoints:
    - /health: Health check (required for monitoring)
    - /auth/*: Authentication flow endpoints
    - /.well-known/*: OAuth metadata discovery
    
    Protected endpoints:
    - /mcp: MCP tool calls (requires authentication)
    - /sse: Server-Sent Events (requires authentication)
    - /docs: API documentation (protected in production)
    """
    
    def __init__(
        self,
        app,
        scalekit_client: Optional[ScalekitClient] = None,
        mcp_resource_url: str = "http://localhost:8000",
        debug: bool = False,
    ):
        """
        Initialize authentication middleware.
        
        Args:
            app: FastAPI application
            scalekit_client: Scalekit client for token validation
            mcp_resource_url: This MCP server's base URL (for audience validation)
            debug: If True, allow access to /docs without auth
        """
        super().__init__(app)
        self.scalekit_client = scalekit_client
        self.mcp_resource_url = mcp_resource_url
        self.debug = debug
        self.security = HTTPBearer(auto_error=False)
        
        if not SCALEKIT_AVAILABLE:
            logger.warning(
                "Scalekit SDK not available. Install with: pip install scalekit"
            )
        
        if not scalekit_client:
            logger.warning(
                "No Scalekit client provided. Token validation will fail!"
            )
    
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
        Validate JWT token using Scalekit and extract user information.
        
        Uses Scalekit's validate_access_token method with audience validation.
        
        Args:
            token: JWT token string
            
        Returns:
            User info dict with role, email, etc. or None if invalid
        """
        if not self.scalekit_client or not SCALEKIT_AVAILABLE:
            logger.error("Cannot validate token: Scalekit client not available")
            return None
        
        try:
            # Validate token with Scalekit and get claims
            # This verifies signature, expiration, issuer, and audience
            claims = self.scalekit_client.validate_token_and_get_claims(
                token=token,
                audience=self.mcp_resource_url,
            )
            
            # Extract user information from claims
            user_info = {
                "sub": claims.get("sub"),  # User ID
                "email": claims.get("email"),
                "role": self._extract_role(claims),
                "name": claims.get("name"),
                "org_id": claims.get("org_id"),
                "claims": claims,  # Full claims for debugging
            }
            
            logger.info(
                f"Token validated successfully: user={user_info['email']}, "
                f"role={user_info['role']}"
            )
            
            return user_info
            
        except Exception as ex:
            logger.error(f"Token validation failed: {ex}", exc_info=True)
            return None
    
    def _extract_role(self, claims: dict) -> str:
        """
        Extract user role from Scalekit token claims.
        
        Scalekit tokens include roles in the 'roles' claim.
        We map Scalekit roles to our internal roles (student, teacher, admin).
        
        Args:
            claims: JWT token claims
            
        Returns:
            User's role (defaults to 'student' if not found)
        """
        roles = claims.get("roles", [])
        
        # If multiple roles, use highest privilege
        if "admin" in roles:
            return "admin"
        elif "teacher" in roles:
            return "teacher"
        elif "student" in roles:
            return "student"
        
        # Default to student for authenticated users
        logger.warning(f"No recognized role in token, defaulting to student. Roles: {roles}")
        return "student"


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
