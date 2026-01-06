"""
JSONL File Ingestion Pipeline with Watchdog Integration.

This module provides automated ingestion of JSONL files containing pre-computed
embeddings into the Qdrant vector database. It includes:
- File system watching for automatic ingestion
- JSONL validation and parsing
- Batch upsert to Qdrant with RBAC payload
- Error handling and file management
- Statistics tracking
"""

import asyncio
import json
import logging
import shutil
import time
import uuid
from pathlib import Path
from typing import Any
from datetime import datetime
from zoneinfo import ZoneInfo

import aiofiles
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams

logger = logging.getLogger(__name__)


# ============================================================================
# Validation Functions
# ============================================================================
def _parse_inline_metadata(text: str, doc_id: str) -> dict:
    """
    Parse inline metadata from text field (legacy format support).
    
    Expected format in text:
        "Title: ...\nNamespace: ...\nContent_Type: ..."
    
    Args:
        text: Text content with inline metadata
        doc_id: Document ID for logging
        
    Returns:
        Dictionary with frontmatter structure
    """
    metadata = {
        "title": "Untitled",
        "namespace": "default",
        "content_type": "KNOWLEDGE",
        "access_level": "student"  # Default
    }
    
    # Parse inline metadata from text (first few lines)
    lines = text.split('\n')[:5]  # Check first 5 lines
    
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            
            if key == "title":
                metadata["title"] = value
            elif key == "namespace":
                metadata["namespace"] = value
                # Set access_level based on namespace
                if "teacher" in value.lower() or "exams" in value.lower():
                    metadata["access_level"] = "teacher"
                elif "admin" in value.lower():
                    metadata["access_level"] = "admin"
                else:
                    metadata["access_level"] = "student"
            elif key == "content_type":
                metadata["content_type"] = value
    
    logger.debug(
        f"Parsed metadata for {doc_id}: "
        f"title={metadata['title']}, namespace={metadata['namespace']}, "
        f"access_level={metadata['access_level']}"
    )
    
    return metadata


def validate_jsonl_document(doc: dict) -> tuple[bool, str]:
    """
    Validate a single JSONL document structure.
    
    Supports two formats:
    1. New format with metadata.frontmatter structure
    2. Legacy format with inline metadata in text field (auto-converted)
    
    Required fields:
    - id: str
    - text: str
    - embedding: list[float] with 3072 dimensions
    - metadata: dict with frontmatter containing access_level (auto-created if missing)
    
    Args:
        doc: Document dictionary from JSONL line
        
    Returns:
        Tuple of (is_valid, error_message)
        - (True, "OK") if valid
        - (False, "error message") if invalid
    """
    # Check required top-level fields
    if "id" not in doc:
        return False, "Missing required field: 'id'"
    
    if "text" not in doc or not isinstance(doc["text"], str):
        return False, "Missing or invalid 'text' field (must be string)"
    
    if "embedding" not in doc:
        return False, "Missing required field: 'embedding'"
    
    # Validate embedding dimensions
    embedding = doc["embedding"]
    if not isinstance(embedding, list):
        return False, f"'embedding' must be a list, got {type(embedding)}"
    
    if len(embedding) != 3072:
        return False, f"Invalid embedding dimensions: {len(embedding)} (expected 3072 for text-embedding-3-large)"
    
    # Check all values are floats/ints
    if not all(isinstance(v, (int, float)) for v in embedding):
        return False, "'embedding' must contain only numbers (int/float)"
    
    # Auto-create metadata structure if missing (legacy format support)
    if "metadata" not in doc or not isinstance(doc["metadata"], dict):
        logger.info(f"Auto-creating metadata structure for document {doc['id']} (legacy format)")
        doc["metadata"] = {}
    
    metadata = doc["metadata"]
    
    # Auto-create frontmatter if missing (legacy format support)
    if "frontmatter" not in metadata:
        # Check if metadata already has the required fields directly (flat structure)
        if "access_level" in metadata or "title" in metadata:
            # Metadata is already in the correct format, just flat instead of nested
            logger.debug(f"Using flat metadata structure for document {doc['id']}")
            frontmatter = metadata  # Use metadata directly as frontmatter (no nesting needed)
        else:
            # Parse from text field (old format)
            logger.info(f"Parsing inline metadata from text field for document {doc['id']}")
            frontmatter = _parse_inline_metadata(doc["text"], doc["id"])
            metadata["frontmatter"] = frontmatter
    
    # Get frontmatter reference (either nested or flat)
    frontmatter = metadata.get("frontmatter", metadata)
    
    if not isinstance(frontmatter, dict):
        return False, "'frontmatter' must be a dict"
    
    # Validate RBAC field (access_level)
    valid_access_levels = {"public", "student", "teacher", "admin"}
    
    # Map common aliases to standard values
    access_level_mapping = {
        "teacher_only": "teacher",
        "student_only": "student",
        "all": "public",
    }
    
    access_level = frontmatter.get("access_level", "public")
    
    # Apply alias mapping
    if access_level in access_level_mapping:
        original_level = access_level
        access_level = access_level_mapping[access_level]
        frontmatter["access_level"] = access_level
        logger.debug(
            f"Mapped access_level '{original_level}' to '{access_level}' "
            f"for document {doc['id']}"
        )
    
    if access_level not in valid_access_levels:
        # Warn but don't fail - default to public
        logger.warning(
            f"Invalid access_level '{access_level}' for document {doc['id']}, "
            f"defaulting to 'public'"
        )
        frontmatter["access_level"] = "public"
        return True, f"Warning: Defaulted access_level to 'public'"
    
    return True, "OK"


