"""
OAuth 2.1 Protected Resource Metadata Handler

This module implements the OAuth 2.1 protected resource metadata endpoint
(/.well-known/oauth-protected-resource) that provides OAuth client discovery
information for Scalekit authentication.

This endpoint is essential for Claude Desktop and other OAuth clients to
discover how to authenticate with this MCP server.

Specification: RFC 8414 (OAuth 2.0 Authorization Server Metadata)
Extended for: OAuth 2.1 Protected Resource Pattern

Reference: https://docs.scalekit.com/authenticate/mcp/quickstart/
"""

import json
import logging
from typing import Dict, Any
from fastapi import Response
from src.config.server_config import ServerConfig

logger = logging.getLogger(__name__)


async def get_oauth_protected_resource_metadata(config: ServerConfig) -> Response:
    """
    Return OAuth 2.1 Protected Resource metadata for client discovery.
    
    This endpoint provides:
    - Authorization server URL (where to get tokens)
    - Supported scopes (what permissions are available)
    - Bearer token methods (how to send tokens)
    - Resource identifier (this MCP server)
    
    The metadata is either:
    1. Custom JSON from PROTECTED_RESOURCE_METADATA env var (from Scalekit dashboard)
    2. Auto-generated default metadata
    
    Args:
        config: Server configuration with Scalekit settings
        
    Returns:
        JSON response with OAuth 2.1 metadata
    """
    
    try:
        logger.info("OAuth protected resource metadata requested")
        
        # Option 1: Use custom metadata from Scalekit dashboard (RECOMMENDED)
        if config.scalekit_protected_resource_metadata:
            logger.info("Using custom OAuth metadata from PROTECTED_RESOURCE_METADATA")
            try:
                metadata = json.loads(config.scalekit_protected_resource_metadata)
                logger.debug(f"OAuth metadata: {json.dumps(metadata, indent=2)}")
                
                return Response(
                    content=json.dumps(metadata, indent=2),
                    media_type="application/json",
                    status_code=200
                )
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in PROTECTED_RESOURCE_METADATA: {e}")
                return Response(
                    content=json.dumps({
                        "error": "invalid_metadata",
                        "error_description": "PROTECTED_RESOURCE_METADATA contains invalid JSON"
                    }),
                    media_type="application/json",
                    status_code=500
                )
        
        # Option 2: Auto-generate metadata (FALLBACK - NOT RECOMMENDED for production)
        logger.warning("PROTECTED_RESOURCE_METADATA not set, generating default metadata")
        logger.warning("For production, copy metadata from Scalekit dashboard!")
        
        metadata = _generate_default_metadata(config)
        
        return Response(
            content=json.dumps(metadata, indent=2),
            media_type="application/json",
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Failed to generate OAuth metadata: {e}", exc_info=True)
        return Response(
            content=json.dumps({
                "error": "server_error",
                "error_description": "Failed to generate OAuth metadata"
            }),
            media_type="application/json",
            status_code=500
        )


def _generate_default_metadata(config: ServerConfig) -> Dict[str, Any]:
    """
    Generate default OAuth 2.1 Protected Resource metadata.
    
    This is a FALLBACK for development. In production, you should:
    1. Create an MCP Server in Scalekit dashboard
    2. Copy the PROTECTED_RESOURCE_METADATA JSON
    3. Set it in your environment variables
    
    Args:
        config: Server configuration
        
    Returns:
        Default OAuth metadata dictionary
    """
    return {
        "resource": config.scalekit_mcp_server_id or "mcp-edu-server",
        "authorization_servers": [
            config.scalekit_env_url
        ],
        "bearer_methods_supported": [
            "header"
        ],
        "resource_signing_alg_values_supported": [
            "RS256"
        ],
        "scopes_supported": [
            "mcp:read",
            "mcp:write",
            "usr:read",
            "usr:write"
        ],
        "resource_documentation": f"http://localhost:{config.server_port}/docs"
    }


def validate_metadata_configuration(config: ServerConfig) -> bool:
    """
    Validate that OAuth metadata is properly configured.
    
    Args:
        config: Server configuration
        
    Returns:
        True if metadata is properly configured, False otherwise
    """
    if not config.scalekit_protected_resource_metadata:
        config.logger.warning(
            "PROTECTED_RESOURCE_METADATA not set. "
            "For production, copy JSON from Scalekit dashboard."
        )
        return False
    
    try:
        metadata = json.loads(config.scalekit_protected_resource_metadata)
        
        # Validate required fields
        required_fields = [
            "resource",
            "authorization_servers",
            "bearer_methods_supported"
        ]
        
        for field in required_fields:
            if field not in metadata:
                config.logger.error(f"Missing required field in metadata: {field}")
                return False
        
        config.logger.info("OAuth metadata configuration valid")
        return True
        
    except json.JSONDecodeError as e:
        config.logger.error(f"Invalid JSON in PROTECTED_RESOURCE_METADATA: {e}")
        return False
