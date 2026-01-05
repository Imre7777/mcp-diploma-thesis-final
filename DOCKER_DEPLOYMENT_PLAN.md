# 🐳 Docker Compose Deployment Plan - Raspberry Pi

**Date**: January 3, 2026  
**Target**: Raspberry Pi with Docker Compose  
**Data Format**: JSONL (JSON Lines) ⭐  
**Architecture**: Multi-container system

---

## 🏗️ System Architecture

```
Raspberry Pi (Docker Compose)
│
├── Container 1: Qdrant Vector Database
│   ├── Port: 6333 (HTTP API)
│   ├── Port: 6334 (gRPC)
│   └── Volume: ./data/qdrant_storage
│
├── Container 2: MCP Server
│   ├── Port: 8080 (HTTP)
│   ├── Connects to: Qdrant
│   └── Handles: Student/Teacher queries with RBAC
│
├── Container 3: Data Ingestion Service ⭐ NEW
│   ├── Watches: ./data/incoming/*.jsonl
│   ├── Processes: Parse → Embed → Insert to Qdrant
│   └── Moves: processed files to ./data/processed/
│
├── Container 4: OAuth Server
│   ├── Port: 8001
│   ├── Handles: User login, JWT generation
│   └── Volume: ./data/users.db
│
└── Container 5: Caddy Reverse Proxy
    ├── Port: 80, 443
    ├── Handles: TLS, routing, auth
    └── Volume: ./data/caddy_data
```

---

## 📦 Docker Compose Configuration

### **File: `docker-compose.yml`** (Production Ready)

```yaml
version: '3.8'

services:
  # ========================================
  # Qdrant Vector Database
  # ========================================
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    restart: unless-stopped
    ports:
      - "6333:6333"  # HTTP API
      - "6334:6334"  # gRPC
    volumes:
      - ./data/qdrant_storage:/qdrant/storage
    environment:
      # Optional: API key for security
      - QDRANT__SERVICE__API_KEY=${QDRANT_API_KEY:-}
    networks:
      - mcp_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ========================================
  # OAuth Server (User Authentication)
  # ========================================
  oauth-server:
    build:
      context: .
      dockerfile: Dockerfile.oauth
    container_name: oauth-server
    restart: unless-stopped
    ports:
      - "8001:8001"
    volumes:
      - ./src:/app/src:ro
      - ./data/users.db:/app/data/users.db
    environment:
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - DATABASE_URL=sqlite:////app/data/users.db
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    networks:
      - mcp_network
    depends_on:
      - qdrant
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ========================================
  # MCP Server (Main Application)
  # ========================================
  mcp-server:
    build:
      context: .
      dockerfile: Dockerfile.mcp
    container_name: mcp-server
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ./src:/app/src:ro
      - ./data:/app/data:ro  # Read-only access to data
    environment:
      # Qdrant connection
      - VECTOR_DB_BACKEND=qdrant
      - VECTOR_DB_URL=http://qdrant:6333
      - VECTOR_DB_API_KEY=${QDRANT_API_KEY:-}
      - DEFAULT_COLLECTION=educational_content
      
      # Embedding service
      - EMBEDDING_PROVIDER=openai
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - EMBEDDING_MODEL=text-embedding-3-small
      
      # Authentication
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - JWT_ALGORITHM=HS256
      - JWT_EXPIRATION_HOURS=1
      
      # RBAC
      - ENABLE_RBAC=true
      - DEFAULT_ROLE=student
      
      # Server
      - TRANSPORT=http
      - HTTP_HOST=0.0.0.0
      - HTTP_PORT=8080
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    networks:
      - mcp_network
    depends_on:
      qdrant:
        condition: service_healthy
      oauth-server:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ========================================
  # Data Ingestion Service ⭐ NEW
  # Watches for new JSONL files and auto-inserts to Qdrant
  # ========================================
  data-ingestion:
    build:
      context: .
      dockerfile: Dockerfile.ingestion
    container_name: data-ingestion
    restart: unless-stopped
    volumes:
      - ./data/incoming:/app/data/incoming  # Colleague uploads here
      - ./data/processed:/app/data/processed  # Successful files moved here
      - ./data/failed:/app/data/failed  # Failed files moved here
      - ./src:/app/src:ro
    environment:
      # Qdrant connection
      - VECTOR_DB_BACKEND=qdrant
      - VECTOR_DB_URL=http://qdrant:6333
      - VECTOR_DB_API_KEY=${QDRANT_API_KEY:-}
      - DEFAULT_COLLECTION=educational_content
      
      # Embedding service
      - EMBEDDING_PROVIDER=openai
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - EMBEDDING_MODEL=text-embedding-3-small
      
      # File paths
      - DATA_INCOMING_DIR=/app/data/incoming
      - DATA_PROCESSED_DIR=/app/data/processed
      - DATA_FAILED_DIR=/app/data/failed
      
      # Processing
      - WATCH_INTERVAL=5  # Check for new files every 5 seconds
      - BATCH_SIZE=100  # Insert in batches of 100 documents
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    networks:
      - mcp_network
    depends_on:
      qdrant:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "pgrep", "-f", "python"]
      interval: 60s
      timeout: 10s
      retries: 3

  # ========================================
  # Caddy Reverse Proxy
  # ========================================
  caddy:
    image: caddy:2-alpine
    container_name: caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - ./data/caddy_data:/data
      - ./data/caddy_config:/config
    environment:
      - DOMAIN=${DOMAIN:-localhost}
      - EMAIL=${EMAIL:-admin@example.com}
    networks:
      - mcp_network
    depends_on:
      - mcp-server
      - oauth-server

networks:
  mcp_network:
    driver: bridge

volumes:
  qdrant_storage:
  caddy_data:
  caddy_config:
```

