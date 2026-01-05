"""
Database interfaces for MCP Educational Server.

This module defines abstract interfaces for vector databases and other storage backends.
"""

from .vector_db import SearchResult, VectorDatabase

__all__ = ["SearchResult", "VectorDatabase"]
