#!/usr/bin/env python3
"""
Watchdog Service - Automatic JSONL File Processing

This service monitors the incoming directory for new JSONL files
and automatically processes them into the Qdrant vector database.

Usage:
    python -m src.pipeline.watchdog_service
"""

import asyncio
import logging
import os
import signal
import sys
import time
from pathlib import Path

from qdrant_client import QdrantClient
from src.pipeline.jsonl_ingestion import JSONLIngestionPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class WatchdogService:
    """
    Watchdog service for automatic JSONL file processing.
    
    Monitors the incoming directory and automatically processes
    new JSONL files as they arrive.
    """
    
    def __init__(self):
        """Initialize watchdog service."""
        self.pipeline = None
        self.observer = None
        self.shutdown_event = asyncio.Event()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_event.set()
    
    async def start(self):
        """Start the watchdog service."""
        try:
            logger.info("=" * 70)
            logger.info("  MCP Educational Server - Watchdog Service")
            logger.info("  Automatic JSONL File Processing")
            logger.info("=" * 70)
            logger.info("")
            
            # Load configuration from environment
            qdrant_url = os.getenv("VECTOR_DB_URL", "http://qdrant:6334")
            collection_name = os.getenv("DEFAULT_COLLECTION", "educational_content")
            incoming_dir = Path(os.getenv("INCOMING_DIR", "/app/data/incoming"))
            processed_dir = Path(os.getenv("PROCESSED_DIR", "/app/data/processed"))
            failed_dir = Path(os.getenv("FAILED_DIR", "/app/data/failed"))
            
            logger.info(f"Configuration:")
            logger.info(f"  Qdrant URL: {qdrant_url}")
            logger.info(f"  Collection: {collection_name}")
            logger.info(f"  Incoming: {incoming_dir}")
            logger.info(f"  Processed: {processed_dir}")
            logger.info(f"  Failed: {failed_dir}")
            logger.info("")
            
            # Initialize Qdrant client
            logger.info("Connecting to Qdrant...")
            qdrant_client = QdrantClient(url=qdrant_url)
            logger.info("✅ Connected to Qdrant")
            logger.info("")
            
            # Initialize ingestion pipeline
            logger.info("Initializing JSONL ingestion pipeline...")
            self.pipeline = JSONLIngestionPipeline(
                qdrant_client=qdrant_client,
                incoming_dir=incoming_dir,
                processed_dir=processed_dir,
                failed_dir=failed_dir,
                collection_name=collection_name,
                batch_size=100,
                auto_create_collection=True
            )
            logger.info("✅ Pipeline initialized successfully")
            logger.info("")
            
            # Process existing files first
            logger.info("Processing existing files in incoming directory...")
            await self.pipeline.process_existing_files()
            logger.info("✅ Existing files processed")
            logger.info("")
            
            # Start watching for new files
            logger.info("Starting filesystem watcher...")
            self.observer = self.pipeline.start_watching()
            logger.info(f"✅ Watching directory: {self.pipeline.incoming_dir}")
            logger.info("")
            
            logger.info("=" * 70)
            logger.info("🚀 Watchdog service is running!")
            logger.info("=" * 70)
            logger.info("Waiting for new JSONL files...")
            logger.info("Press Ctrl+C to stop")
            logger.info("")
            
            # Keep running until shutdown signal
            while not self.shutdown_event.is_set():
                await asyncio.sleep(1)
            
            logger.info("Shutdown signal received, cleaning up...")
            
        except Exception as e:
            logger.error(f"Fatal error in watchdog service: {e}", exc_info=True)
            raise
        
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources."""
        logger.info("Performing cleanup...")
        
        if self.observer:
            logger.info("Stopping filesystem observer...")
            self.observer.stop()
            self.observer.join(timeout=5)
            logger.info("✅ Observer stopped")
        
        if self.pipeline:
            logger.info("Closing pipeline resources...")
            # Pipeline cleanup if needed
            logger.info("✅ Pipeline closed")
        
        logger.info("=" * 70)
        logger.info("Watchdog service stopped gracefully")
        logger.info("=" * 70)


async def main():
    """Main entry point."""
    service = WatchdogService()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Service failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Run the service
    asyncio.run(main())