---

## 📁 Directory Structure

```
/home/pi/mcp-thesis/
│
├── docker-compose.yml           # Main orchestration file
├── Dockerfile.mcp               # MCP server image
├── Dockerfile.oauth             # OAuth server image
├── Dockerfile.ingestion         # Data ingestion service image ⭐
├── Caddyfile                    # Reverse proxy config
├── .env                         # Environment variables (secrets)
├── .env.example                 # Template for .env
│
├── src/                         # Source code (mounted read-only)
│   ├── server/
│   ├── tools/
│   ├── auth/
│   ├── database/
│   └── pipeline/  ⭐            # Data ingestion code
│
├── data/                        # Persistent data (volumes)
│   ├── incoming/  ⭐            # Colleague uploads JSONL here (SCP target)
│   ├── processed/              # Successfully processed files
│   ├── failed/                 # Failed files (for debugging)
│   ├── qdrant_storage/         # Qdrant database files
│   ├── users.db                # User database
│   ├── caddy_data/             # Caddy certificates
│   └── caddy_config/           # Caddy configuration
│
├── scripts/
│   ├── setup_users.py          # Create initial users
│   ├── init_qdrant.py          # Initialize Qdrant collection
│   └── test_ingestion.sh       # Test data pipeline
│
└── docs/
    └── COLLEAGUE_UPLOAD.md     # Instructions for colleague
```

---

## 🐳 Dockerfiles

### **Dockerfile.mcp** (MCP Server)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run server
CMD ["python", "-m", "uvicorn", "src.server.http_server:app", "--host", "0.0.0.0", "--port", "8080"]
```

### **Dockerfile.oauth** (OAuth Server)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run OAuth server
CMD ["python", "-m", "uvicorn", "src.auth.oauth_server:app", "--host", "0.0.0.0", "--port", "8001"]
```

### **Dockerfile.ingestion** ⭐ (Data Ingestion Service)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Create data directories
RUN mkdir -p /app/data/incoming /app/data/processed /app/data/failed

# Health check (check if process is running)
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD pgrep -f "python.*watch_jsonl" || exit 1

# Run data ingestion watcher
CMD ["python", "-m", "src.pipeline.watch_jsonl"]
```

---

## 📊 JSONL Data Pipeline Implementation

### **File: `src/pipeline/watch_jsonl.py`** ⭐ (NEW - Critical!)

```python
"""
JSONL Data Ingestion Service

Watches for new JSONL files uploaded by colleague and automatically:
1. Parses JSONL (JSON Lines format)
2. Validates document structure
3. Generates embeddings
4. Inserts into Qdrant with visibility metadata
5. Moves processed files to appropriate directory

JSONL Format:
Each line is a complete JSON document. Example:
{"id": "doc_001", "title": "Python Basics", "content": "...", "visibility": "student"}
{"id": "doc_002", "title": "Answer Key", "content": "...", "visibility": "teacher"}
{"id": "doc_003", "title": "Assignment 1", "content": "...", "visibility": "all"}
"""

