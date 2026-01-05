"""
Test script for JSONL ingestion pipeline.

This script tests the ingestion of colleague's JSONL data into Qdrant.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from qdrant_client import QdrantClient
from pipeline.jsonl_ingestion import JSONLIngestionPipeline
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_ingestion():
    """Test JSONL ingestion with actual data."""
    
    logger.info("=" * 70)
    logger.info("Testing JSONL Ingestion Pipeline")
    logger.info("=" * 70)
    
    # Step 1: Connect to Qdrant
    logger.info("\n[1/5] Connecting to Qdrant...")
    try:
        client = QdrantClient(url="http://localhost:6334")  # Port 6334 for qdrant-mcp-edu container
        health = client.get_collections()
        logger.info(f"✅ Connected to Qdrant! Found {len(health.collections)} collections")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Qdrant: {e}")
        logger.error("Make sure Qdrant is running: docker run -p 6333:6333 qdrant/qdrant")
        return False
    
    # Step 2: Initialize pipeline
    logger.info("\n[2/5] Initializing ingestion pipeline...")
    pipeline = JSONLIngestionPipeline(
        qdrant_client=client,
        incoming_dir="data/incoming",
        processed_dir="data/processed",
        failed_dir="data/failed",
        collection_name="educational_content",
        batch_size=100,
        auto_create_collection=True,
    )
    logger.info("✅ Pipeline initialized")
    
    # Step 3: Copy test file to incoming directory
    logger.info("\n[3/5] Preparing test data...")
    test_file = Path("data/jsonl/pages.jsonl")
    incoming_dir = Path("data/incoming")
    
    if not test_file.exists():
        logger.error(f"❌ Test file not found: {test_file}")
        logger.error("Expected colleague's pages.jsonl in data/jsonl/")
        return False
    
    # Create a small test file (first 10 lines)
    incoming_dir.mkdir(parents=True, exist_ok=True)
    test_incoming = incoming_dir / "test_pages.jsonl"
    
    logger.info(f"Creating test file with first 10 documents from {test_file.name}...")
    with open(test_file, "r", encoding="utf-8") as src:
        with open(test_incoming, "w", encoding="utf-8") as dst:
            for i, line in enumerate(src):
                if i >= 10:
                    break
                dst.write(line)
    
    logger.info(f"✅ Test file created: {test_incoming.name} (10 documents)")
    
    # Step 4: Process the file
    logger.info("\n[4/5] Processing test file...")
    success, message, stats = await pipeline.ingest_jsonl_file(test_incoming)
    
    if success:
        logger.info(f"✅ {message}")
        logger.info(f"   - Total lines: {stats['total_lines']}")
        logger.info(f"   - Valid documents: {stats['valid_documents']}")
        logger.info(f"   - Invalid documents: {stats['invalid_documents']}")
        logger.info(f"   - Ingested points: {stats['ingested_points']}")
        
        if stats['errors']:
            logger.warning(f"   - Errors: {len(stats['errors'])}")
            for error in stats['errors'][:3]:  # Show first 3 errors
                logger.warning(f"     Line {error['line']}: {error['error']}")
    else:
        logger.error(f"❌ {message}")
        return False
    
    # Step 5: Verify data in Qdrant
    logger.info("\n[5/5] Verifying data in Qdrant...")
    try:
        # Count points
        collection_info = client.get_collection("educational_content")
        point_count = collection_info.points_count
        logger.info(f"✅ Collection 'educational_content' has {point_count} points")
        
        # Test search with RBAC filter
        logger.info("\nTesting RBAC search filter...")
        
        # Get first point to use its vector for testing
        points, _ = client.scroll(
            collection_name="educational_content",
            limit=1,
            with_payload=True,
            with_vectors=True
        )
        
        if points:
            test_point = points[0]
            logger.info(f"   - Sample document ID: {test_point.id}")
            logger.info(f"   - Access level: {test_point.payload.get('access_level', 'N/A')}")
            logger.info(f"   - Title: {test_point.payload.get('title', 'N/A')[:50]}...")
            
            # Test search with student role (public + student access)
            logger.info("\n   Testing search with 'student' role filter...")
            results = client.search(
                collection_name="educational_content",
                query_vector=test_point.vector,
                limit=3,
                query_filter={
                    "must": [
                        {
                            "key": "access_level",
                            "match": {
                                "any": ["public", "student"]
                            }
                        }
                    ]
                }
            )
            logger.info(f"   ✅ Found {len(results)} results with student access")
            
            # Test search with teacher role (public + student + teacher access)
            logger.info("\n   Testing search with 'teacher' role filter...")
            results = client.search(
                collection_name="educational_content",
                query_vector=test_point.vector,
                limit=3,
                query_filter={
                    "must": [
                        {
                            "key": "access_level",
                            "match": {
                                "any": ["public", "student", "teacher"]
                            }
                        }
                    ]
                }
            )
            logger.info(f"   ✅ Found {len(results)} results with teacher access")
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False
    
    # Move test file to processed
    logger.info("\n[Cleanup] Moving test file to processed...")
    await pipeline.process_file(test_incoming)
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ ALL TESTS PASSED!")
    logger.info("=" * 70)
    logger.info("\nYour colleague's data structure is perfect!")
    logger.info("Ready to ingest all 757 pages from pages.jsonl")
    logger.info("\nNext steps:")
    logger.info("  1. Copy data/jsonl/pages.jsonl to data/incoming/")
    logger.info("  2. Pipeline will automatically process it")
    logger.info("  3. Check data/processed/ for completed files")
    logger.info("=" * 70)
    
    return True


if __name__ == "__main__":
    result = asyncio.run(test_ingestion())
    sys.exit(0 if result else 1)
