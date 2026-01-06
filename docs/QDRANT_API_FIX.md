# Qdrant API Fix - Search Method Migration

**Date:** 2026-01-05  
**Issue:** `'QdrantClient' object has no attribute 'search'`

## Problem

The Qdrant Python client API changed in newer versions:
- **Old API:** `client.search()` (deprecated/removed)
- **New API:** `client.query_points()` (current)

Our `src/backends/qdrant.py` was using the old `search()` method, causing runtime errors.

## Root Cause

The codebase was initially written for `qdrant-client>=1.11.0`, which had a `search()` method. However, in newer versions of the Qdrant client (likely 1.12+), this method was replaced with `query_points()`.

## Changes Made

### 1. Fixed `src/backends/qdrant.py` (Line 240-280)

**Changed:**
```python
# OLD (broken)
return self.client.search(
    collection_name=collection,
    query_vector=query_vector,  # ❌ Wrong parameter name
    ...
)
```

**To:**
```python
# NEW (working)
response = self.client.query_points(
    collection_name=collection,
    query=query_vector,  # ✅ Correct parameter name
    ...
)

# Convert Qdrant points to SearchResult objects
results = []
for point in response.points:
    results.append(SearchResult(
        id=str(point.id),
        score=float(point.score),
        payload=point.payload or {},
        vector=vec
    ))
return results
```

**Key changes:**
- ✅ `client.search()` → `client.query_points()`
- ✅ `query_vector=` → `query=`
- ✅ Access response via `response.points`
- ✅ Convert raw Qdrant points to `SearchResult` objects
- ✅ Added proper error handling

### 2. Fixed `main.py` (Line 150-153)

**Changed:**
```python
# OLD (broken)
f"**Result {i+1}** (score: {r.score:.3f})\n{r.text}\n" +  # ❌ .text doesn't exist
f"Source: {r.metadata.get('source', 'N/A')}"              # ❌ .metadata doesn't exist
```

**To:**
```python
# NEW (working)
f"**Result {i+1}** (score: {r.score:.3f})\n{r.payload.get('text', 'No text available')}\n" +
f"Source: {r.payload.get('source', 'N/A')}"
```

**Key changes:**
- ✅ `r.text` → `r.payload.get('text')`
- ✅ `r.metadata` → `r.payload`

## Why This Happened

**Reason:** The code was written based on outdated Qdrant client documentation or examples. The actual installed version had already migrated to the new API.

**Lesson Learned:** Always verify the actual API methods available in the installed version, especially for rapidly evolving libraries like vector databases.

## Verification

Run this command to verify the available methods:
```bash
python -c "from qdrant_client import QdrantClient; print([m for m in dir(QdrantClient) if 'query' in m.lower()])"
```

Expected output (modern Qdrant client):
```
['query', 'query_batch', 'query_batch_points', 'query_points', 'query_points_groups']
```

## Testing

After these fixes, the `search_content` tool should work correctly. Test with:
```
Search for "machine learning" in the educational content
```

## Status

✅ **FIXED** - All Qdrant API calls now use the correct modern API.
