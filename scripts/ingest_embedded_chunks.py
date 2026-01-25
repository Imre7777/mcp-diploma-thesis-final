"""
Ingest embedded_chunks.jsonl into local Docker Qdrant
Replaces old 757 points with new 3417 points
"""
import json
import sys
import hashlib
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    print("=" * 60)
    print("INGESTION: embedded_chunks.jsonl -> Local Docker Qdrant")
    print("=" * 60)
    
    # Connect to local Docker Qdrant
    qdrant_url = "http://localhost:6334"  # Local Docker port mapping
    collection_name = "htl_wiki_content"
    
    print(f"\nConnecting to Qdrant: {qdrant_url}")
    client = QdrantClient(url=qdrant_url)
    
    # Check if collection exists
    try:
        collection_info = client.get_collection(collection_name)
        print(f"[OK] Collection '{collection_name}' exists")
        print(f"   Current points: {collection_info.points_count}")
        
        # Delete old collection
        print(f"\n[DELETE] Deleting old collection...")
        client.delete_collection(collection_name)
        print(f"[OK] Old collection deleted")
    except Exception as e:
        print(f"[INFO] Collection doesn't exist yet: {e}")
    
    # Create new collection
    print(f"\n[CREATE] Creating new collection...")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=3072,  # OpenAI text-embedding-3-large
            distance=Distance.COSINE
        )
    )
    print(f"[OK] Collection created")
    
    # Load JSONL file
    jsonl_path = Path(__file__).parent.parent / "embedded_chunks.jsonl"
    print(f"\n[LOAD] Loading: {jsonl_path}")
    
    if not jsonl_path.exists():
        print(f"[ERROR] File not found: {jsonl_path}")
        return 1
    
    points = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
                
                # Extract fields
                original_id = data.get('id', str(idx))
                
                # Convert string ID to integer using hash
                # Qdrant requires integer or UUID, not strings
                if isinstance(original_id, str):
                    # Use first 8 bytes of SHA256 hash as integer
                    hash_bytes = hashlib.sha256(original_id.encode()).digest()[:8]
                    point_id = int.from_bytes(hash_bytes, byteorder='big') % (2**63 - 1)
                else:
                    point_id = original_id
                
                vector = data.get('embedding', data.get('vector'))
                
                # Build payload (all fields except embedding/vector)
                payload = {k: v for k, v in data.items() 
                          if k not in ['id', 'embedding', 'vector']}
                
                # Store original ID in payload for reference
                payload['original_id'] = original_id
                
                # Ensure required fields
                if 'text' not in payload:
                    payload['text'] = data.get('content', data.get('chunk', ''))
                
                if 'access_level' not in payload:
                    payload['access_level'] = 'student'
                
                if 'source' not in payload:
                    payload['source'] = 'embedded_chunks.jsonl'
                
                # Create point
                point = PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
                points.append(point)
                
                # Upload in batches of 100
                if len(points) >= 100:
                    client.upsert(
                        collection_name=collection_name,
                        points=points
                    )
                    print(f"   [OK] Uploaded {idx} points...", end='\r')
                    points = []
                    
            except Exception as e:
                print(f"\n[WARN] Error on line {idx}: {e}")
                continue
    
    # Upload remaining points
    if points:
        client.upsert(
            collection_name=collection_name,
            points=points
        )
    
    # Final count
    collection_info = client.get_collection(collection_name)
    print(f"\n\n[SUCCESS] INGESTION COMPLETE!")
    print(f"   Total points in Qdrant: {collection_info.points_count}")
    print(f"   Collection: {collection_name}")
    print(f"   URL: {qdrant_url}")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
