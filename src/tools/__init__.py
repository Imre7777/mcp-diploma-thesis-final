"""
MCP Tools Package

This package contains all MCP tools for the Educational Server,
organized by functionality and supporting role-based access control.
"""

from src.tools.search_tools import register_search_tools

__all__ = [
    "register_search_tools",
    "register_all_tools",
]


def register_all_tools(mcp, db, embedding_service, config=None):
    """
    Register all MCP tools with the FastMCP server.

    Args:
        mcp: FastMCP server instance
        db: Vector database instance
        embedding_service: Embedding service for query vectorization
        config: Server configuration instance
    """
    # Register search tools with RBAC support
    register_search_tools(mcp, db, embedding_service, config)
    
    # Future: Register additional tool categories
    # - Document management tools
    # - Content filtering tools
    # - Analytics tools
