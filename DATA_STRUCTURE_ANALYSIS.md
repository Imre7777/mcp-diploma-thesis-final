# Data Structure Analysis - Colleague's JSONL Data

**Date**: 2026-01-05  
**Author**: MCP Diploma Thesis Team  
**Data Source**: Colleague's scraped LeoWiki educational content

---

## 📁 File Organization

```
data/
├── jsonl/
│   ├── pages.jsonl         (2.0+ MB, 197 docs, 757 chunks)
│   └── media.jsonl         (2.0+ MB, 300 docs, 1523 chunks)
└── statistics/
    └── embedding_statistics.json (18 bytes)
```

**Note**: `media.jsonl` will be merged into `pages.jsonl` in future updates by colleague.

---

## 🔍 JSONL Structure - Line Format

Each line in the JSONL file is a complete JSON object:

```json
{
  "id": "pages_archive_exams_matura-2021_0",
  "text": "Title: ...\nNamespace: ...\n\n# Content...",
  "embedding": [3072 float values],
  "metadata": { ... }
}
```

### Key Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | string | Unique document identifier | `"pages_archive_exams_matura-2021_0"` |
| `text` | string | Full markdown content with title, namespace, headers | `"Title: Ablauf...\nNamespace: archive:exams\n\n# Content"` |
| `embedding` | float[] | 3072-dimensional vector from `text-embedding-3-large` | `[-0.0036, 0.0053, ...]` |
| `metadata` | object | Rich metadata (see below) | Various fields |

---

## 📋 Metadata Structure (Critical for RBAC!)

### Core Metadata Fields

```json
{
  "source": "archive_exams_matura-2021.md",
  "collection": "pages",
  "chunk_index": 0,
  "total_chunks": 9,
  "original_length": 6364,
  "embedding_model": "text-embedding-3-large",
  "created_at": "2026-01-04T15:07:39.344157"
}
```

### Frontmatter (RBAC-Critical!) 🔐

```json
{
  "frontmatter": {
    "title": "Ablauf und Durchführung der Matura 2020/21",
    "namespace": "archive:exams",
    "source": "leowiki",
    "page_id": "archive:exams:matura-2021",
    
    // ⭐ CRITICAL FOR RBAC:
    "access_level": "public",           // "public" | "student" | "teacher" | "admin"
    "content_type": "KNOWLEDGE",
    "freshness_score": 0.4,
    "freshness_category": "outdated",   // "current", "recent", "outdated"
    
    // Additional fields:
    "chunking_method": "recursive_header",
    "last_modified": "2023-09-04T19:17:37",
    "author": "it190207",
    "revision": 1693847857,
    "content_hash": "fc55bb828d7bf2bf7494b69357d65f50",
    "links_to": ["archive:org:termine-sose-2021"],
    "linked_from": ["archive:start"]
  }
}
```

---

## ⚠️ Important Questions About `source` Field

**Current Understanding**:
- `metadata.source` currently contains: `"archive_exams_matura-2021.md"` (the file name)
- User mentioned: *"only in the source field there will be no markdown content. it will contain the original source, but the field stays the same"*

**Question for User**:
What will the `source` field contain in future uploads?
- ✅ A) Original URL (e.g., `"https://leowiki.at/archive/exams/matura-2021"`)
- ✅ B) Source system identifier (e.g., `"leowiki"`)
- ✅ C) File path (e.g., `"archive/exams/matura-2021.md"`)
- ✅ D) Something else?

**Impact**: We need to validate this field format in the ingestion pipeline.

---

## 🎯 RBAC Implementation Fields

### Access Level Mapping

| `access_level` | Visible To | Description |
|----------------|------------|-------------|
| `public` | Everyone | Publicly accessible content |
| `student` | student, teacher, admin | Student-level content |
| `teacher` | teacher, admin | Teacher-only content |
| `admin` | admin only | Admin-only sensitive content |

### Qdrant Payload Structure

When inserting into Qdrant, we'll use:

