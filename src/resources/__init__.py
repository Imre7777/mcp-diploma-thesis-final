"""
MCP Resources for LeoWiki Server

This package provides MCP resources that expose read-only data to LLM clients.
Resources help LLMs understand the structure and capabilities of the server.
"""

from .metadata import register_metadata_resources
from .content import register_content_resources

__all__ = [
    "register_metadata_resources",
    "register_content_resources",
]
