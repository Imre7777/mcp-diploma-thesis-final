# Quick Start Guide - Testing the Ingestion Pipeline

## Prerequisites

### 1. Start Docker Desktop
- Open Docker Desktop on Windows
- Wait for it to fully start (Docker icon in system tray should be green)

### 2. Start Qdrant
```powershell
# Start Qdrant container (unique name to avoid conflicts)
docker run -d --name qdrant-mcp-edu -p 6334:6333 -p 6335:6334 -v qdrant_mcp_edu_data:/qdrant/storage qdrant/qdrant

# Verify it's running
docker ps | Select-String "qdrant-mcp-edu"

# Check Qdrant is accessible
curl http://localhost:6334
```

Expected output: `{"title":"qdrant - vector search engine","version":"..."}`

### 3. Install Python Dependencies
```powershell
cd "C:\Users\imreo\Documents\MCP_diploma_thesis_final"

# Create virtual environment (recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

---

## Test the Ingestion Pipeline

### Run the Test Script
```powershell
# Make sure you're in the project root
cd "C:\Users\imreo\Documents\MCP_diploma_thesis_final"

# Run the test (processes first 10 documents from pages.jsonl)
python test_ingestion.py
```

### Expected Output
```
======================================================================
Testing JSONL Ingestion Pipeline
======================================================================

[1/5] Connecting to Qdrant...
✅ Connected to Qdrant! Found 0 collections

[2/5] Initializing ingestion pipeline...
✅ Pipeline initialized

[3/5] Preparing test data...
✅ Test file created: test_pages.jsonl (10 documents)

[4/5] Processing test file...
✅ Successfully ingested test_pages.jsonl: 10 points from 10 documents
   - Total lines: 10
   - Valid documents: 10
   - Invalid documents: 0
   - Ingested points: 10

[5/5] Verifying data in Qdrant...
✅ Collection 'educational_content' has 10 points
   - Sample document ID: pages_archive_exams_matura-2021_0
   - Access level: public
   - Title: Ablauf und Durchführung der Matura 2020/21...

   Testing search with 'student' role filter...
   ✅ Found 3 results with student access

   Testing search with 'teacher' role filter...
   ✅ Found 3 results with teacher access

======================================================================
✅ ALL TESTS PASSED!
======================================================================

Your colleague's data structure is perfect!
Ready to ingest all 757 pages from pages.jsonl
```

---

## Ingest All Data (757 Pages)

Once the test passes:

```powershell
# Copy pages.jsonl to incoming directory
Copy-Item "data\jsonl\pages.jsonl" "data\incoming\pages.jsonl"

# The Watchdog will automatically detect and process it!
# Or run manually:
python -c "import asyncio; from src.pipeline import JSONLIngestionPipeline; from qdrant_client import QdrantClient; asyncio.run(JSONLIngestionPipeline(QdrantClient('http://localhost:6333'), 'data/incoming', 'data/processed', 'data/failed').process_existing_files())"
```

### Monitor Progress
```powershell
# Watch the log output
# Check processed files
Get-ChildItem data\processed

# Check for errors
Get-ChildItem data\failed
```

---

## Verify Ingestion

### Check Collection Stats
```powershell
# Check how many points were ingested
curl http://localhost:6333/collections/educational_content
```

Expected: `"points_count": 757`

### Test RBAC Search via Qdrant API
```powershell
# Search with student role filter
$body = @{
    vector = @(0.1) * 3072  # Dummy vector
    limit = 5
    filter = @{
        must = @(
            @{
                key = "access_level"
                match = @{
                    any = @("public", "student")
                }
            }
        )
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:6333/collections/educational_content/points/search" -Method POST -Body $body -ContentType "application/json"
```

---

## Troubleshooting

### Qdrant not starting
```powershell
# Check Docker Desktop is running
docker version

# Check if port 6333 is already in use
netstat -ano | findstr :6333

# Remove old container if needed
docker rm -f qdrant

# Start fresh
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
```

### Test fails with "Collection not found"
The pipeline auto-creates the collection. If it fails:
```powershell
# Manually create collection
$body = @{
    vectors = @{
        size = 3072
        distance = "Cosine"
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:6333/collections/educational_content" -Method PUT -Body $body -ContentType "application/json"
```

### Import errors
```powershell
# Make sure you're in the venv
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

---

## Next Steps

After successful ingestion:

1. ✅ **Week 1 Complete**: Data pipeline working!
2. ⏭️ **Week 2**: Scalekit OAuth integration
3. ⏭️ **Week 3**: MCP tools with RBAC filtering
4. ⏭️ **Week 4**: Docker Compose deployment

---

## Quick Stats

- **Documents**: 757 pages (197 original docs, chunked)
- **Embeddings**: 3072 dimensions (text-embedding-3-large)
- **RBAC Levels**: public, student, teacher, admin
- **Batch Size**: 100 points per batch
- **Expected Time**: ~30-45 seconds for full ingestion
