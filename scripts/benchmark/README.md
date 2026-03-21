# MCP Server Benchmark Suite

Benchmark scripts for comparing MCP transport performance and measuring semantic search latency.

## Query Catalog

Uses **78 ground-truth Q&A pairs** from the LeoWiki evaluation catalog:
- 17 easy questions
- 33 medium questions  
- 15 hard questions (+ 13 unclassified)

Source: `data/benchmark/query_catalog.json`

## Scripts

### 1. Direct Search Benchmark (`benchmark_search.py`)

Tests the "pure" search performance without MCP protocol overhead:
- Embedding generation time (OpenAI API)
- Vector search time (Qdrant)
- Total query latency

```bash
# Full benchmark (78 queries)
python scripts/benchmark/benchmark_search.py

# Quick test (10 queries)
python scripts/benchmark/benchmark_search.py --limit 10

# Multiple iterations for statistics
python scripts/benchmark/benchmark_search.py --iterations 3

# Against local Qdrant
python scripts/benchmark/benchmark_search.py --qdrant http://localhost:6333
```

**Requirements:**
- `OPENAI_API_KEY` environment variable
- Running Qdrant instance

### 2. MCP Transport Benchmark (`run_benchmark.py`)

Compares STDIO vs HTTP transport:

```bash
# HTTP transport (against running server)
python scripts/benchmark/run_benchmark.py --transport http --url http://localhost:8000

# STDIO transport (runs server as subprocess)
python scripts/benchmark/run_benchmark.py --transport stdio

# Compare both
python scripts/benchmark/run_benchmark.py --transport both

# Quick test
python scripts/benchmark/run_benchmark.py --transport http --limit 10
```

**Requirements:**
- For HTTP: Running MCP server
- For STDIO: Local Python environment with all dependencies

## Output

Results are saved to `data/benchmark/`:
- `*_benchmark_YYYYMMDD_HHMMSS.json` - Raw timing data
- `*_benchmark_YYYYMMDD_HHMMSS.md` - Markdown report

## Expected Results

Typical latencies on Raspberry Pi:

| Component | Expected |
|-----------|----------|
| Embedding (OpenAI) | 200-500 ms |
| Vector Search (Qdrant) | 10-50 ms |
| HTTP Overhead | 50-200 ms |
| STDIO Overhead | ~0 ms |

## Interpretation

- **Embedding** is the bottleneck (external API call)
- **STDIO** will be faster (no network overhead)
- **HTTP** includes TLS, OAuth validation, SSE framing
