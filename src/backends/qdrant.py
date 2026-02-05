"""
Qdrant vector database implementation with RBAC filtering support.

This module provides a production-ready Qdrant client with:
- Robust error handling and logging
- RBAC filter validation
- Health checking
- Support for named and unnamed vectors
- Efficient scroll operations
"""

from __future__ import annotations

import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from qdrant_client.http.exceptions import ResponseHandlingException

# Import fallbacks for different import contexts
try:
    from interfaces.vector_db import SearchResult, VectorDatabase
except ImportError:
    from ..interfaces.vector_db import SearchResult, VectorDatabase

logger = logging.getLogger(__name__)


class QdrantBackend(VectorDatabase):
    """
    Qdrant implementation of the VectorDatabase interface.
    
    This implementation supports:
    - Vector similarity search with RBAC filters
    - Collection management and health checks
    - Point retrieval and counting
    - Efficient scrolling for large result sets
    - Robust error handling with logging
    """

    def __init__(self, url: str, api_key: str | None = None):
        """
        Initialize Qdrant client.
        
        Args:
            url: Qdrant server URL (e.g., "http://localhost:6333")
            api_key: Optional API key for Qdrant Cloud
        """
        self.url = url
        self.api_key = api_key
        self.client = QdrantClient(url=url, api_key=api_key)
        logger.info(f"Initialized Qdrant client for {url}")

    # ========================================================================
    # Filter Validation
    # ========================================================================
    def validate_filters(self, filters: dict[str, Any] | None) -> rest.Filter | None:
        """
        Validate and convert filter dict to Qdrant Filter model.
        
        This method ensures filters are properly formatted for Qdrant's API
        and converts them to the appropriate Pydantic model.
        
        Args:
            filters: Plain dict filters (e.g., {"must": [{"key": "access_level", "match": {"value": "public"}}]})
            
        Returns:
            Qdrant Filter model or None if no filters
        """
        if not filters:
            return None
        
        try:
            # Use parent class validation first
            validated = super().validate_filters(filters)
            if not validated:
                return None
            
            # Convert to Qdrant's Filter model
            return rest.Filter.model_validate(validated)
        
        except Exception as e:
            logger.warning(f"Invalid filter format, ignoring filters: {e}")
            return None

    # ========================================================================
    # Health & Metadata Operations
    # ========================================================================
    def ping(self) -> dict[str, Any]:
        """
        Health check for Qdrant database.
        
        Returns:
            Dictionary with health status:
            - status: "healthy" or "unhealthy"
            - backend: "qdrant"
            - url: Connection URL
            - collections_count: Number of collections
            - error: Error message if unhealthy
        """
        try:
            cols = self.client.get_collections()
            return {
                "status": "healthy",
                "backend": "qdrant",
                "collections_count": len(cols.collections),
            }
        except Exception as e:
            # Log full error server-side, return generic message
            logger.error(f"Qdrant health check failed: {e}")
            return {
                "status": "unhealthy",
                "backend": "qdrant",
                "message": "Datenbank vorübergehend nicht erreichbar"
            }

    def list_collections(self) -> list[str]:
        """
        List all collections in Qdrant.
        
        Returns:
            List of collection names, empty list on error
        """
        try:
            cols = self.client.get_collections()
            collection_names = [c.name for c in cols.collections]
            logger.debug(f"Found {len(collection_names)} collections: {collection_names}")
            return collection_names
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []

    def get_point(self, collection: str, point_id: str) -> SearchResult | None:
        """
        Retrieve a specific point by ID.
        
        Args:
            collection: Collection name
            point_id: Point ID to retrieve
            
        Returns:
            SearchResult with point data, or None if not found
        """
        try:
            if not collection or not point_id:
                logger.warning("Empty collection name or point_id provided to get_point")
                return None
            
            res = self.client.retrieve(
                collection_name=collection,
                ids=[point_id],
                with_payload=True,
                with_vectors=True,
            )
            
            if not res:
                logger.debug(f"Point {point_id} not found in {collection}")
                return None
            
            p = res[0]
            
            # Extract vector (handle both named and unnamed vectors)
            vec = None
            if getattr(p, "vector", None) is not None:
                if isinstance(p.vector, dict) and "text" in p.vector:
                    vec = p.vector["text"]
                elif isinstance(p.vector, list):
                    vec = p.vector
            
            return SearchResult(
                id=str(p.id),
                score=1.0,  # Retrieved points don't have similarity score
                payload=p.payload or {},
                vector=vec
            )
        
        except ResponseHandlingException as e:
            logger.error(f"Qdrant response error in get_point: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get point {point_id} from {collection}: {e}")
            return None

    # ========================================================================
    # Core Search Operations
    # ========================================================================
    def search(
        self,
        query_vector: Any,
        collection: str,
        limit: int = 10,
        score_threshold: float | None = None,
        with_payload: bool = True,
        with_vectors: bool = False,
        filters: dict[str, Any] | None = None,
    ):
        """
        Vector similarity search with RBAC filtering.
        
        This method supports collections with unnamed vectors (default Qdrant setup)
        and applies RBAC filters for role-based content access control.
        
        Args:
            query_vector: Query embedding (list of floats or dict with "text" key)
            collection: Collection name to search in
            limit: Maximum number of results
            score_threshold: Minimum similarity score (0.0-1.0)
            with_payload: Include payload in results
            with_vectors: Include vectors in results
            filters: RBAC filters (e.g., {"must": [{"key": "access_level", "match": {"any": ["public", "student"]}}]})
            
        Returns:
            List of search results from Qdrant
        """
        # Step 1: Normalize query vector
        if isinstance(query_vector, dict):
            if "text" in query_vector and isinstance(query_vector["text"], (list, tuple)):
                query_vector = list(query_vector["text"])
            else:
                # Try to extract vector from any dict value
                for v in query_vector.values():
                    if isinstance(v, (list, tuple)) and v and isinstance(v[0], (int, float)):
                        query_vector = list(v)
                        break
        elif hasattr(query_vector, "vector") and isinstance(getattr(query_vector, "vector"), (list, tuple)):
            query_vector = list(getattr(query_vector, "vector"))

        # Step 2: Validate query vector format
        if not isinstance(query_vector, (list, tuple)) or not query_vector or not isinstance(query_vector[0], (int, float)):
            raise ValueError(
                "query_vector must be a list[float] for unnamed-vector collections. "
                f"Got: {type(query_vector)}"
            )

        # Step 3: Convert RBAC filters to Qdrant format
        qdrant_filter = self.validate_filters(filters)

        # Step 4: Execute Qdrant search
        # Note: Modern Qdrant client uses 'query_points()' method with 'query_filter' parameter
        try:
            response = self.client.query_points(
                collection_name=collection,
                query=query_vector,  # 'query' parameter instead of 'query_vector'
                limit=int(limit),
                score_threshold=(float(score_threshold) if score_threshold is not None else None),
                with_payload=bool(with_payload),
                with_vectors=bool(with_vectors),
                query_filter=qdrant_filter,
            )
            
            # Convert Qdrant points to SearchResult objects
            results = []
            for point in response.points:
                # Extract vector if requested
                vec = None
                if with_vectors and hasattr(point, "vector"):
                    if isinstance(point.vector, dict) and "text" in point.vector:
                        vec = point.vector["text"]
                    elif isinstance(point.vector, list):
                        vec = point.vector
                
                results.append(SearchResult(
                    id=str(point.id),
                    score=float(point.score) if hasattr(point, "score") else 0.0,
                    payload=point.payload or {},
                    vector=vec
                ))
            
            logger.debug(f"Search in {collection}: {len(results)} results")
            return results
            
        except ResponseHandlingException as e:
            logger.error(f"Qdrant response error in search: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to search collection {collection}: {e}")
            return []

    def count(self, collection: str, filters: dict[str, Any] | None = None) -> int:
        """
        Count points in collection with optional RBAC filters.
        
        Args:
            collection: Collection name
            filters: Optional RBAC filters
            
        Returns:
            Number of points matching filters
        """
        try:
            if not collection:
                logger.warning("Empty collection name provided to count")
                return 0
            
            qdrant_filter = self.validate_filters(filters)
            res = self.client.count(
                collection_name=collection,
                count_filter=qdrant_filter
            )
            
            count = int(res.count)
            logger.debug(f"Count in {collection}: {count} points")
            return count
        
        except ResponseHandlingException as e:
            logger.error(f"Qdrant response error in count: {e}")
            return 0
        except Exception as e:
            logger.error(f"Failed to count points in {collection}: {e}")
            return 0

    def scroll(
        self,
        collection: str,
        limit: int = 10,
        offset: int = 0,
        with_payload: bool = True,
        with_vectors: bool = False,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """
        Scroll through collection points (for large result sets).
        
        This method is useful for retrieving large numbers of points
        without loading everything into memory at once.
        
        Args:
            collection: Collection name
            limit: Maximum number of results
            offset: Number of points to skip
            with_payload: Include payload in results
            with_vectors: Include vectors in results
            filters: Optional RBAC filters
            
        Returns:
            List of SearchResult objects
        """
        try:
            if not collection:
                logger.warning("Empty collection name provided to scroll")
                return []
            
            qdrant_filter = self.validate_filters(filters)
            points, _ = self.client.scroll(
                collection_name=collection,
                limit=limit + max(0, offset),
                offset=offset,
                with_payload=with_payload,
                with_vectors=with_vectors,
                scroll_filter=qdrant_filter,
            )

            out: list[SearchResult] = []
            for p in points:
                # Extract vector (handle both named and unnamed vectors)
                vec = None
                if with_vectors and getattr(p, "vector", None) is not None:
                    if isinstance(p.vector, dict) and "text" in p.vector:
                        vec = p.vector["text"]
                    elif isinstance(p.vector, list):
                        vec = p.vector
                
                out.append(SearchResult(
                    id=str(p.id),
                    score=1.0,  # Scroll doesn't provide similarity scores
                    payload=p.payload or {},
                    vector=vec
                ))
            
            logger.debug(f"Scroll {collection}: {len(out)} points")
            return out
        
        except ResponseHandlingException as e:
            logger.error(f"Qdrant response error in scroll: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to scroll collection {collection}: {e}")
            return []
