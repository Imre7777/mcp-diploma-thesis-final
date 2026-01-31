"""
Dynamic Content Resources for LeoWiki MCP Server

This module provides dynamic resources that expose live data from the
Qdrant database, including statistics, topic details, and recent updates.
"""

import json
import logging
from datetime import datetime
from fastmcp import FastMCP, Context

logger = logging.getLogger(__name__)


def register_content_resources(mcp: FastMCP):
    """
    Register dynamic content resources with the MCP server.
    
    Args:
        mcp: FastMCP server instance
    """
    
    @mcp.resource(
        uri="leowiki://stats",
        name="Collection Statistics",
        description="Current statistics about the LeoWiki knowledge base",
        mime_type="application/json",
        tags={"metadata", "stats", "live"}
    )
    async def get_stats(ctx: Context) -> str:
        """
        Returns live database statistics.
        
        Provides real-time information about the collection size,
        vector configuration, and health status.
        """
        from src.server.lifespan import AppContext
        
        try:
            app: AppContext = ctx.lifespan_context
            
            # Get collection information
            collection_info = app.qdrant.client.get_collection(
                app.config.default_collection
            )
            
            stats = {
                "collection": app.config.default_collection,
                "total_documents": collection_info.points_count,
                "vector_dimensions": collection_info.config.params.vectors.size,
                "distance_metric": collection_info.config.params.vectors.distance.name,
                "status": "healthy",
                "last_checked": datetime.now().isoformat(),
                "optimizer_status": collection_info.optimizer_status.status.name if collection_info.optimizer_status else "unknown",
                "segments_count": collection_info.segments_count,
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            stats = {
                "status": "error",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }
        
        return json.dumps(stats, indent=2)
    
    
    @mcp.resource(
        uri="leowiki://topic/{topic_id}",
        name="Topic Details",
        description="Detailed information about a specific topic",
        mime_type="application/json",
        tags={"content", "dynamic", "detailed"}
    )
    async def get_topic(topic_id: str, ctx: Context) -> str:
        """
        Retrieve detailed content for a specific topic.
        
        Example URIs:
        - leowiki://topic/sew-java-oop
        - leowiki://topic/nwt-subnetting-basics
        
        Args:
            topic_id: Unique topic identifier
            ctx: MCP context with user information
            
        Returns:
            JSON with topic details or error message
        """
        from src.server.lifespan import AppContext
        
        app: AppContext = ctx.lifespan_context
        user_role = ctx.get_state("user_role") or "student"
        
        try:
            # Search for the specific topic using scroll
            # Note: In production, you'd have a proper topic_id field
            # For now, search by ID in the collection
            results = app.qdrant.client.scroll(
                collection_name=app.config.default_collection,
                scroll_filter={
                    "must": [
                        {"key": "original_id", "match": {"value": topic_id}}
                    ]
                },
                limit=1,
                with_payload=True
            )
            
            if not results[0]:
                return json.dumps({
                    "error": "Topic not found",
                    "topic_id": topic_id,
                    "message": "No topic found with this ID"
                }, indent=2)
            
            topic = results[0][0]
            topic_level = topic.payload.get("access_level", "student")
            
            # Check access level
            allowed_levels = {
                "student": ["student"],
                "teacher": ["student", "teacher"],
                "admin": ["student", "teacher", "admin"]
            }
            
            user_allowed = allowed_levels.get(user_role, ["student"])
            
            if topic_level not in user_allowed:
                return json.dumps({
                    "error": "Access denied",
                    "topic_id": topic_id,
                    "required_level": topic_level,
                    "your_level": user_role,
                    "message": f"This topic requires {topic_level} access level"
                }, indent=2)
            
            # Return topic details
            return json.dumps({
                "id": topic_id,
                "title": topic.payload.get("title", "Untitled"),
                "content": topic.payload.get("text", "No content available"),
                "access_level": topic_level,
                "namespace": topic.payload.get("namespace", "unknown"),
                "content_type": topic.payload.get("content_type", "unknown"),
                "metadata": {
                    "author": topic.payload.get("author", "unknown"),
                    "source": topic.payload.get("source", "unknown"),
                    "freshness_score": topic.payload.get("freshness_score", 0),
                    "chunk_index": topic.payload.get("chunk_index", 0),
                    "total_chunks": topic.payload.get("total_chunks", 1),
                }
            }, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Error retrieving topic {topic_id}: {e}")
            return json.dumps({
                "error": "Retrieval failed",
                "topic_id": topic_id,
                "message": str(e)
            }, indent=2)
    
    
    @mcp.resource(
        uri="leowiki://recent/{count}",
        name="Recent Updates",
        description="Recently updated content in the knowledge base",
        mime_type="application/json",
        tags={"content", "dynamic", "recent"}
    )
    async def get_recent(count: str, ctx: Context) -> str:
        """
        Get recently updated documents.
        
        Args:
            count: Number of recent items to return (max 20)
            ctx: MCP context
            
        Returns:
            JSON with recent documents
        """
        from src.server.lifespan import AppContext
        
        app: AppContext = ctx.lifespan_context
        user_role = ctx.get_state("user_role") or "student"
        
        try:
            # Parse and limit count
            count_int = min(int(count), 20)
            
            # Get allowed access levels for user
            allowed_levels = {
                "student": ["student"],
                "teacher": ["student", "teacher"],
                "admin": ["student", "teacher", "admin"]
            }
            user_allowed = allowed_levels.get(user_role, ["student"])
            
            # Scroll through collection to get recent items
            # Note: Actual "recent" sorting would require timestamp field and sorting
            # For now, just return first N items with user's access level
            from qdrant_client.models import Filter, FieldCondition, MatchAny
            
            results = app.qdrant.client.scroll(
                collection_name=app.config.default_collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="access_level",
                            match=MatchAny(any=user_allowed)
                        )
                    ]
                ),
                limit=count_int,
                with_payload=True
            )
            
            recent_items = []
            for point in results[0]:
                recent_items.append({
                    "id": point.payload.get("original_id", str(point.id)),
                    "title": point.payload.get("title", "Untitled"),
                    "access_level": point.payload.get("access_level", "unknown"),
                    "content_type": point.payload.get("content_type", "unknown"),
                    "source": point.payload.get("source", "unknown"),
                    "freshness_category": point.payload.get("freshness_category", "unknown"),
                })
            
            return json.dumps({
                "count": len(recent_items),
                "items": recent_items,
                "user_role": user_role,
                "retrieved_at": datetime.now().isoformat()
            }, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Error retrieving recent items: {e}")
            return json.dumps({
                "error": "Retrieval failed",
                "message": str(e)
            }, indent=2)
    
    logger.info("Registered 3 dynamic content resources: stats, topic/{id}, recent/{count}")