```python
{
    "id": document["id"],
    "vector": document["embedding"],
    "payload": {
        # Core fields
        "text": document["text"],
        "source": document["metadata"]["source"],
        "collection": document["metadata"]["collection"],
        "chunk_index": document["metadata"]["chunk_index"],
        "total_chunks": document["metadata"]["total_chunks"],
        
        # RBAC fields (from frontmatter)
        "access_level": document["metadata"]["frontmatter"]["access_level"],
        "content_type": document["metadata"]["frontmatter"]["content_type"],
        "freshness_score": document["metadata"]["frontmatter"]["freshness_score"],
        "freshness_category": document["metadata"]["frontmatter"]["freshness_category"],
        
        # Additional searchable fields
        "title": document["metadata"]["frontmatter"]["title"],
        "namespace": document["metadata"]["frontmatter"]["namespace"],
        "author": document["metadata"]["frontmatter"]["author"],
        "last_modified": document["metadata"]["frontmatter"]["last_modified"]
    }
}
```

---

## 🚀 Performance Analysis: Embedding at End of Line

### Question: Is having embeddings at the end of each line a performance problem?

**Answer: NO! 🟢 No performance impact at all.**

### Technical Reasons:

1. **JSONL is line-based parsing**: 
   - Each line is read as a complete string
   - `json.loads()` parses the entire object at once
   - Field order doesn't affect parsing speed

2. **Sequential reading**:
   - We read line-by-line: `for line in file:`
   - Python's I/O is optimized for line-based reading
   - No random access needed

3. **Memory efficiency**:
   - We process one document at a time
   - Parse JSON → Extract fields → Insert to Qdrant → Release memory
   - Field order irrelevant

4. **Qdrant insertion**:
   - We extract `embedding`, `id`, and `payload` separately
   - Field order in source JSON doesn't matter

### Benchmark Estimate:
- **Reading 1000 documents**: ~2-3 seconds
- **Parsing JSON**: <1 second
- **Embedding extraction**: <0.1 second
- **Qdrant insertion** (batch): ~1-2 seconds per batch (100 docs)

**Total ingestion time for 757 pages**: ~30-45 seconds ⚡

---

## 📊 Embedding Statistics

From `embedding_statistics.json`:

```json
{
  "collections": {
    "pages": {
      "docs": 197,
      "chunks": 757
    },
    "media": {
      "docs": 300,
      "chunks": 1523
    }
  },
  "embedding_api": {
    "total_tokens": 741403,
    "total_requests": 24,
    "total_cost": 0.09638239
  },
  "timestamp": "2026-01-04T15:08:58.515924"
}
```

**Analysis**:
- **Total documents**: 497 (197 pages + 300 media)
- **Total chunks**: 2280 (757 + 1523)
- **Cost**: ~$0.096 USD (~10 cents)
- **Average chunk size**: ~325 tokens per chunk (741403 / 2280)

---

## 🔧 Data Ingestion Pipeline Design

### Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Colleague uploads JSONL via Tailscale SCP                   │
│     → scp pages.jsonl pi@raspberry:~/incoming/                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. Watchdog detects new file in /incoming/                     │
│     → Triggers ingestion script                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. Validation & Parsing                                        │
│     ✓ Check JSONL format                                        │
│     ✓ Validate required fields: id, text, embedding, metadata  │
│     ✓ Validate access_level: public|student|teacher|admin      │
│     ✓ Validate embedding dimensions (3072)                     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. Qdrant Insertion (Batch: 100 docs)                          │
│     → Collection: "educational_content"                         │
│     → Upsert with payload (RBAC fields included)                │
│     → Log success/failures                                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. Post-Processing                                             │
│     ✓ Move file to /processed/ (with timestamp)                │
│     ✓ Update statistics                                         │
│     ✓ Send notification (optional)                              │
└─────────────────────────────────────────────────────────────────┘
```

### Error Handling

```
┌─────────────────────────────────────────────────────────────────┐
│  Error Types & Actions                                          │
├─────────────────────────────────────────────────────────────────┤
│  • Invalid JSON → Move to /failed/, log error                   │
│  • Missing field → Skip document, log warning                   │
│  • Invalid access_level → Default to "public", log warning     │
│  • Qdrant connection error → Retry 3x, then fail               │
│  • Embedding dimension mismatch → Skip, log error              │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ Validation Checklist for Ingestion

