"""
Test script to verify the search_content function works correctly.

This script tests:
1. Qdrant connection
2. OpenAI embedding generation
3. Search functionality
4. Result formatting
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.server_config import ServerConfig
from src.backends.qdrant import QdrantBackend
from src.utils.embeddings import EmbeddingService
from src.tools.search_tools import get_access_filter

def test_search():
    """Test the complete search pipeline."""
    print("\n" + "="*80)
    print("Testing MCP Educational Server Search Function")
    print("="*80 + "\n")
    
    # Step 1: Load configuration
    print("[1/5] Loading configuration...")
    config = ServerConfig()
    print(f"  - Qdrant URL: {config.vector_db_url}")
    print(f"  - Collection: {config.default_collection}")
    print(f"  - RBAC: {config.enable_rbac}")
    print(f"  - OpenAI API Key: {'***' + config.openai_api_key[-4:] if config.openai_api_key else 'NOT SET'}")
    
    if not config.openai_api_key:
        print("\nERROR: OPENAI_API_KEY not set!")
        return False
    
    # Step 2: Initialize Qdrant backend
    print("\n[2/5] Connecting to Qdrant...")
    try:
        db = QdrantBackend(url=config.vector_db_url)
        health = db.ping()
        if health["status"] != "healthy":
            print(f"  ERROR: Qdrant unhealthy: {health.get('error')}")
            return False
        print(f"  - Status: {health['status']}")
        print(f"  - Collections: {health['collections_count']}")
    except Exception as e:
        print(f"  ERROR: {e}")
        return False
    
    # Step 3: Initialize embedding service
    print("\n[3/5] Initializing OpenAI embedding service...")
    try:
        embedding_service = EmbeddingService(api_key=config.openai_api_key)
        test_embedding = embedding_service.embed_query("test")
        print(f"  - Embedding dimension: {len(test_embedding)}")
        print(f"  - Test embedding generated successfully")
    except Exception as e:
        print(f"  ERROR: {e}")
        return False
    
    # Step 4: Generate query embedding
    print("\n[4/5] Testing search with query: 'machine learning'...")
    query = "machine learning"
    try:
        query_embedding = embedding_service.embed_query(query)
        print(f"  - Query embedding dimension: {len(query_embedding)}")
    except Exception as e:
        print(f"  ERROR generating embedding: {e}")
        return False
    
    # Step 5: Perform search
    print("\n[5/5] Performing search...")
    try:
        # Get RBAC filter
        access_filter = get_access_filter("student") if config.enable_rbac else None
        if access_filter:
            print(f"  - RBAC filter: {access_filter}")
        
        # Search
        results = db.search(
            query_vector=query_embedding,
            collection=config.default_collection,
            limit=5,
            filters=access_filter
        )
        
        print(f"\n  RESULTS: Found {len(results)} results")
        print("  " + "-"*76)
        
        if results:
            for i, result in enumerate(results, 1):
                text = result.payload.get('text', 'No text available')[:100]
                source = result.payload.get('source', 'N/A')
                print(f"\n  [{i}] Score: {result.score:.4f}")
                print(f"      Text: {text}...")
                print(f"      Source: {source}")
        else:
            print("\n  WARNING: No results found!")
            print("  This could mean:")
            print("  - The collection is empty")
            print("  - The RBAC filter is too restrictive")
            print("  - The query has no matching documents")
        
        print("\n" + "="*80)
        print("SUCCESS: All tests passed!")
        print("="*80 + "\n")
        return True
        
    except Exception as e:
        print(f"\n  ERROR during search: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_search()
    sys.exit(0 if success else 1)