def extract_payload_from_document(doc: dict) -> dict[str, Any]:
    """
    Extract Qdrant payload from JSONL document.
    
    This function extracts relevant fields for RBAC filtering and search,
    excluding the embedding vector (stored separately in Qdrant).
    
    Args:
        doc: JSONL document dictionary
        
    Returns:
        Payload dictionary for Qdrant point
    """
    metadata = doc.get("metadata", {})
    frontmatter = metadata.get("frontmatter", {})
    
    payload = {
        # Core content fields
        "text": doc.get("text", ""),
        "source": metadata.get("source", ""),
        "collection": metadata.get("collection", "unknown"),
        "chunk_index": metadata.get("chunk_index", 0),
        "total_chunks": metadata.get("total_chunks", 1),
        
        # RBAC fields (critical for filtering!)
        "access_level": frontmatter.get("access_level", "public"),
        "content_type": frontmatter.get("content_type", "KNOWLEDGE"),
        "freshness_score": frontmatter.get("freshness_score", 0.5),
        "freshness_category": frontmatter.get("freshness_category", "unknown"),
        
        # Searchable metadata
        "title": frontmatter.get("title", ""),
        "namespace": frontmatter.get("namespace", ""),
        "author": frontmatter.get("author", ""),
        "last_modified": frontmatter.get("last_modified", ""),
        "page_id": frontmatter.get("page_id", ""),
        
        # Additional fields
        "embedding_model": metadata.get("embedding_model", "text-embedding-3-large"),
        "created_at": metadata.get("created_at", ""),
        "original_length": metadata.get("original_length", 0),
    }
    
    return payload


