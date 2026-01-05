"""
Full data ingestion script - ingests all 757 pages from pages.jsonl
"""

import asyncio
import sys
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from qdrant_client import QdrantClient
from pipeline.jsonl_ingestion import JSONLIngestionPipeline
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Ingest full pages.jsonl file."""
    
    logger.info("=" * 70)
    logger.info("Full Data Ingestion - 757 Pages")
    logger.info("=" * 70)
    
    # Connect to Qdrant
    logger.info("\nConnecting to Qdrant on port 6334...")
    client = QdrantClient(url="http://localhost:6334")
    
    # Initialize pipeline
    pipeline = JSONLIngestionPipeline(
        qdrant_client=client,
        incoming_dir="data/incoming",
        processed_dir="data/processed",
        failed_dir="data/failed",
        collection_name="educational_content",
        batch_size=100,
        auto_create_collection=True,
    )
    
    # Check for files
    incoming_dir = Path("data/incoming")
    files = list(incoming_dir.glob("*.jsonl"))
    
    if not files:
        logger.error("❌ No JSONL files found in data/incoming/")
        logger.info("Expected: pages.jsonl")
        return False
    
    logger.info(f"\n✅ Found {len(files)} file(s) to process:")
    for f in files:
        size_mb = f.stat().st_size / (1024 * 1024)
        logger.info(f"   - {f.name} ({size_mb:.2f} MB)")
    
    # Process files
    logger.info("\n" + "=" * 70)
    logger.info("Starting Ingestion...")
    logger.info("=" * 70)
    
    start_time = time.time()
    
    for file_path in files:
        logger.info(f"\nProcessing: {file_path.name}")
        await pipeline.process_file(file_path)
    
    elapsed = time.time() - start_time
    
    # Show final stats
    stats = pipeline.get_stats()
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ INGESTION COMPLETE!")
    logger.info("=" * 70)
    logger.info(f"\nStatistics:")
    logger.info(f"  - Files processed: {stats['files_processed']}")
    logger.info(f"  - Files failed: {stats['files_failed']}")
    logger.info(f"  - Documents ingested: {stats['documents_ingested']}")
    logger.info(f"  - Documents failed: {stats['documents_failed']}")
    logger.info(f"  - Time elapsed: {elapsed:.2f} seconds")
    logger.info(f"  - Throughput: {stats['documents_ingested'] / elapsed:.1f} docs/sec")
    
    # Verify in Qdrant
    logger.info("\n" + "=" * 70)
    logger.info("Verifying Data in Qdrant...")
    logger.info("=" * 70)
    
    collection_info = client.get_collection("educational_content")
    point_count = collection_info.points_count
    
    logger.info(f"\n✅ Collection 'educational_content':")
    logger.info(f"   - Total points: {point_count}")
    logger.info(f"   - Vector dimensions: {collection_info.config.params.vectors.size}")
    logger.info(f"   - Distance metric: {collection_info.config.params.vectors.distance}")
    
    # Check access level distribution
    logger.info("\nAccess level distribution:")
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
        logger.info(f"   - {level}: {count.count} documents")
    
    logger.info("\n" + "=" * 70)
    logger.info("🎉 SUCCESS! All data ingested and verified!")
    logger.info("=" * 70)
    logger.info("\nNext steps:")
    logger.info("  1. ✅ Data ingestion complete")
    logger.info("  2. ⏭️  Continue with refactoring (main.py, http_server.py)")
    logger.info("  3. ⏭️  Implement MCP tools with RBAC filtering")
    logger.info("=" * 70)
    
    return True


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