import asyncio
import json
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from database.qdrant_client import QdrantClient
from database.embeddings import EmbeddingProvider
from config.settings import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JSONLFileHandler(FileSystemEventHandler):
    """
    Handles new JSONL file detection in incoming directory.
    
    Triggers processing when .jsonl files are created or modified.
    """
    
    def __init__(self, processor):
        self.processor = processor
        self._processing = set()  # Track files being processed
    
    def on_created(self, event):
        """Called when a new file is created."""
        if not event.is_directory and event.src_path.endswith('.jsonl'):
            file_path = Path(event.src_path)
            if file_path not in self._processing:
                logger.info(f"New JSONL file detected: {file_path.name}")
                asyncio.run(self._process_with_lock(file_path))
    
    def on_modified(self, event):
        """Called when a file is modified (e.g., during SCP upload)."""
        if not event.is_directory and event.src_path.endswith('.jsonl'):
            file_path = Path(event.src_path)
            if file_path not in self._processing:
                # Wait a bit for file to finish uploading
                asyncio.run(asyncio.sleep(2))
                logger.info(f"Modified JSONL file detected: {file_path.name}")
                asyncio.run(self._process_with_lock(file_path))
    
    async def _process_with_lock(self, file_path: Path):
        """Process file with lock to prevent duplicate processing."""
        if file_path in self._processing:
            return
        
        self._processing.add(file_path)
        try:
            await self.processor.process_file(file_path)
        finally:
            self._processing.discard(file_path)


