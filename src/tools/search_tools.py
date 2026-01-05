"""
Search Tools with RBAC Support

This module provides semantic search tools with role-based access control,
allowing users to search educational content filtered by their access level.
"""

import logging
from typing import List, Dict, Any, Optional

from mcp.server.fastmcp import FastMCP
from qdrant_client.models import Filter, FieldCondition, MatchAny

from src.backends.qdrant import QdrantBackend
from src.config.server_config import ServerConfig

logger = logging.getLogger(__name__)

# Access level hierarchies for RBAC
# Each role can see its own level plus all levels below it
ROLE_ACCESS_LEVELS = {
    "public": ["public"],
    "student": ["public", "student"],
    "teacher": ["public", "student", "teacher"],
    "admin": ["public", "student", "teacher", "admin"],
}


def get_access_filter(user_role: str) -> Filter:
    """
    Create a Qdrant filter for role-based access control.
    
    Args:
        user_role: User's role (public, student, teacher, admin)
        
    Returns:
        Filter: Qdrant filter for access control
    """
    # Get allowed access levels for this role
    allowed_levels = ROLE_ACCESS_LEVELS.get(user_role, ["public"])
    
    # Create filter
    return Filter(
        must=[
            FieldCondition(
                key="access_level",
                match=MatchAny(any=allowed_levels)
            )
        ]
    )


