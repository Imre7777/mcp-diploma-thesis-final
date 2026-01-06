"""
MCP Educational Server - Server Components

This package contains the core server implementation for the MCP Educational Server,
including OAuth metadata handlers for the official Scalekit architecture.

Note: The old http_server.py and base.py are deprecated.
We now use FastMCP library in main.py instead of custom server implementation.
"""

# OAuth metadata handler (new official architecture)
from src.server.oauth_metadata import (
    get_oauth_protected_resource_metadata,
    validate_metadata_configuration
)

__all__ = [
    "get_oauth_protected_resource_metadata",
    "validate_metadata_configuration",
]