class JSONLProcessor:
    """
    Processes JSONL files: parse, validate, embed, insert to Qdrant.
    
    Each line in the JSONL file is a separate JSON document.
    """
    
    def __init__(self):
        self.qdrant = QdrantClient()
        self.embeddings = EmbeddingProvider()
        self.incoming_dir = Path(settings.data_incoming_dir)
        self.processed_dir = Path(settings.data_processed_dir)
        self.failed_dir = Path(settings.data_failed_dir)
        self.batch_size = getattr(settings, 'batch_size', 100)
        
        # Create directories if they don't exist
        self.incoming_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.failed_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("JSONL Processor initialized")
        logger.info(f"Watching: {self.incoming_dir}")
        logger.info(f"Processed: {self.processed_dir}")
        logger.info(f"Failed: {self.failed_dir}")
    
    async def process_file(self, file_path: Path):
        """
        Process a single JSONL file.
        
        Args:
            file_path: Path to JSONL file
        """
        start_time = datetime.now()
        logger.info(f"Processing file: {file_path.name}")
        
        try:
            # 1. Parse JSONL file
            documents = self._parse_jsonl(file_path)
            logger.info(f"Parsed {len(documents)} documents from {file_path.name}")
            
            # 2. Validate all documents
            validated_docs = self._validate_documents(documents)
            logger.info(f"Validated {len(validated_docs)} documents")
            
            # 3. Process in batches
            total_inserted = 0
            for i in range(0, len(validated_docs), self.batch_size):
                batch = validated_docs[i:i + self.batch_size]
                inserted = await self._process_batch(batch)
                total_inserted += inserted
                logger.info(
                    f"Batch {i//self.batch_size + 1}: "
                    f"Inserted {inserted}/{len(batch)} documents"
                )
            
            # 4. Move to processed directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            dest_path = self.processed_dir / new_name
            shutil.move(str(file_path), str(dest_path))
            
            # Log success
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"✅ Successfully processed {file_path.name}: "
                f"{total_inserted}/{len(documents)} documents inserted "
                f"in {duration:.2f} seconds"
            )
            
        except Exception as e:
            # Move to failed directory
            logger.error(f"❌ Failed to process {file_path.name}: {e}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_name = f"{file_path.stem}_FAILED_{timestamp}{file_path.suffix}"
            dest_path = self.failed_dir / new_name
            
            try:
                shutil.move(str(file_path), str(dest_path))
                
                # Write error log
                error_log = dest_path.with_suffix('.error.txt')
                error_log.write_text(f"Error: {str(e)}\nTime: {datetime.now()}")
            except Exception as move_error:
                logger.error(f"Failed to move error file: {move_error}")
    
    def _parse_jsonl(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse JSONL file.
        
        Each line is a separate JSON document.
        
        Args:
            file_path: Path to JSONL file
            
        Returns:
            List of parsed documents
            
        Raises:
            ValueError: If file is not valid JSONL
        """
        documents = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue  # Skip empty lines
                
                try:
                    doc = json.loads(line)
                    documents.append(doc)
                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"Invalid JSON on line {line_num}: {e}\n"
                        f"Line content: {line[:100]}..."
                    )
        
        if not documents:
            raise ValueError("No documents found in JSONL file")
        
        return documents
    
    def _validate_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Validate document structure.
        
        Required fields:
        - id: Unique document identifier
        - title: Document title
        - content: Document content (will be embedded)
        - visibility: "student" | "teacher" | "all"
        
        Optional fields:
        - metadata: Additional metadata dict
        
        Args:
            documents: List of documents to validate
            
        Returns:
            List of valid documents
            
        Raises:
            ValueError: If any document is invalid
        """
        validated = []
        
        for i, doc in enumerate(documents, 1):
            # Check required fields
            required_fields = ['id', 'title', 'content', 'visibility']
            missing = [f for f in required_fields if f not in doc]
            
            if missing:
                raise ValueError(
                    f"Document {i} missing required fields: {missing}\n"
                    f"Document ID: {doc.get('id', 'UNKNOWN')}"
                )
            
            # Validate visibility value
            valid_visibility = ['student', 'teacher', 'all']
            visibility = doc['visibility']
            
            if visibility not in valid_visibility:
                raise ValueError(
                    f"Document {i} has invalid visibility: '{visibility}'\n"
                    f"Must be one of: {valid_visibility}\n"
                    f"Document ID: {doc['id']}"
                )
            
            # Validate content is not empty
            if not doc['content'].strip():
                raise ValueError(
                    f"Document {i} has empty content\n"
                    f"Document ID: {doc['id']}"
                )
            
            validated.append(doc)
        
        return validated
    
    async def _process_batch(self, batch: List[Dict]) -> int:
        """
        Process a batch of documents: embed and insert to Qdrant.
        
        Args:
            batch: List of documents to process
            
        Returns:
            Number of successfully inserted documents
        """
        inserted_count = 0
        
        for doc in batch:
            try:
                # Generate embedding for content
                embedding = await self.embeddings.embed_text(doc['content'])
                
                # ⭐ Prepare payload with visibility metadata (KEY for RBAC!)
                payload = {
                    "id": doc['id'],
                    "title": doc['title'],
                    "content": doc['content'],
                    "visibility": doc['visibility'],  # CRITICAL: Used for RBAC filtering!
                    "metadata": doc.get('metadata', {}),
                    "ingested_at": datetime.now().isoformat()
                }
                
                # Insert into Qdrant
                await self.qdrant.insert(
                    collection=settings.default_collection,
                    id=doc['id'],
                    vector=embedding,
                    payload=payload
                )
                
                inserted_count += 1
                logger.debug(
                    f"Inserted: {doc['id']} (visibility: {doc['visibility']})"
                )
                
            except Exception as e:
                logger.error(f"Failed to insert document {doc.get('id')}: {e}")
                # Continue with next document
        
        return inserted_count


async def main():
    """Main entry point for JSONL watcher service."""
    logger.info("=" * 60)
    logger.info("JSONL Data Ingestion Service Starting")
    logger.info("=" * 60)
    
    # Initialize processor
    processor = JSONLProcessor()
    
    # Setup file watcher
    event_handler = JSONLFileHandler(processor)
    observer = Observer()
    observer.schedule(
        event_handler,
        str(processor.incoming_dir),
        recursive=False
    )
    
    # Start watching
    observer.start()
    logger.info(f"👀 Watching for JSONL files in: {processor.incoming_dir}")
    logger.info("Ready to process scraped data from colleague!")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down JSONL watcher...")
        observer.stop()
    
    observer.join()
    logger.info("JSONL watcher stopped")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📝 Instructions for Colleague

### **File: `docs/COLLEAGUE_UPLOAD.md`**

```markdown
# Data Upload Instructions for Colleague

## How to Upload Scraped Data

### 1. JSONL Format (JSON Lines)

Your scraped data should be in **JSONL format** (JSON Lines).  
Each line is a separate JSON document.

**Example file: `education_data_20260103.jsonl`**

```jsonl
{"id": "doc_001", "title": "Introduction to Python", "content": "Python is a versatile programming language used for web development, data science, and automation...", "visibility": "all", "metadata": {"subject": "Computer Science", "difficulty": "beginner"}}
{"id": "doc_002", "title": "Python Exercise 1", "content": "Write a function that calculates the factorial of a number...", "visibility": "student", "metadata": {"subject": "Computer Science", "type": "exercise"}}
{"id": "doc_003", "title": "Python Exercise 1 - Solution", "content": "Solution: def factorial(n): return 1 if n <= 1 else n * factorial(n-1)...", "visibility": "teacher", "metadata": {"subject": "Computer Science", "type": "solution", "confidential": true}}
```

### 2. Required Fields

Each JSON document must have:

- **`id`** (string): Unique identifier (e.g., "doc_001")
- **`title`** (string): Document title
- **`content`** (string): Full document content (this will be embedded)
- **`visibility`** (string): One of:
  - `"all"` - Visible to everyone (students AND teachers)
  - `"student"` - Visible to students AND teachers
  - `"teacher"` - Visible ONLY to teachers (solutions, answer keys)
- **`metadata`** (object, optional): Additional metadata

### 3. Upload via SCP

Upload your JSONL file to the Raspberry Pi:

```bash
scp education_data_20260103.jsonl pi@leowiki-mcp.stream:/home/pi/mcp-thesis/data/incoming/
```

**Password**: [Ask Imre]

### 4. Automatic Processing

Within 5-10 seconds:
- ✅ File will be detected
- ✅ Parsed and validated
- ✅ Embedded (using OpenAI)
- ✅ Inserted into Qdrant
- ✅ Moved to `/data/processed/` with timestamp

### 5. Check Status

**Success**: File appears in `/data/processed/` with timestamp
```bash
ls /home/pi/mcp-thesis/data/processed/
# Output: education_data_20260103_20260103_143022.jsonl
```

**Failed**: File appears in `/data/failed/` with error log
```bash
ls /home/pi/mcp-thesis/data/failed/
# Output: education_data_20260103_FAILED_20260103_143022.jsonl
# Check error: cat education_data_20260103_FAILED_20260103_143022.error.txt
```

### 6. View Logs

```bash
docker logs data-ingestion -f
```

You should see:
```
2026-01-03 14:30:22 - INFO - New JSONL file detected: education_data_20260103.jsonl
2026-01-03 14:30:23 - INFO - Parsed 150 documents from education_data_20260103.jsonl
2026-01-03 14:30:23 - INFO - Validated 150 documents
2026-01-03 14:30:25 - INFO - Batch 1: Inserted 100/100 documents
2026-01-03 14:30:27 - INFO - Batch 2: Inserted 50/50 documents
2026-01-03 14:30:27 - INFO - ✅ Successfully processed: 150/150 documents in 5.23 seconds
```

### 7. Troubleshooting

**Problem**: File not processed

**Solutions**:
1. Check file format: `head education_data.jsonl` (should show one JSON per line)
2. Validate JSON: `cat education_data.jsonl | jq empty` (should show no errors)
3. Check permissions: `ls -la /home/pi/mcp-thesis/data/incoming/`
4. Check logs: `docker logs data-ingestion -f`

**Common Errors**:
- ❌ "Invalid JSON on line X" → Fix JSON syntax
- ❌ "Missing required fields" → Add id, title, content, visibility
- ❌ "Invalid visibility" → Must be "student", "teacher", or "all"
```

---

## 🚀 Deployment Steps

### 1. Initial Setup

```bash
# SSH into Raspberry Pi
ssh pi@leowiki-mcp.stream

# Clone repository
cd /home/pi
git clone https://github.com/Imre7777/mcp-diploma-thesis-final.git mcp-thesis
cd mcp-thesis

# Create .env file
cp .env.example .env
nano .env  # Add your secrets (OpenAI API key, JWT secret, etc.)

# Create data directories
mkdir -p data/{incoming,processed,failed,qdrant_storage,caddy_data,caddy_config}
chmod 755 data/incoming  # Allow colleague to upload
```

### 2. Build and Start

```bash
# Build all images
docker-compose build

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# Expected output:
# NAME              STATUS         PORTS
# qdrant            Up (healthy)   0.0.0.0:6333->6333/tcp
# oauth-server      Up (healthy)   0.0.0.0:8001->8001/tcp
# mcp-server        Up (healthy)   0.0.0.0:8080->8080/tcp
# data-ingestion    Up (healthy)
# caddy             Up             0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

### 3. Initialize Qdrant Collection

```bash
# Create educational_content collection
docker exec -it mcp-server python -m scripts.init_qdrant
```

### 4. Create Initial Users

```bash
# Create admin user
docker exec -it oauth-server python -m scripts.setup_users --create-admin

# Create test student
docker exec -it oauth-server python -m scripts.setup_users \
  --username student1 \
  --email student1@school.com \
  --role student \
  --password test123

# Create test teacher
docker exec -it oauth-server python -m scripts.setup_users \
  --username teacher1 \
  --email teacher1@school.com \
  --role teacher \
  --password test123
```

### 5. Test Data Ingestion

```bash
# Create test JSONL file
cat > test_data.jsonl << 'EOF'
{"id": "test_001", "title": "Test Document 1", "content": "This is a test document visible to all.", "visibility": "all", "metadata": {"test": true}}
{"id": "test_002", "title": "Test Student Doc", "content": "This is a student document.", "visibility": "student", "metadata": {"test": true}}
{"id": "test_003", "title": "Test Teacher Doc", "content": "This is a teacher-only document.", "visibility": "teacher", "metadata": {"test": true}}
EOF

# Copy to incoming directory
cp test_data.jsonl data/incoming/

# Watch logs
docker logs data-ingestion -f

# Should see processing logs within 5-10 seconds
```

---

## 📊 Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker logs mcp-server -f
docker logs data-ingestion -f
docker logs qdrant -f
```

### Check Health

```bash
# All services
docker-compose ps

# Qdrant
curl http://localhost:6333/healthz

# MCP Server
curl http://localhost:8080/health

# OAuth Server
curl http://localhost:8001/health
```

### Resource Usage

```bash
# CPU and Memory
docker stats

# Disk usage
du -sh data/qdrant_storage
du -sh data/incoming
du -sh data/processed
```

---

## 🔧 Maintenance

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart data-ingestion
```

### Update Code

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d
```

### Backup Qdrant Data

```bash
# Create backup
tar -czf qdrant_backup_$(date +%Y%m%d).tar.gz data/qdrant_storage/

# Or use Qdrant snapshot API
curl -X POST http://localhost:6333/collections/educational_content/snapshots
```

---

## 📝 Summary

**✅ You Now Have:**

1. **Multi-container Docker Compose** setup
2. **JSONL ingestion pipeline** (auto-processes colleague uploads)
3. **Qdrant** for vector storage
4. **MCP server** with RBAC
5. **OAuth server** for authentication
6. **Caddy** for TLS and routing
7. **Data ingestion service** that watches for new .jsonl files

**⚡ Automatic Workflow:**

```
Colleague uploads JSONL
       ↓
data/incoming/*.jsonl
       ↓
Data Ingestion Service detects file
       ↓
Parse → Validate → Embed → Insert to Qdrant
       ↓
Move to data/processed/
       ↓
MCP Server can now query this data!
```

**🎓 Thesis Benefits:**

- ✅ Production-ready Docker deployment
- ✅ Automated data pipeline (no manual work!)
- ✅ JSONL format (industry standard for streaming data)
- ✅ Batch processing (efficient)
- ✅ Error handling (failed files tracked)
- ✅ Monitoring and logging

---

**Ready to deploy on Raspberry Pi!** 🚀
