"""
Vector database backend implementations.

This module contains concrete implementations of the VectorDatabase interface
for various vector database backends.
"""

from typing import Optional
from .qdrant import QdrantBackend


def create_vector_backend(
    name: str = "qdrant",
    url: str = "http://localhost:6334",
    api_key: Optional[str] = None,
    **kwargs
):
    """
    Create a vector database backend instance.
    
    Args:
        name: Backend name ("qdrant" is currently the only supported backend)
        url: Backend URL
        api_key: Optional API key for authentication
        **kwargs: Additional backend-specific arguments
        
    Returns:
        Vector database backend instance
        
    Raises:
        ValueError: If backend name is not supported
    """
    if name.lower() == "qdrant":
        return QdrantBackend(url=url, api_key=api_key, **kwargs)
    else:
        raise ValueError(f"Unsupported vector backend: {name}")


__all__ = ["QdrantBackend", "create_vector_backend"]
