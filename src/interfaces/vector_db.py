"""
Abstract interface for vector databases.

This module defines the contract for vector database implementations,
ensuring consistent behavior across different vector database backends.
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """
    Standard search result format with validation.
    
    Attributes:
        id: Unique identifier for the document/chunk
        score: Similarity score (0.0 = dissimilar, 1.0+ = similar)
        payload: Document metadata including RBAC fields
        vector: Optional vector representation (if requested)
    """
    id: str = Field(..., description="Unique identifier for the result")
    score: float = Field(ge=0.0, le=2.0, description="Similarity score (0.0-2.0, cosine distance)")
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Document metadata including text, access_level, source, etc."
    )
    vector: list[float] | None = Field(
        None,
        description="Vector representation if requested (3072 dimensions for text-embedding-3-large)"
    )


class VectorDatabase(ABC):
    """
    Abstract interface for vector database operations.
    
    This interface ensures consistency across different vector database backends
    (Qdrant, Pinecone, Weaviate, etc.) and enables easy swapping of backends
    without changing the MCP server code.
    """
    
    @abstractmethod
    def __init__(self, url: str, api_key: str | None = None):
        """
        Initialize the vector database client.
        
        Args:
            url: Database connection URL
            api_key: Optional API key for authentication
        """
        pass
    
    @abstractmethod
    def ping(self) -> dict[str, Any]:
        """
        Health check for the database.
        
        Returns:
            Dictionary with status information:
            - status: "healthy" or "unhealthy"
            - backend: Backend type (e.g., "qdrant")
            - collections_count: Number of collections
            - error: Error message if unhealthy
        """
        pass
    
    @abstractmethod
    def list_collections(self) -> list[str]:
        """
        List all available collections in the database.
        
        Returns:
            List of collection names
        """
        pass
    
    @abstractmethod
    def get_point(self, collection: str, point_id: str) -> SearchResult | None:
        """
        Retrieve a specific point by ID.
        
        Args:
            collection: Collection name
            point_id: Unique point identifier
            
        Returns:
            SearchResult if found, None otherwise
        """
        pass
    
    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        collection: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
        score_threshold: float | None = None,
        with_payload: bool = True,
        with_vectors: bool = False
    ) -> list[SearchResult]:
        """
        Search for similar vectors with optional RBAC filters.
        
        Args:
            query_vector: Query embedding vector (3072 dimensions for text-embedding-3-large)
            collection: Collection name to search in
            limit: Maximum number of results to return
            filters: Optional filters (e.g., {"access_level": {"$in": ["public", "student"]}})
            score_threshold: Minimum similarity score (0.0-1.0)
            with_payload: Include payload in results
            with_vectors: Include vectors in results
            
        Returns:
            List of SearchResult objects sorted by similarity score
        """
        pass
    
    @abstractmethod 
    def count(self, collection: str, filters: dict[str, Any] | None = None) -> int:
        """
        Count points in collection with optional filters.
        
        Args:
            collection: Collection name
            filters: Optional filters (e.g., {"access_level": "public"})
            
        Returns:
            Number of points matching the filters
        """
        pass
    
    def validate_filters(self, filters: dict[str, Any] | None) -> dict[str, Any] | None:
        """
        Validate and normalize filter format.
        
        This method can be overridden in implementations for backend-specific
        filter validation and conversion.
        
        Args:
            filters: Filter dictionary (Qdrant-style filters)
            
        Returns:
            Validated filter dictionary or None
            
        Raises:
            ValueError: If filters are invalid
        """
        if not filters:
            return None
        
        # Basic validation - ensure filters is a dictionary
        if not isinstance(filters, dict):
            raise ValueError("Filters must be a dictionary")
        
        return filters
    
    def apply_score_threshold(
        self,
        results: list[SearchResult],
        threshold: float | None
    ) -> list[SearchResult]:
        """
        Apply score threshold filtering after search.
        
        This method can be overridden for backend-specific filtering,
        but provides a default implementation for backends that don't
        support score_threshold natively.
        
        Args:
            results: Search results to filter
            threshold: Minimum score threshold
            
        Returns:
            Filtered results above threshold
        """
        if threshold is None:
            return results
        
        return [r for r in results if r.score >= threshold]
