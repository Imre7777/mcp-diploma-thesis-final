"""
Test new 3072-dimensional embeddings in local Qdrant
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient

def main():
    print("=" * 60)
    print("Testing New Embeddings (3072D) in Local Qdrant")
    print("=" * 60)
    
    # Connect to local Docker Qdrant
    client = QdrantClient(url="http://localhost:6334")
    
    # Get collection info
    collection_name = "htl_wiki_content"
    try:
        collection = client.get_collection(collection_name)
        print(f"\n[OK] Collection: {collection_name}")
        print(f"   Points: {collection.points_count}")
        print(f"   Vector size: {collection.config.params.vectors.size}")
        print(f"   Distance: {collection.config.params.vectors.distance}")
        
        # Try to search with a sample query
        from src.utils.embeddings import create_embedding_service
        
        embedding_service = create_embedding_service()
        print(f"\n[OK] EmbeddingService initialized")
        print(f"   Model: {embedding_service.model}")
        print(f"   Dimensions: {embedding_service.dimensions}")
        print(f"   Using mock: {embedding_service.is_using_mock}")
        
        # Generate query embedding
        query = "Matura Prüfung"
        query_vector = embedding_service.embed_query(query)
        print(f"\n[OK] Query embedding generated")
        print(f"   Query: '{query}'")
        print(f"   Vector length: {len(query_vector)}")
        
        # Search in Qdrant
        results = client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=3,
            with_payload=True
        )
        
        print(f"\n[OK] Search results: {len(results.points)} points")
        for i, result in enumerate(results.points, 1):
            text = result.payload.get('text', 'N/A')[:100]
            score = result.score
            print(f"   {i}. Score: {score:.4f}")
            print(f"      Text: {text}...")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
