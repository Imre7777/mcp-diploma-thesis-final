"""
Test the live MCP server's search functionality.

This script tests real semantic search with the OpenAI API.
"""

import sys
import json

# Add src to path
sys.path.insert(0, str(__file__).rsplit('\\', 1)[0])

from src.config.server_config import ServerConfig
from src.backends import create_vector_backend
from src.utils.embeddings import create_embedding_service
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_search():
    """Test semantic search with real embeddings."""
    
    logger.info("=" * 70)
    logger.info("Testing Live Semantic Search")
    logger.info("=" * 70)
    
    # Initialize components
    config = ServerConfig()
    db = create_vector_backend(
        name=config.vector_db_backend,
        url=config.vector_db_url,
    )
    embedding_service = create_embedding_service(
        model=config.embedding_model,
        dimensions=config.vector_dimensions,
    )
    
    # Test queries
    test_queries = [
        ("Matura 2021", "public"),
        ("Stundenplan", "student"),
        ("Lehrerfortbildung", "teacher"),
    ]
    
    for query, role in test_queries:
        logger.info(f"\n{'='*70}")
        logger.info(f"Query: '{query}' | Role: {role}")
        logger.info("=" * 70)
        
        try:
            # Generate embedding
            query_vector = embedding_service.embed_query(query)
            logger.info(f"✅ Generated embedding: {len(query_vector)} dimensions")
            
            # Perform search
            from qdrant_client.models import Filter, FieldCondition, MatchAny
            
            # RBAC filter
            role_access = {
                "public": ["public"],
                "student": ["public", "student"],
                "teacher": ["public", "student", "teacher"],
            }
            allowed_levels = role_access.get(role, ["public"])
            
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="access_level",
                        match=MatchAny(any=allowed_levels)
                    )
                ]
            )
            
            from qdrant_client.models import QueryRequest, VectorInput
            
            results = db.client.query_points(
                collection_name=config.default_collection,
                query=query_vector,
                limit=3,
                query_filter=query_filter,
                with_payload=True,
                with_vectors=False,
            ).points
            
            logger.info(f"✅ Found {len(results)} results")
            
            # Display results
            for i, result in enumerate(results, 1):
                logger.info(f"\n  Result {i}:")
                logger.info(f"    Score: {result.score:.4f}")
                logger.info(f"    Title: {result.payload.get('title', 'N/A')[:60]}...")
                logger.info(f"    Access: {result.payload.get('access_level', 'N/A')}")
                logger.info(f"    Namespace: {result.payload.get('namespace', 'N/A')}")
                logger.info(f"    Source: {result.payload.get('source', 'N/A')[:50]}...")
                text_preview = result.payload.get('text', '')[:150]
                logger.info(f"    Text: {text_preview}...")
                
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ Search testing complete!")
    logger.info("=" * 70)
    logger.info("\nNext steps:")
    logger.info("  - Open http://localhost:8000/docs for Swagger UI")
    logger.info("  - Test MCP tools via the API")
    logger.info("  - Check server logs at terminals/5.txt")
    logger.info("=" * 70)


if __name__ == "__main__":
    test_search()
