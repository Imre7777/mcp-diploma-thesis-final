# Direct Search Benchmark Results

**Generated:** 2026-03-21T09:16:44.445033

**Embedding Model:** text-embedding-3-large

**Qdrant:** http://qdrant:6333

**Collection:** educational_content

**Queries:** 78

**Iterations:** 3


## Summary

| Metric | Mean (ms) | Median (ms) | P95 (ms) | Min (ms) | Max (ms) |
|--------|-----------|-------------|----------|----------|----------|
| Embedding | 181.8 | 174.8 | - | 144.3 | 434.4 |
| Search | 26.1 | 22.9 | - | 21.4 | 50.0 |
| **Total** | **207.9** | **199.7** | **263.6** | 167.1 | 459.7 |


## By Difficulty

| Difficulty | Count | Mean (ms) | Median (ms) |
|------------|-------|-----------|-------------|
| easy | 17 | 215.8 | 192.2 |
| medium | 40 | 203.7 | 202.5 |
| hard | 21 | 209.4 | 199.8 |


## Time Breakdown

- **Embedding generation:** 181.8 ms (87%)

- **Vector search:** 26.1 ms (13%)

- **Total:** 207.9 ms

