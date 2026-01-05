"""
OAuth 2.0 Protected Resource Metadata Endpoint

This module implements the .well-known endpoint for MCP OAuth discovery as per
the Scalekit MCP Server specification.

Reference: https://docs.scalekit.com/mcp-servers
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Response

logger = logging.getLogger(__name__)

# OAuth 2.0 Protected Resource Metadata
# This is served at: /.well-known/oauth-protected-resource/<mcp-resource-path>
def create_oauth_metadata_router(
    auth_server_url: str,
    mcp_resource_url: str,
    mcp_resource_id: str,
) -> APIRouter:
    """
    Create OAuth metadata router for MCP server discovery.
    
    This implements the OAuth 2.0 Protected Resource Metadata specification
    required by Scalekit for MCP server authentication.
    
    Args:
        auth_server_url: Scalekit authorization server URL
        mcp_resource_url: This MCP server's base URL
        mcp_resource_id: Scalekit MCP resource ID
        
    Returns:
        FastAPI router with .well-known endpoints
    """
    router = APIRouter(tags=["oauth-metadata"])
    
    @router.get(
        f"/.well-known/oauth-protected-resource/{mcp_resource_id}",
        response_model=Dict[str, Any],
        include_in_schema=False,
    )
    async def oauth_protected_resource_metadata():
        """
        OAuth 2.0 Protected Resource Metadata endpoint.
        
        This endpoint is required for MCP client discovery and authorization.
        It tells clients (like Claude Desktop) how to authenticate with this server.
        
        Returns:
            OAuth metadata JSON as per RFC 8414
        """
        metadata = {
            "resource": mcp_resource_url,
            "authorization_servers": [auth_server_url],
            "bearer_methods_supported": ["header"],
            "resource_documentation": f"{mcp_resource_url}/docs",
            "scopes_supported": [],  # We use role-based access, not scopes
        }
        
        logger.info(
            f"Serving OAuth metadata for resource {mcp_resource_id}: "
            f"auth_server={auth_server_url}"
        )
        
        return metadata
    
    @router.get(
        "/.well-known/oauth-authorization-server",
        response_model=Dict[str, Any],
        include_in_schema=False,
    )
    async def oauth_authorization_server_metadata():
        """
        OAuth 2.0 Authorization Server Metadata endpoint.
        
        This is a redirect/pointer to the Scalekit authorization server.
        Some OAuth clients may look for this endpoint.
        
        Returns:
            Redirect information to Scalekit auth server
        """
        return {
            "issuer": auth_server_url,
            "authorization_endpoint": f"{auth_server_url}/authorize",
            "token_endpoint": f"{auth_server_url}/token",
            "jwks_uri": f"{auth_server_url}/.well-known/jwks.json",
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code"],
            "token_endpoint_auth_methods_supported": ["client_secret_post"],
        }
    
    return router