# ============================================================================
# JSONL Ingestion Pipeline
# ============================================================================
class JSONLIngestionPipeline:
    """
    Automated JSONL ingestion pipeline with file watching.
    
    This class handles:
    - Watching incoming directory for new JSONL files
    - Validating and parsing JSONL documents
    - Batch upserting to Qdrant with RBAC payload
    - Moving processed/failed files
    - Statistics tracking
    """
    
    def __init__(
        self,
        qdrant_client: QdrantClient,
        incoming_dir: str | Path,
        processed_dir: str | Path,
        failed_dir: str | Path,
        collection_name: str = "educational_content",
        batch_size: int = 100,
        auto_create_collection: bool = True,
    ):
        """
        Initialize the ingestion pipeline.
        
        Args:
            qdrant_client: Initialized Qdrant client
            incoming_dir: Directory to watch for new JSONL files
            processed_dir: Directory to move successfully processed files
            failed_dir: Directory to move failed files
            collection_name: Qdrant collection name
            batch_size: Number of points to upsert in one batch
            auto_create_collection: Auto-create collection if it doesn't exist
        """
        self.qdrant_client = qdrant_client
        self.incoming_dir = Path(incoming_dir)
        self.processed_dir = Path(processed_dir)
        self.failed_dir = Path(failed_dir)
        self.collection_name = collection_name
        self.batch_size = batch_size
        self.auto_create_collection = auto_create_collection
        
        # Ensure directories exist
        self.incoming_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.failed_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            "files_processed": 0,
            "files_failed": 0,
            "documents_ingested": 0,
            "documents_failed": 0,
            "last_ingestion": None,
        }
        
        logger.info(
            f"Initialized JSONL ingestion pipeline: "
            f"collection={collection_name}, batch_size={batch_size}"
        )
    
    def ensure_collection_exists(self) -> bool:
        """
        Ensure the Qdrant collection exists, create if necessary.
        
        Returns:
            True if collection exists/created, False on error
        """
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections().collections
            if any(c.name == self.collection_name for c in collections):
                logger.info(f"Collection '{self.collection_name}' already exists")
                return True
            
            if not self.auto_create_collection:
                logger.error(
                    f"Collection '{self.collection_name}' does not exist and "
                    f"auto_create_collection=False"
                )
                return False
            
            # Create collection
            logger.info(f"Creating collection '{self.collection_name}'...")
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=3072,  # text-embedding-3-large dimensions
                    distance=Distance.COSINE
                ),
            )
            
            logger.info(f"Collection '{self.collection_name}' created successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to ensure collection exists: {e}")
            return False
    
    def clear_collection(self) -> bool:
        """
        Delete all points from the collection.
        
        This ensures a clean state before ingesting new data,
        preventing orphaned documents from previous uploads.
        
        Returns:
            True if successful, False on error
        """
        try:
            logger.info(f"🗑️  Clearing all points from collection '{self.collection_name}'...")
            
            # Delete all points by using a filter that matches everything
            # Using scroll to get all point IDs, then delete them
            scroll_result = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=10000,  # Get all points (adjust if you have more than 10k)
                with_payload=False,
                with_vectors=False,
            )
            
            point_ids = [point.id for point in scroll_result[0]]
            
            if not point_ids:
                logger.info("Collection is already empty")
                return True
            
            logger.info(f"Deleting {len(point_ids)} existing points...")
            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=point_ids,
            )
            
            logger.info(f"✅ Cleared {len(point_ids)} points from collection")
            return True
        
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return False
    
    async def ingest_jsonl_file(self, file_path: Path) -> tuple[bool, str, dict]:
        """
        Ingest a single JSONL file into Qdrant.
        
        Args:
            file_path: Path to JSONL file
            
        Returns:
            Tuple of (success, message, statistics)
        """
        logger.info(f"Starting ingestion of {file_path.name}...")
        
        stats = {
            "total_lines": 0,
            "valid_documents": 0,
            "invalid_documents": 0,
            "ingested_points": 0,
            "errors": [],
        }
        
        points_batch: list[PointStruct] = []
        
        try:
            # Ensure collection exists
            if not self.ensure_collection_exists():
                return False, "Collection does not exist and could not be created", stats
            
            # Clear collection before ingestion if configured
            # This ensures the uploaded file is the ONLY source of truth
            clear_before_ingest = os.getenv("CLEAR_COLLECTION_BEFORE_INGEST", "false").lower() == "true"
            if clear_before_ingest:
                logger.info("🔄 CLEAR_COLLECTION_BEFORE_INGEST=true: Clearing existing data...")
                if not self.clear_collection():
                    logger.warning("Failed to clear collection, continuing anyway...")
                else:
                    logger.info("✅ Collection cleared, starting fresh ingestion...")
            
            # Read and process JSONL file line by line
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                async for line in f:
                    stats["total_lines"] += 1
                    line = line.strip()
                    
                    if not line:
                        continue  # Skip empty lines
                    
                    try:
                        # Parse JSON
                        doc = json.loads(line)
                        
                        # Validate document structure
                        is_valid, error_msg = validate_jsonl_document(doc)
                        
                        if not is_valid:
                            stats["invalid_documents"] += 1
                            stats["errors"].append({
                                "line": stats["total_lines"],
                                "id": doc.get("id", "unknown"),
                                "error": error_msg
                            })
                            logger.warning(
                                f"Invalid document at line {stats['total_lines']}: {error_msg}"
                            )
                            continue
                        
                        stats["valid_documents"] += 1
                        
                        # Extract payload and create Qdrant point
                        payload = extract_payload_from_document(doc)
                        
                        # Convert string ID to UUID (Qdrant requirement)
                        # Using UUID5 for deterministic conversion (same string = same UUID)
                        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, doc["id"]))
                        
                        # Store original ID in payload for reference
                        payload["original_id"] = doc["id"]
                        
                        point = PointStruct(
                            id=point_id,
                            vector=doc["embedding"],
                            payload=payload
                        )
                        points_batch.append(point)
                        
                        # Batch upsert when batch size reached
                        if len(points_batch) >= self.batch_size:
                            self.qdrant_client.upsert(
                                collection_name=self.collection_name,
                                points=points_batch
                            )
                            stats["ingested_points"] += len(points_batch)
                            logger.debug(
                                f"Upserted batch of {len(points_batch)} points "
                                f"(total: {stats['ingested_points']})"
                            )
                            points_batch = []
                    
                    except json.JSONDecodeError as e:
                        stats["invalid_documents"] += 1
                        stats["errors"].append({
                            "line": stats["total_lines"],
                            "error": f"JSON decode error: {str(e)}"
                        })
                        logger.warning(f"JSON decode error at line {stats['total_lines']}: {e}")
                    
                    except Exception as e:
                        stats["invalid_documents"] += 1
                        stats["errors"].append({
                            "line": stats["total_lines"],
                            "error": str(e)
                        })
                        logger.error(f"Error processing line {stats['total_lines']}: {e}")
            
            # Upsert remaining points
            if points_batch:
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=points_batch
                )
                stats["ingested_points"] += len(points_batch)
                logger.debug(f"Upserted final batch of {len(points_batch)} points")
            
            # Update global stats
            self.stats["files_processed"] += 1
            self.stats["documents_ingested"] += stats["ingested_points"]
            self.stats["documents_failed"] += stats["invalid_documents"]
            self.stats["last_ingestion"] = datetime.now(ZoneInfo("Europe/Vienna")).isoformat()
            
            success_msg = (
                f"Successfully ingested {file_path.name}: "
                f"{stats['ingested_points']} points from {stats['valid_documents']} documents "
                f"({stats['invalid_documents']} invalid, {stats['total_lines']} total lines)"
            )
            logger.info(success_msg)
            
            return True, success_msg, stats
        
        except Exception as e:
            error_msg = f"Failed to ingest {file_path.name}: {str(e)}"
            logger.error(error_msg)
            self.stats["files_failed"] += 1
            return False, error_msg, stats
    
    async def process_file(self, file_path: Path):
        """
        Process a single JSONL file and move to processed/failed directory.
        
        Args:
            file_path: Path to JSONL file
        """
        logger.info(f"Processing file: {file_path.name}")
        
        success, message, stats = await self.ingest_jsonl_file(file_path)
        
        # Generate timestamp for filename (Europe/Vienna timezone)
        timestamp = datetime.now(ZoneInfo("Europe/Vienna")).strftime("%Y%m%d_%H%M%S")
        
        if success:
            # Move to processed directory
            dest_path = self.processed_dir / f"{timestamp}_{file_path.name}"
            shutil.move(str(file_path), str(dest_path))
            logger.info(f"Moved {file_path.name} to processed: {dest_path.name}")
        else:
            # Move to failed directory
            dest_path = self.failed_dir / f"{timestamp}_{file_path.name}"
            shutil.move(str(file_path), str(dest_path))
            logger.error(f"Moved {file_path.name} to failed: {dest_path.name}")
            
            # Write error log
            error_log_path = dest_path.with_suffix(".error.json")
            async with aiofiles.open(error_log_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps({
                    "file": file_path.name,
                    "timestamp": timestamp,
                    "message": message,
                    "stats": stats
                }, indent=2))
            logger.info(f"Error log written to: {error_log_path.name}")
    
    async def process_existing_files(self):
        """Process all existing JSONL files in incoming directory."""
        jsonl_files = list(self.incoming_dir.glob("*.jsonl"))
        
        if not jsonl_files:
            logger.info("No existing JSONL files to process")
            return
        
        logger.info(f"Found {len(jsonl_files)} existing JSONL files to process")
        
        for file_path in jsonl_files:
            await self.process_file(file_path)
    
    def start_watching(self):
        """Start watching incoming directory for new files."""
        event_handler = JSONLFileHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(self.incoming_dir), recursive=False)
        observer.start()
        logger.info(f"Started watching directory: {self.incoming_dir}")
        return observer
    
    def get_stats(self) -> dict:
        """Get ingestion statistics."""
        return self.stats.copy()


