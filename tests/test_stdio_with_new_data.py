"""
Test STDIO mode with new 3417-point dataset
"""
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_stdio_search():
    """Test search functionality with new dataset"""
    print("=" * 60)
    print("Testing Search with New Dataset (3417 points)")
    print("=" * 60)
    
    # Import backend and embedding service
    from src.backends.qdrant import QdrantBackend
    from src.utils.embeddings import create_embedding_service
    from src.config.server_config import ServerConfig
    
    # Initialize components
    config = ServerConfig()
    embedding_service = create_embedding_service(api_key=config.openai_api_key)
    backend = QdrantBackend(
        url="http://localhost:6334",
        collection="htl_wiki_content",
        embedding_service=embedding_service
    )
    
    print(f"\n[OK] Backend initialized")
    print(f"   Qdrant URL: http://localhost:6334")
    print(f"   Collection: htl_wiki_content")
    print(f"   Embedding Model: {embedding_service.model}")
    
    print("\n[TEST 1] Search: Matura Prüfung")
    try:
        results = backend.search(
            query="Matura Prüfung",
            access_level="student",
            limit=3
        )
        print(f"[OK] Found {len(results)} results")
        for i, r in enumerate(results, 1):
            text = r.payload.get('text', 'N/A')[:100]
            score = r.score
            print(f"   {i}. Score: {score:.4f}")
            print(f"      Text: {text}...")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n[TEST 2] Search: Python Programmierung")
    try:
        results = search_content(
            query="Python Programmierung",
            access_level="student",
            limit=3
        )
        print(f"[OK] Found {len(results)} results")
        for i, r in enumerate(results, 1):
            text = r['text'][:100] if 'text' in r else 'N/A'
            score = r.get('score', 0)
            print(f"   {i}. Score: {score:.4f}")
            print(f"      Text: {text}...")
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1
    
    print("\n[TEST 3] Search: HTL Leonding")
    try:
        results = search_content(
            query="HTL Leonding",
            access_level="student",
            limit=3
        )
        print(f"[OK] Found {len(results)} results")
        for i, r in enumerate(results, 1):
            text = r['text'][:100] if 'text' in r else 'N/A'
            score = r.get('score', 0)
            print(f"   {i}. Score: {score:.4f}")
            print(f"      Text: {text}...")
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1
    
    print("\n" + "=" * 60)
    print("[SUCCESS] All STDIO tests passed!")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(test_stdio_search())