def register_search_tools(
    mcp: FastMCP,
    db: QdrantBackend,
    embedding_service,
    config: Optional[ServerConfig] = None
) -> None:
    """
    Register search tools with the MCP server.
    
    Args:
        mcp: FastMCP server instance
        db: Qdrant database backend
        embedding_service: Embedding service for query vectorization
        config: Server configuration
    """
    config = config or ServerConfig()
    
    @mcp.tool()
    async def search_content(
        query: str,
        user_role: str = "public",
        limit: int = 10,
        namespace: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search educational content with role-based filtering.
        
        Performs semantic search over educational materials and returns
        results filtered by the user's access level.
        
        Args:
            query: Search query text
            user_role: User's role (public, student, teacher, admin). Default: public
            limit: Maximum number of results to return. Default: 10
            namespace: Optional namespace filter (e.g., "course:math")
            content_type: Optional content type filter (e.g., "KNOWLEDGE", "TUTORIAL")
            
        Returns:
            List of search results with title, content, score, and metadata
            
        Example:
            >>> search_content("How to solve quadratic equations", user_role="student", limit=5)
            [
                {
                    "title": "Quadratic Equations Introduction",
                    "text": "A quadratic equation is...",
                    "score": 0.89,
                    "metadata": {
                        "namespace": "course:math",
                        "access_level": "student",
                        "content_type": "KNOWLEDGE"
                    }
                }
            ]
        """
        try:
            logger.info(
                f"Searching: query='{query}' role={user_role} limit={limit} "
                f"namespace={namespace} content_type={content_type}"
            )
            
            # Validate user role
            if user_role not in ROLE_ACCESS_LEVELS:
                logger.warning(f"Invalid user role '{user_role}', defaulting to 'public'")
                user_role = "public"
            
            # Generate embedding for query
            logger.debug(f"Generating embedding for query: '{query[:50]}...'")
            query_vector = embedding_service.embed_query(query)
            logger.debug(f"Embedding generated: {len(query_vector)} dimensions")
            
            # Build Qdrant filters
            query_filter = None
            filter_conditions = []
            
            # Add RBAC filter if enabled
            if config.enable_rbac:
                allowed_levels = ROLE_ACCESS_LEVELS[user_role]
                filter_conditions.append(
                    FieldCondition(
                        key="access_level",
                        match=MatchAny(any=allowed_levels)
                    )
                )
                logger.debug(f"RBAC filter: access_level in {allowed_levels}")
            
            # Add optional filters
            if namespace:
                filter_conditions.append(
                    FieldCondition(
                        key="namespace",
                        match={"value": namespace}
                    )
                )
                logger.debug(f"Namespace filter: {namespace}")
            
            if content_type:
                filter_conditions.append(
                    FieldCondition(
                        key="content_type",
                        match={"value": content_type}
                    )
                )
                logger.debug(f"Content type filter: {content_type}")
            
            # Create filter if we have conditions
            if filter_conditions:
                query_filter = Filter(must=filter_conditions)
            
            # Perform vector search
            logger.debug(f"Searching collection '{config.default_collection}' with {len(filter_conditions)} filters")
            search_results = db.client.query_points(
                collection_name=config.default_collection,
                query=query_vector,
                limit=limit,
                query_filter=query_filter,
                with_payload=True,
                with_vectors=False,
            ).points
            
            logger.info(f"Found {len(search_results)} results")
            
            # Format results
            formatted_results = []
            for result in search_results:
                formatted_results.append({
                    "title": result.payload.get("title", "Untitled"),
                    "text": result.payload.get("text", "")[:500] + "..." if len(result.payload.get("text", "")) > 500 else result.payload.get("text", ""),
                    "score": float(result.score),
                    "metadata": {
                        "id": result.payload.get("original_id", str(result.id)),
                        "access_level": result.payload.get("access_level", "unknown"),
                        "namespace": result.payload.get("namespace", "unknown"),
                        "content_type": result.payload.get("content_type", "unknown"),
                        "source": result.payload.get("source", "unknown"),
                        "author": result.payload.get("author", "unknown"),
                        "freshness_score": result.payload.get("freshness_score", 0),
                        "freshness_category": result.payload.get("freshness_category", "unknown"),
                        "chunk_index": result.payload.get("chunk_index", 0),
                        "total_chunks": result.payload.get("total_chunks", 1),
                    }
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            return [
                {
                    "title": "Search Error",
                    "text": f"An error occurred during search: {str(e)}",
                    "score": 0.0,
                    "metadata": {"error": True}
                }
            ]

    @mcp.tool()
    async def get_collection_stats(
        user_role: str = "admin"
    ) -> Dict[str, Any]:
        """
        Get statistics about the educational content collection.
        
        Returns information about:
        - Total number of documents
        - Access level distribution
        - Content type distribution
        - Namespace distribution
        
        Args:
            user_role: User's role (must be 'admin' or 'teacher'). Default: admin
            
        Returns:
            Dictionary with collection statistics
            
        Example:
            >>> get_collection_stats(user_role="admin")
            {
                "total_documents": 757,
                "access_levels": {"public": 757, "student": 0, ...},
                "collection": "educational_content"
            }
        """
        try:
            # RBAC check: only admin and teacher can see stats
            if user_role not in ["admin", "teacher"]:
                return {
                    "error": "Access denied",
                    "message": "Only admin and teacher roles can view collection statistics"
                }
            
            logger.info(f"Getting collection stats for role={user_role}")
            
            # Get collection info
            collection_info = db.client.get_collection(config.default_collection)
            total_count = collection_info.points_count
            
            # Get access level distribution
            access_distribution = {}
            for level in ["public", "student", "teacher", "admin"]:
                count = db.client.count(
                    collection_name=config.default_collection,
                    count_filter={
                        "must": [
                            {
                                "key": "access_level",
                                "match": {"value": level}
                            }
                        ]
                    }
                )
                access_distribution[level] = count.count
            
            return {
                "collection": config.default_collection,
                "total_documents": total_count,
                "vector_dimensions": collection_info.config.params.vectors.size,
                "distance_metric": collection_info.config.params.vectors.distance.name,
                "access_levels": access_distribution,
                "rbac_enabled": config.enable_rbac,
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}", exc_info=True)
            return {
                "error": str(e),
                "message": "Failed to retrieve collection statistics"
            }
    
    logger.info("Registered 2 search tools with RBAC support")