# ============================================================================
# File System Event Handler
# ============================================================================
class JSONLFileHandler(FileSystemEventHandler):
    """Watchdog event handler for JSONL files."""
    
    def __init__(self, pipeline: JSONLIngestionPipeline):
        """
        Initialize handler.
        
        Args:
            pipeline: JSONLIngestionPipeline instance
        """
        self.pipeline = pipeline
        super().__init__()
    
    def _wait_for_file_stable(self, file_path: Path, check_interval: float = 1.0, max_wait: int = 300) -> bool:
        """
        Wait until file size is stable (not growing anymore).
        
        This prevents processing files that are still being uploaded via SCP/rsync.
        
        Args:
            file_path: Path to file
            check_interval: Seconds between size checks
            max_wait: Maximum seconds to wait
            
        Returns:
            True if file is stable, False if timeout or error
        """
        logger.info(f"Waiting for file to stabilize: {file_path.name}")
        
        try:
            previous_size = -1
            stable_count = 0
            elapsed = 0
            
            while elapsed < max_wait:
                if not file_path.exists():
                    logger.warning(f"File disappeared while waiting: {file_path.name}")
                    return False
                
                current_size = file_path.stat().st_size
                
                if current_size == previous_size:
                    stable_count += 1
                    # File size hasn't changed for 2 consecutive checks
                    if stable_count >= 2:
                        logger.info(
                            f"File is stable: {file_path.name} "
                            f"({current_size / (1024*1024):.2f} MB)"
                        )
                        return True
                else:
                    stable_count = 0
                    logger.debug(
                        f"File still growing: {file_path.name} "
                        f"({current_size / (1024*1024):.2f} MB)"
                    )
                
                previous_size = current_size
                time.sleep(check_interval)
                elapsed += check_interval
            
            logger.warning(
                f"Timeout waiting for file to stabilize: {file_path.name} "
                f"(waited {max_wait}s)"
            )
            return False
            
        except Exception as e:
            logger.error(f"Error waiting for file stability: {e}")
            return False
    
    def on_created(self, event: FileCreatedEvent):
        """Handle file creation event."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Only process .jsonl files
        if file_path.suffix.lower() != ".jsonl":
            return
        
        logger.info(f"Detected new file: {file_path.name}")
        
        # Wait for file to be completely uploaded
        if not self._wait_for_file_stable(file_path):
            logger.error(
                f"File did not stabilize, skipping processing: {file_path.name}"
            )
            return
        
        # Process file asynchronously
        asyncio.run(self.pipeline.process_file(file_path))
