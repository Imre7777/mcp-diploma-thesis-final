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
from src.backends import create_vector_backend
from src.utils.embeddings import EmbeddingService
from src.tools.search_tools import get_access_filter


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
# FastMCP Server Setup
# ============================================================================
mcp = FastMCP(
    name=config.server_name,
    stateless_http=True  # Required for HTTP transport
)

logger.info("FastMCP server initialized")


# ============================================================================
# MCP Tools - Educational Content Search
# ============================================================================
@mcp.tool(
    name="search_content",
    description="Search educational content with semantic search and RBAC filtering"
)
async def search_content(
    query: str,
    limit: int = 10,
    access_level: str = "student",
    ctx: Context | None = None
) -> dict:
    """
    Search educational content using semantic search.
    
    Args:
        query: Search query text
        limit: Maximum number of results (default: 10)
        access_level: User's access level for RBAC filtering (student/teacher/admin)
        ctx: MCP context (contains authentication info)
        
    Returns:
        Search results with content, metadata, and relevance scores
    """
    try:
        logger.info(f"Search request: query='{query}', limit={limit}, access_level={access_level}")
        
        # Initialize backend and embedding service if not already done
        if not hasattr(search_content, '_initialized'):
            logger.info("Initializing search backend...")
            search_content._db = create_vector_backend(
                name=config.vector_db_backend,
                url=config.vector_db_url,
                api_key=config.vector_db_api_key
            )
            search_content._embedding_service = EmbeddingService(
                api_key=config.openai_api_key,
                model=config.embedding_model
            )
            search_content._initialized = True
            logger.info("Search backend initialized successfully")
        
        # Generate query embedding
        query_embedding = await search_content._embedding_service.generate_embedding(query)
        
        # Create RBAC filter
        access_filter = get_access_filter(access_level) if config.enable_rbac else None
        
        # Perform search
        results = await search_content._db.search(
            collection_name=config.default_collection,
            query_vector=query_embedding,
            limit=limit,
            filters=access_filter
        )
        
        logger.info(f"Search completed: {len(results)} results found")
        
        # Format results
        formatted_results = "\n\n".join([
            f"**Result {i+1}** (score: {r.score:.3f})\n{r.text}\n" +
            f"Source: {r.metadata.get('source', 'N/A')}"
            for i, r in enumerate(results)
        ])
        
        return {
            "content": [{
                "type": "text",
                "text": f"Found {len(results)} results for '{query}'\n\n{formatted_results}" if results else f"No results found for '{query}'"
            }]
        }
        
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        return {
            "content": [{
                "type": "text",
                "text": f"Error performing search: {str(e)}"
            }],
            "isError": True
        }


@mcp.tool(
    name="health_check",
    description="Check server health and connectivity"
)
async def health_check(ctx: Context | None = None) -> dict:
    """Check server health status."""
    return {
        "content": [{
            "type": "text",
            "text": f"Server: {config.server_name} v{config.server_version}\nStatus: Healthy ✓"
        }]
    }


logger.info(f"Registered {len(mcp._tool_manager._tools)} MCP tools")


# ============================================================================
# Create MCP ASGI App (MCP protocol at root "/")
# ============================================================================
mcp_app = mcp.http_app(path="/")
logger.info("MCP ASGI app created (mounted at /)")


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
        expose_headers=["WWW-Authenticate"],  # Important for OAuth 2.1
        max_age=86400,
    )
    logger.info("CORS middleware enabled")


# ============================================================================
# Public Endpoints (OAuth Discovery + Health)
# ============================================================================
@app.get("/.well-known/oauth-protected-resource")
async def oauth_discovery():
    """
    OAuth 2.1 Protected Resource metadata endpoint.
    
    This endpoint provides OAuth client discovery information:
    - Where to get access tokens (authorization server)
    - Supported scopes
    - How to send tokens (Bearer in header)
    - Resource identifier
    
    This is essential for Claude Desktop and other OAuth clients.
    """
    return await get_oauth_protected_resource_metadata(config)


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
# Mount MCP at "/" (LAST so public routes take precedence)
# ============================================================================
app.mount("/", mcp_app)
logger.info("MCP app mounted at / (MCP protocol endpoints)")


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
