# MCP Server Performance Benchmark Results

**Benchmark Date:** 2026-03-21  
**Server:** LeoWiki MCP Server v2.0.1  
**Location:** Raspberry Pi (Production)  
**Test Suite:** 78 Ground-Truth Q&A Pairs × 3 Iterations = 234 Requests

---

## Executive Summary

The semantic search pipeline achieves a **mean response time of 207.9 ms** per query, with **87% of the time spent on embedding generation** (OpenAI API) and only **13% on vector search** (Qdrant).

| Metric | Value |
|--------|-------|
| Mean Latency | 207.9 ms |
| Median Latency | 199.7 ms |
| P95 Latency | 263.6 ms |
| Error Rate | 0% |

---

## Test Configuration

### Hardware
- **Server:** Raspberry Pi 4 (8GB RAM)
- **Storage:** microSD
- **Network:** Tailscale VPN / Public HTTPS

### Software Stack
- **MCP Protocol:** FastMCP 3.0.1
- **Vector Database:** Qdrant (Docker)
- **Embedding Model:** OpenAI text-embedding-3-large (3072 dimensions)
- **Reverse Proxy:** Caddy (TLS, HTTP/2)

### Query Catalog
- **Total Queries:** 78 ground-truth Q&A pairs
- **Source:** LeoWiki educational content (HTL Leonding)
- **Difficulty Distribution:**
  - Easy: 17 queries (22%)
  - Medium: 40 queries (51%)
  - Hard: 21 queries (27%)
- **Verification:** Each answer verified against source documents

---

## Performance Results

### Overall Latency Distribution

| Metric | Mean (ms) | Median (ms) | P95 (ms) | Min (ms) | Max (ms) |
|--------|-----------|-------------|----------|----------|----------|
| **Embedding Generation** | 181.8 | 174.8 | - | 144.3 | 434.4 |
| **Vector Search** | 26.1 | 22.9 | - | 21.4 | 50.0 |
| **Total** | **207.9** | **199.7** | **263.6** | 167.1 | 459.7 |

### Time Breakdown

```
┌─────────────────────────────────────────────────────────────┐
│                    Query Processing Time                     │
├─────────────────────────────────────────────────────────────┤
│ Embedding (OpenAI API)  ████████████████████████████  87%   │
│ Vector Search (Qdrant)  ████                          13%   │
└─────────────────────────────────────────────────────────────┘
```

- **Embedding Generation:** 181.8 ms (87%) - External API call to OpenAI
- **Vector Search:** 26.1 ms (13%) - Local Qdrant query over 6,082 documents

### Performance by Query Difficulty

| Difficulty | Count | Mean (ms) | Median (ms) |
|------------|-------|-----------|-------------|
| Easy | 17 | 215.8 | 192.2 |
| Medium | 40 | 203.7 | 202.5 |
| Hard | 21 | 209.4 | 199.8 |

**Observation:** Query difficulty does not significantly impact latency. This is expected since:
- Embedding generation time is consistent regardless of query complexity
- Vector search uses cosine similarity which has O(n) complexity with HNSW index

---

## Component Analysis

### 1. Embedding Generation (OpenAI API)

| Metric | Value |
|--------|-------|
| Model | text-embedding-3-large |
| Dimensions | 3072 |
| Mean Latency | 181.8 ms |
| Bottleneck | Yes (87% of total time) |

**Analysis:** The OpenAI embedding API is the primary bottleneck. This is an external network call that cannot be optimized without:
- Caching frequently used queries
- Using a local embedding model
- Batch processing multiple queries

### 2. Vector Search (Qdrant)

| Metric | Value |
|--------|-------|
| Documents | 6,082 |
| Index Type | HNSW |
| Distance Metric | Cosine |
| Mean Latency | 26.1 ms |
| Median Latency | 22.9 ms |

**Analysis:** Qdrant performs excellently:
- Sub-30ms searches over 6,000+ documents
- Consistent performance (low variance)
- Could scale to 100,000+ documents with similar latency

### 3. Network Overhead (Not Measured Separately)

When accessing via HTTP (production), additional latency includes:
- TLS handshake: ~20-50 ms (first request)
- OAuth token validation: ~10-30 ms
- SSE framing: ~5-10 ms

---

## Comparison: STDIO vs HTTP Transport

| Transport | Use Case | Estimated Latency |
|-----------|----------|-------------------|
| **STDIO** | Local/Desktop apps | ~210 ms (pure search) |
| **HTTP** | Remote/Web clients | ~280-350 ms (+ network + auth) |

**Note:** STDIO transport eliminates network overhead but requires local server execution.

---

## Recommendations

### For Production Use
1. **Current performance is acceptable** for interactive use (< 500ms target)
2. **Consider query caching** for frequently asked questions
3. **Monitor P95 latency** as document count grows

### For Future Optimization
1. **Local embedding model** would reduce latency by ~150ms but increase server load
2. **Batch embedding** for bulk ingestion scenarios
3. **Edge caching** for static content queries

---

## Raw Data

Full benchmark data available at:
- JSON: `data/benchmark/search_benchmark_20260321_091644.json`
- Query Catalog: `data/benchmark/query_catalog.json` (78 Q&A pairs)

---

## Methodology

### Test Execution
```bash
python scripts/benchmark/benchmark_search.py --iterations 3
```

### Measurements
- Each query executed 3 times
- Timing via `time.perf_counter()` (microsecond precision)
- Warm start (services pre-initialized)

### Environment
- No concurrent load during benchmark
- Stable network conditions
- Production Qdrant instance (6,082 documents)

---

**Generated by:** MCP Server Benchmark Suite  
**Repository:** https://github.com/Imre7777/mcp-diploma-thesis-final