```python
def validate_document(doc: dict) -> tuple[bool, str]:
    """Validate a single JSONL document."""
    
    # Required top-level fields
    if "id" not in doc:
        return False, "Missing 'id' field"
    if "text" not in doc:
        return False, "Missing 'text' field"
    if "embedding" not in doc:
        return False, "Missing 'embedding' field"
    if "metadata" not in doc:
        return False, "Missing 'metadata' field"
    
    # Validate embedding dimensions
    if len(doc["embedding"]) != 3072:
        return False, f"Invalid embedding dimensions: {len(doc['embedding'])} (expected 3072)"
    
    # Validate metadata structure
    metadata = doc["metadata"]
    if "frontmatter" not in metadata:
        return False, "Missing 'frontmatter' in metadata"
    
    # Validate RBAC field
    frontmatter = metadata["frontmatter"]
    valid_access_levels = {"public", "student", "teacher", "admin"}
    access_level = frontmatter.get("access_level", "public")
    
    if access_level not in valid_access_levels:
        # Default to public but log warning
        frontmatter["access_level"] = "public"
        return True, f"Warning: Invalid access_level '{access_level}', defaulting to 'public'"
    
    return True, "OK"
```

---

## 🎓 Thesis Contribution

### Research Questions Addressed

1. **RQ1: How can educational content be efficiently filtered based on user roles?**
   - ✅ Answer: Use `access_level` metadata + Qdrant filtering
   - Implementation: MCP tools filter by `user_role` in JWT token

2. **RQ2: What is the optimal data structure for RBAC-enabled vector search?**
   - ✅ Answer: JSONL with embedded metadata (access_level in frontmatter)
   - Benefit: Self-contained documents, easy ingestion, Qdrant-ready

3. **RQ3: How to automate data ingestion from multiple sources?**
   - ✅ Answer: Watchdog + JSONL pipeline + Tailscale secure upload
   - Scalability: Can handle 1000+ documents per upload

---

## 🚨 Action Items Before Starting Implementation

### High Priority

1. **Clarify `source` field format** with colleague:
   - What will it contain in future? (URL, system name, path?)
   - Do we need to validate format?

2. **Confirm `access_level` values**:
   - Are `public`, `student`, `teacher`, `admin` the only values?
   - Any additional roles needed?

3. **Test JSONL parsing**:
   - Write quick validation script to check all 757 pages
   - Ensure no malformed JSON

### Medium Priority

4. **Define Qdrant collection schema**:
   - Collection name: `educational_content`
   - Vector size: 3072
   - Distance metric: Cosine similarity

5. **Design MCP tool RBAC filters**:
   - How to handle multi-role users? (e.g., teacher + admin)
   - Hierarchical access? (admin sees everything)

6. **Error notification**:
   - How to notify on ingestion failures?
   - Email? Slack? Log file?

---

## 📝 Notes & Recommendations

### ✅ Good Things

1. **Embeddings pre-computed**: No need to generate embeddings server-side (fast ingestion)
2. **Rich metadata**: Excellent RBAC metadata (access_level, content_type, freshness)
3. **JSONL format**: Perfect for streaming, line-by-line processing
4. **Self-contained**: Each line is independent (easy to parallelize)

### ⚠️ Potential Issues

1. **No schema validation**: JSONL has no enforced schema - need validation code
2. **Large file size**: 2MB+ per file - need streaming parser (not load entire file)
3. **Media will merge into pages**: Need to handle this gracefully when it happens

### 🚀 Optimizations

1. **Batch insertion**: Insert 100 documents at a time to Qdrant (faster than 1-by-1)
2. **Parallel processing**: Use `multiprocessing` if files get >10MB
3. **Incremental updates**: Track `content_hash` to avoid re-inserting unchanged documents

---

## 🎯 Next Steps

1. ✅ **Data copied to correct directory** (`data/jsonl/`)
2. 🔄 **Await user confirmation on**:
   - `source` field format
   - Authentication decision (Caddy OAuth vs Scalekit)
3. 🚀 **Start Week 1 implementation**:
   - Copy backup code
   - Setup project structure
   - Create JSONL ingestion pipeline
   - Test with actual data

---

**Status**: ✅ Ready to proceed with implementation once user confirms authentication and source field format.
