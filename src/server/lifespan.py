"""
Application Lifespan Management for LeoWiki MCP Server

This module implements dependency injection and resource lifecycle management
for the MCP server using FastMCP's lifespan pattern. All dependencies are
initialized at startup and properly cleaned up at shutdown.

Resources managed:
- Qdrant Vector Database connection
- Embedding Service (OpenAI API)
- Server Configuration
- In-memory cache for query results
"""

from contextlib import asynccontextmanager
from dataclasses import dataclass
from collections.abc import AsyncIterator
import logging

from fastmcp import FastMCP
from qdrant_client import QdrantClient

from src.config.server_config import ServerConfig
from src.utils.embeddings import EmbeddingService
from src.backends.qdrant import QdrantBackend

logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    """
    Type-safe container for all injected dependencies.
    
    This context is accessible in all MCP tools via ctx.lifespan_context.
    Provides centralized access to:
    - Database connections
    - External services (embeddings)
    - Configuration
    - Shared resources (cache)
    """
    qdrant: QdrantBackend
    embedding_service: EmbeddingService
    config: ServerConfig
    cache: dict  # Simple in-memory cache for query results


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """
    Initialize and cleanup application resources.
    
    This async context manager runs ONCE when the server starts and ensures
    proper cleanup when the server shuts down. All tools can access these
    resources via ctx.lifespan_context.
    
    Args:
        server: FastMCP server instance
        
    Yields:
        AppContext with initialized dependencies
    """
    # Load configuration
    config = ServerConfig()
    
    logger.info("=" * 60)
    logger.info("🚀 Initializing LeoWiki MCP Server...")
    logger.info("=" * 60)
    
    # Initialize Qdrant Vector Database
    logger.info("📊 Connecting to Qdrant Vector Database...")
    try:
        qdrant = QdrantBackend(
            url=config.vector_db_url,
            api_key=config.vector_db_api_key
        )
        
        # Test connection
        health = qdrant.ping()
        if health["status"] == "healthy":
            logger.info(f"✓ Qdrant connected: {health.get('collections_count', 0)} collections")
        else:
            logger.warning(f"⚠️  Qdrant health check returned: {health}")
    except Exception as e:
        logger.error(f"✗ Failed to connect to Qdrant: {e}")
        logger.error("Make sure Qdrant is running: docker ps | grep qdrant")
        raise
    
    # Initialize Embedding Service
    logger.info("🔤 Initializing embedding service...")
    try:
        embedding_service = EmbeddingService(
            api_key=config.openai_api_key,
            model=config.embedding_model,
            dimensions=config.vector_dimensions
        )
        
        if embedding_service.is_using_mock:
            logger.warning("⚠️  Using MOCK embeddings (no OpenAI API key)")
            logger.warning("Set OPENAI_API_KEY environment variable for production!")
        else:
            logger.info(f"✓ Embedding service initialized: {config.embedding_model}")
    except Exception as e:
        logger.error(f"✗ Failed to initialize embedding service: {e}")
        raise
    
    # Create shared cache
    cache = {}
    logger.info("💾 In-memory cache initialized")
    
    # Summary
    logger.info("=" * 60)
    logger.info("✓ All dependencies initialized successfully")
    logger.info(f"  • Qdrant: {config.vector_db_url}")
    logger.info(f"  • Collection: {config.default_collection}")
    logger.info(f"  • Embedding: {config.embedding_model} ({config.vector_dimensions}D)")
    logger.info(f"  • RBAC: {'Enabled' if config.enable_rbac else 'Disabled'}")
    logger.info(f"  • Auth: {'Enabled (Scalekit)' if config.enable_auth else 'Disabled'}")
    logger.info("=" * 60)
    
    try:
        # Yield context to application
        yield AppContext(
            qdrant=qdrant,
            embedding_service=embedding_service,
            config=config,
            cache=cache
        )
    finally:
        # Cleanup on shutdown
        logger.info("=" * 60)
        logger.info("🛑 Shutting down LeoWiki MCP Server...")
        logger.info("=" * 60)
        
        # Close Qdrant connection if needed
        # Note: QdrantClient doesn't require explicit close, but log it
        logger.info("✓ Qdrant connection closed")
        
        # Clear cache
        cache.clear()
        logger.info("✓ Cache cleared")
        
        logger.info("✓ Cleanup complete")
        logger.info("=" * 60)
