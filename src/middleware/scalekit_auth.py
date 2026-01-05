"""
Scalekit OAuth 2.1 Authentication Middleware

This module implements OAuth 2.1 authentication middleware using the official
Scalekit SDK. It validates Bearer tokens for all MCP requests according to the
OAuth 2.1 Protected Resource specification.

Architecture:
- MCP Server acts as an OAuth 2.1 Protected Resource
- Claude Desktop (or other OAuth clients) handle the OAuth flow
- This middleware validates Bearer tokens using Scalekit SDK
- Returns proper WWW-Authenticate headers for OAuth 2.1 compliance

Reference: https://github.com/scalekit-inc/mcp-auth-demos
"""

from typing import Callable
from fastapi import Request, Response
from scalekit import ScalekitClient
from scalekit.common.scalekit import TokenValidationOptions

from src.config.server_config import ServerConfig


class ScalekitAuthMiddleware:
    """
    Middleware for Scalekit OAuth 2.1 token validation.
    
    Validates Bearer tokens on all protected endpoints, returning proper
    OAuth 2.1 error responses with WWW-Authenticate headers.
    """
    
    def __init__(self, config: ServerConfig):
        """
        Initialize the Scalekit authentication middleware.
        
        Args:
            config: Server configuration with Scalekit credentials
        """
        self.config = config
        self.logger = config.logger
        
        # Initialize Scalekit client
        try:
            self.scalekit_client = ScalekitClient(
                env_url=config.scalekit_env_url,
                client_id=config.scalekit_client_id,
                client_secret=config.scalekit_client_secret
            )
            self.scalekit_available = True
            self.logger.info("Scalekit client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Scalekit client: {e}")
            self.scalekit_client = None
            self.scalekit_available = False
        
        # OAuth 2.1 WWW-Authenticate header
        self.www_authenticate_header = {
            "WWW-Authenticate": (
                f'Bearer realm="OAuth", '
                f'resource_metadata="http://localhost:{config.server_port}/.well-known/oauth-protected-resource"'
            )
        }
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """
        Middleware callable that validates Bearer tokens.
        
        Args:
            request: Incoming FastAPI request
            call_next: Next middleware/route handler
            
        Returns:
            Response with appropriate status code and headers
        """
        try:
            # Log request for debugging
            self.logger.debug(
                f"Auth check: {request.method} {request.url.path}",
                headers=dict(request.headers)
            )
            
            # Allow public access to OAuth discovery and health endpoints
            if self._is_public_endpoint(request.url.path):
                self.logger.debug(f"Public endpoint: {request.url.path}")
                return await call_next(request)
            
            # Extract Bearer token
            auth_header = request.headers.get("authorization", "")
            
            if not auth_header.startswith("Bearer "):
                self.logger.warning(f"Missing Bearer token for {request.url.path}")
                return Response(
                    content='{"error": "invalid_token", "error_description": "Missing Bearer token"}',
                    media_type="application/json",
                    status_code=401,
                    headers=self.www_authenticate_header
                )
            
            token = auth_header.split("Bearer ", 1)[1].strip()
            
            if not token:
                self.logger.warning(f"Empty Bearer token for {request.url.path}")
                return Response(
                    content='{"error": "invalid_token", "error_description": "Empty Bearer token"}',
                    media_type="application/json",
                    status_code=401,
                    headers=self.www_authenticate_header
                )
            
            # Validate token with Scalekit SDK
            if not self.scalekit_available:
                self.logger.error("Scalekit SDK not available for token validation")
                return Response(
                    content='{"error": "server_error", "error_description": "Authentication service unavailable"}',
                    media_type="application/json",
                    status_code=503,
                    headers=self.www_authenticate_header
                )
            
            try:
                # Configure token validation options
                validation_options = TokenValidationOptions(
                    issuer=self.config.scalekit_env_url,
                    audience=[self.config.scalekit_expected_audience]
                )
                
                # Validate access token using Scalekit SDK
                is_valid = self.scalekit_client.validate_access_token(
                    token,
                    options=validation_options
                )
                
                if not is_valid:
                    self.logger.warning(f"Invalid token for {request.url.path}")
                    return Response(
                        content='{"error": "invalid_token", "error_description": "Token validation failed"}',
                        media_type="application/json",
                        status_code=401,
                        headers=self.www_authenticate_header
                    )
                
                self.logger.info(f"Token validated successfully for {request.url.path}")
                
                # Token is valid, proceed to next handler
                return await call_next(request)
                
            except Exception as e:
                self.logger.error(f"Token validation error: {e}", exc_info=True)
                return Response(
                    content='{"error": "invalid_token", "error_description": "Token validation failed"}',
                    media_type="application/json",
                    status_code=401,
                    headers=self.www_authenticate_header
                )
        
        except Exception as e:
            self.logger.error(f"Authentication middleware error: {e}", exc_info=True)
            return Response(
                content='{"error": "server_error", "error_description": "Authentication failed"}',
                media_type="application/json",
                status_code=500,
                headers=self.www_authenticate_header
            )
    
    def _is_public_endpoint(self, path: str) -> bool:
        """
        Check if an endpoint is public (does not require authentication).
        
        Args:
            path: Request path
            
        Returns:
            True if endpoint is public, False otherwise
        """
        public_paths = [
            "/.well-known/oauth-protected-resource",
            "/health",
            "/docs",  # FastAPI docs (optional, can be protected)
            "/openapi.json",  # FastAPI OpenAPI spec
        ]
        
        return any(path.startswith(public_path) for public_path in public_paths)


def create_scalekit_middleware(config: ServerConfig) -> ScalekitAuthMiddleware:
    """
    Factory function to create Scalekit authentication middleware.
    
    Args:
        config: Server configuration
        
    Returns:
        Configured ScalekitAuthMiddleware instance
    """
    return ScalekitAuthMiddleware(config)
