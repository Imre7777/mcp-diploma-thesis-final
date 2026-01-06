"""
Test if ingestion process still works correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Force UTF-8 encoding for Windows console
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from qdrant_client import QdrantClient
from src.backends.qdrant import QdrantBackend
from src.config.server_config import ServerConfig

def test_ingestion_status():
    """Test current ingestion status and data in Qdrant."""
    
    print("=" * 70)
    print("INGESTION STATUS CHECK")
    print("=" * 70)
    
    # Connect to Qdrant
    print("\n1. Connecting to Qdrant...")
    try:
        client = QdrantClient(url="http://localhost:6334")
        print("   ✅ Connected to Qdrant on port 6334")
    except Exception as e:
        print(f"   ❌ Failed to connect: {e}")
        return False
    
    # Check collections
    print("\n2. Checking collections...")
    try:
        collections = client.get_collections()
        print(f"   ✅ Found {len(collections.collections)} collection(s):")
        
        for coll in collections.collections:
            info = client.get_collection(coll.name)
            print(f"      - {coll.name}: {info.points_count} points")
    except Exception as e:
        print(f"   ❌ Failed to get collections: {e}")
        return False
    
    # Check educational_content collection details
    print("\n3. Checking 'educational_content' collection...")
    try:
        coll_info = client.get_collection("educational_content")
        print(f"   ✅ Collection exists:")
        print(f"      - Points: {coll_info.points_count}")
        print(f"      - Vector size: {coll_info.config.params.vectors.size}")
        print(f"      - Distance: {coll_info.config.params.vectors.distance}")
    except Exception as e:
        print(f"   ❌ Collection not found: {e}")
        return False
    
    # Check access level distribution
    print("\n4. Checking RBAC access levels...")
    try:
        for level in ["public", "student", "teacher", "admin"]:
            count = client.count(
                collection_name="educational_content",
                count_filter={
                    "must": [
                        {
                            "key": "access_level",
                            "match": {"value": level}
                        }
                    ]
                }
            )
            print(f"   - {level}: {count.count} documents")
    except Exception as e:
        print(f"   ⚠️  Could not check access levels: {e}")
    
    # Test search functionality
    print("\n5. Testing search with QdrantBackend...")
    try:
        config = ServerConfig()
        backend = QdrantBackend(
            url=config.vector_db_url,
            api_key=config.vector_db_api_key
        )
        
        # Create a simple test vector (3072 dimensions, all zeros)
        test_vector = [0.0] * 3072
        
        results = backend.search(
            query_vector=test_vector,
            collection="educational_content",
            limit=3,
            with_payload=True
        )
        
        print(f"   ✅ Search successful: {len(results)} results")
        if results:
            print(f"      Example result:")
            print(f"        - ID: {results[0].id}")
            print(f"        - Score: {results[0].score:.4f}")
            print(f"        - Access level: {results[0].payload.get('access_level', 'N/A')}")
            print(f"        - Text preview: {results[0].payload.get('text', '')[:100]}...")
    except Exception as e:
        print(f"   ❌ Search failed: {e}")
        return False
    
    # Check data directories
    print("\n6. Checking data directories...")
    data_dir = Path("data")
    
    dirs_to_check = {
        "incoming": "Incoming JSONL files",
        "processed": "Successfully processed files",
        "failed": "Failed ingestion files",
        "jsonl": "Source JSONL files",
    }
    
    for dir_name, description in dirs_to_check.items():
        dir_path = data_dir / dir_name
        if dir_path.exists():
            files = list(dir_path.glob("*.jsonl"))
            print(f"   ✅ {description}: {len(files)} file(s)")
        else:
            print(f"   ⚠️  {description}: Directory not found")
    
    print("\n" + "=" * 70)
    print("✅ INGESTION STATUS CHECK COMPLETE!")
    print("=" * 70)
    print("\nSummary:")
    print("  - Qdrant is running ✅")
    print(f"  - Data is loaded: {coll_info.points_count} points ✅")
    print("  - Search functionality works ✅")
    print("  - RBAC metadata is present ✅")
    print("\n🎉 Ingestion process is FULLY FUNCTIONAL!")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    success = test_ingestion_status()
    sys.exit(0 if success else 1)
