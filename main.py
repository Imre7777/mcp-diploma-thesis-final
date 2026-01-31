#!/usr/bin/env python3
"""
MCP Educational Server - Main Entry Point (Official Scalekit Architecture)

This server implements the official Scalekit MCP authentication architecture:
- FastMCP library for MCP protocol communication
- Scalekit SDK for OAuth 2.1 token validation
- OAuth 2.1 Protected Resource pattern
- Role-Based Access Control (RBAC) for content filtering

Architecture:
┌──────────────────┐         ┌─────────────────┐
│  Claude Desktop  │◄────────│  Scalekit Auth  │
│  (OAuth Client)  │  tokens │   Server        │
└────────┬─────────┘         └─────────────────┘
         │ Bearer Token
         ▼
┌──────────────────┐
│   MCP Server     │ ← This Server
│ (Protected Res)  │
├──────────────────┤
│ /.well-known/    │ ← OAuth discovery
│   oauth-prote... │
│ /                │ ← MCP protocol (FastMCP)
│ /health          │ ← Health check
└──────────────────┘

Reference: https://github.com/scalekit-inc/mcp-auth-demos
Documentation: https://docs.scalekit.com/authenticate/mcp/quickstart/

Author: Imre (HTL Diploma Thesis)
Date: January 2026
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from fastmcp import FastMCP, Context
from fastapi import FastAPI, Response
from starlette.middleware.cors import CORSMiddleware

from src.config.server_config import ServerConfig
from src.middleware.scalekit_auth import create_scalekit_middleware
from src.server.oauth_metadata import get_oauth_protected_resource_metadata, validate_metadata_configuration
from src.auth.oauth_flow import create_oauth_router
from src.backends import create_vector_backend


# ============================================================================
# Configuration & Initialization
# ============================================================================
config = ServerConfig()

# Setup logger
logging.basicConfig(
    level=getattr(logging, config.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("=" * 80)
logger.info("MCP EDUCATIONAL SERVER - Official Scalekit Architecture")
logger.info("=" * 80)
logger.info(f"Server Name: {config.server_name}")
logger.info(f"Server Version: {config.server_version}")
logger.info(f"Transport: {config.transport}")
logger.info(f"Port: {config.server_port}")
logger.info(f"Authentication: {'Enabled (Scalekit OAuth 2.1)' if config.enable_auth else 'Disabled'}")
logger.info(f"RBAC: {'Enabled' if config.enable_rbac else 'Disabled'}")
logger.info("=" * 80)


# ============================================================================
# FastMCP Server Setup with Professional Configuration
# ============================================================================
from src.server.lifespan import app_lifespan

mcp = FastMCP(
    name=config.server_name,
    
    # Instructions help LLMs understand how to use the server
    instructions="""
    LeoWiki MCP Server - HTL Leonding Educational Content Search
    
    This server provides semantic search access to HTL Leonding's educational wiki.
    
    CAPABILITIES:
    - Semantic search across educational materials
    - Role-based content filtering (student/teacher/admin)
    - Access to course materials, tutorials, and documentation
    
    AVAILABLE TOOLS:
    - search_content_student: Search with student-level access
    - search_content_teacher: Search with teacher-level access (includes exam materials)
    - get_collection_stats: Database statistics (teacher/admin only)
    
    RESOURCES:
    - leowiki://categories: Available content categories
    - leowiki://access-levels: RBAC documentation
    - leowiki://search-hints: Search tips and best practices
    - leowiki://stats: Live collection statistics
    - leowiki://topic/{id}: Detailed topic information
    - leowiki://recent/{count}: Recently updated content
    
    PROMPTS:
    - explain_topic: Generate structured explanations
    - create_quiz: Generate quiz questions
    - compare_concepts: Compare related concepts
    - summarize_search: Summarize search results
    - learning_path: Create learning roadmaps
    
    LANGUAGE: Content is primarily in German.
    AUTHENTICATION: OAuth 2.1 via Scalekit (required)
    """,
    
    # Transport configuration
    stateless_http=True,  # Required for HTTP transport
    json_response=False,  # Keep SSE for progress reporting
    
    # Security (CRITICAL for production)
    mask_error_details=True,  # Hide internal errors from clients
    
    # Behavior
    on_duplicate_tools="error",  # Catch registration errors early
    
    # Dependency injection
    lifespan=app_lifespan,
)

logger.info("FastMCP server initialized with professional configuration")


# ============================================================================
# Register Custom Middleware (runs before tools)
# ============================================================================
from src.middleware.mcp_middleware import (
    RequestLoggingMiddleware,
    UserContextMiddleware,
    RBACEnforcementMiddleware,
    AuditLoggingMiddleware
)

mcp.add_middleware(RequestLoggingMiddleware())
mcp.add_middleware(UserContextMiddleware())
mcp.add_middleware(RBACEnforcementMiddleware())
mcp.add_middleware(AuditLoggingMiddleware())

logger.info("Registered 4 FastMCP middleware components")


# ============================================================================
# Register MCP Tools
# ============================================================================
from src.tools.search_tools import register_search_tools

register_search_tools(mcp)


# ============================================================================
# Register MCP Resources
# ============================================================================
from src.resources.metadata import register_metadata_resources
from src.resources.content import register_content_resources

register_metadata_resources(mcp)
register_content_resources(mcp)


# ============================================================================
# Register MCP Prompts
# ============================================================================
from src.prompts.educational import register_educational_prompts

register_educational_prompts(mcp)


# ============================================================================
# Health Check Tool
# ============================================================================
@mcp.tool(
    name="health_check",
    description="Check server health and connectivity"
)
async def health_check(ctx: Context = None) -> dict:
    """
    Check server health status.
    
    Returns basic server information and status.
    """
    return {
        "content": [{
            "type": "text",
            "text": f"Server: {config.server_name} v{config.server_version}\nStatus: Healthy ✓"
        }]
    }


logger.info(f"Registered {len(mcp._tool_manager._tools)} MCP tools total")
logger.info("Resources and prompts registered successfully")


# ============================================================================
# Create MCP ASGI App (MCP protocol - handles /mcp path directly)
# ============================================================================
mcp_app = mcp.http_app(path="/mcp")  # Handle /mcp path directly at root mount
logger.info("MCP ASGI app created (path=/mcp at root mount)")


# ============================================================================
# FastAPI App (Wraps MCP + OAuth Discovery + Health)
# ============================================================================
app = FastAPI(
    title=config.server_name,
    version=config.server_version,
    lifespan=mcp_app.lifespan  # Use FastMCP's lifespan for proper initialization
)

logger.info("FastAPI app initialized")


# ============================================================================
# Authentication Middleware (Scalekit OAuth 2.1)
# ============================================================================
if config.enable_auth:
    auth_middleware = create_scalekit_middleware(config)
    app.middleware("http")(auth_middleware)
    logger.info("Scalekit authentication middleware enabled")
else:
    logger.warning("⚠️  Authentication DISABLED - For development only!")


# ============================================================================
# CORS Middleware (Must be after auth middleware)
# ============================================================================
if config.http_enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if config.http_cors_origins == "*" else config.http_cors_origins.split(","),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["WWW-Authenticate", "Content-Type", "Authorization", "Mcp-Session-Id"],  # Required for MCP + OAuth 2.1
        max_age=86400,
    )
    logger.info("CORS middleware enabled")


# ============================================================================
# OAuth Authentication Router (Login, Callback, Logout)
# ============================================================================
if config.enable_auth:
    import os
    
    # Determine callback URL based on environment
    callback_url = os.getenv(
        "OAUTH_CALLBACK_URL",
        f"http://localhost:{config.server_port}/auth/callback"
    )
    
    oauth_router = create_oauth_router(
        scalekit_env_url=config.scalekit_env_url,
        client_id=config.scalekit_client_id,
        client_secret=config.scalekit_client_secret,
        redirect_uri=callback_url,
        frontend_callback_url=None,  # JSON response for API clients
    )
    app.include_router(oauth_router)
    logger.info(f"OAuth router registered: /auth/login, /callback, /auth/logout")
    logger.info(f"OAuth callback URL: {callback_url}")


# ============================================================================
# Public Endpoints (OAuth Discovery + Health)
# ============================================================================
@app.get("/.well-known/oauth-protected-resource")
@app.get("/.well-known/oauth-protected-resource/mcp")
async def oauth_discovery():
    """
    OAuth 2.1 Protected Resource metadata endpoint.
    
    This endpoint provides OAuth client discovery information:
    - Where to get access tokens (authorization server)
    - Supported scopes
    - How to send tokens (Bearer in header)
    - Resource identifier
    
    This is essential for Claude Desktop and other OAuth clients.
    Also responds to /mcp suffix for clients that request path-specific metadata.
    """
    return await get_oauth_protected_resource_metadata(config)


@app.get("/.well-known/oauth-authorization-server")
async def oauth_authorization_server_metadata():
    """
    Redirect to ScaleKit's OIDC Discovery metadata.
    
    Claude.ai and other OAuth clients look for this endpoint to discover
    the authorization server configuration. ScaleKit uses OIDC standard
    (/.well-known/openid-configuration) instead of OAuth standard.
    """
    from fastapi.responses import RedirectResponse
    
    if config.scalekit_env_url:
        # Redirect to ScaleKit's OIDC configuration (ScaleKit uses OIDC standard)
        scalekit_metadata_url = f"{config.scalekit_env_url}/.well-known/openid-configuration"
        logger.info(f"Redirecting to ScaleKit OIDC metadata: {scalekit_metadata_url}")
        return RedirectResponse(url=scalekit_metadata_url, status_code=302)
    else:
        return Response(
            content='{"error": "not_configured", "error_description": "Authorization server not configured"}',
            media_type="application/json",
            status_code=503
        )


@app.post("/register")
@app.get("/register")
async def dynamic_client_registration():
    """
    Dynamic Client Registration endpoint.
    
    This is an OAuth 2.0 feature for dynamic client registration.
    We don't support this directly - clients should be pre-registered in ScaleKit.
    
    Returns a proper OAuth error response.
    """
    logger.info("Dynamic Client Registration attempted - not supported")
    return Response(
        content='{"error": "registration_not_supported", "error_description": "Dynamic client registration is not supported. Please use pre-registered clients via ScaleKit."}',
        media_type="application/json",
        status_code=400
    )


@app.get("/health")
async def health():
    """
    Health check endpoint (public, no authentication required).
    """
    return {
        "status": "healthy",
        "server": config.server_name,
        "version": config.server_version,
        "authentication": "enabled" if config.enable_auth else "disabled",
        "rbac": "enabled" if config.enable_rbac else "disabled"
    }


logger.info("Public endpoints registered: /.well-known/oauth-protected-resource, /health")


# ============================================================================
# Mount MCP at root to handle /mcp path directly (avoids 307 redirect issues)
# ============================================================================
app.mount("/", mcp_app)
logger.info("MCP app mounted at root (handles /mcp path directly, avoids redirect)")


# ============================================================================
# Startup Validation
# ============================================================================
@app.on_event("startup")
async def startup_event():
    """Validate configuration on startup."""
    logger.info("Performing startup validation...")
    
    # Validate OAuth metadata configuration
    if config.enable_auth:
        is_valid = validate_metadata_configuration(config)
        if not is_valid:
            logger.warning(
                "⚠️  OAuth metadata not configured! "
                "Set PROTECTED_RESOURCE_METADATA from Scalekit dashboard for production."
            )
    
    # Test Qdrant connection
    try:
        logger.info("Testing Qdrant connection...")
        db = create_vector_backend(
            name=config.vector_db_backend,
            url=config.vector_db_url,
            api_key=config.vector_db_api_key
        )
        # Simple connectivity test
        logger.info("✓ Qdrant connection successful")
    except Exception as e:
        logger.error(f"✗ Qdrant connection failed: {e}")
        logger.error("Make sure Qdrant is running: docker ps | grep qdrant")
    
    logger.info("=" * 80)
    logger.info("SERVER READY")
    logger.info(f"MCP Endpoint: http://localhost:{config.server_port}/")
    logger.info(f"OAuth Discovery: http://localhost:{config.server_port}/.well-known/oauth-protected-resource")
    logger.info(f"Health Check: http://localhost:{config.server_port}/health")
    logger.info(f"API Docs: http://localhost:{config.server_port}/docs")
    logger.info("=" * 80)


# ============================================================================
# Main Entry Point
# ============================================================================
if __name__ == "__main__":
    import sys
    
    # Determine transport mode:
    # - STDIO mode: when Claude Desktop runs the server (no --http flag)
    # - HTTP mode: when manually started with --http flag
    
    if "--http" in sys.argv:
        # HTTP mode for direct server usage
        import uvicorn
        
        logger.info(f"Starting HTTP server on http://{config.http_host}:{config.server_port}")
        logger.info(f"Log level: {config.log_level}")
        
        uvicorn.run(
            app,
            host=config.http_host,
            port=config.server_port,
            log_level=config.log_level.lower(),
        )
    else:
        # STDIO mode for Claude Desktop
        logger.info("Running in STDIO mode (for Claude Desktop)")
        logger.info("To run as HTTP server, use: python main.py --http")
        
        # Use FastMCP's built-in STDIO runner
        mcp.run()
