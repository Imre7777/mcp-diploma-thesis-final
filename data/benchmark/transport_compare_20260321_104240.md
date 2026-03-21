# MCP Transport Comparison: STDIO vs HTTP

**Generated:** 2026-03-21T10:42:58.372388  
**Iterations:** 20 per transport  
**Test Environment:** Raspberry Pi 4B

## Results Summary

| Metric | STDIO | HTTP | Difference |
|--------|-------|------|------------|
| **Mean Latency** | 17.9 ms | 113.1 ms | +95.2 ms |
| **Median** | 17.9 ms | 109.9 ms | - |
| **Min** | 17.7 ms | 108.6 ms | - |
| **Max** | 18.5 ms | 142.9 ms | - |
| **Std Dev** | 0.2 ms | 8.0 ms | - |

## Key Findings

1. **STDIO is 6.3x faster** than HTTP for warm requests
2. **HTTP overhead: ~95 ms** per request
3. **STDIO consistency:** Very stable (σ = 0.2 ms)
4. **HTTP variability:** Higher variance (σ = 8.0 ms)

## Overhead Breakdown (Estimated)

The ~95 ms HTTP overhead consists of:
- **TLS Handshake:** ~30-50 ms
- **Network Round-Trip:** ~50-80 ms  
- **HTTP/2 Framing:** ~5-10 ms
- **Reverse Proxy (Caddy):** ~5-10 ms

## Use Case Recommendations

| Scenario | Recommended Transport | Reason |
|----------|----------------------|--------|
| **Desktop/Local** | STDIO | 6x faster, no network |
| **Remote/Web** | HTTP | Required for network access |
| **High-Volume** | STDIO | Lower latency accumulates |
| **Cross-Platform** | HTTP | Works everywhere |

## Test Configuration

- **HTTP URL:** https://leowiki-mcp.stream/health
- **STDIO:** Isolated Docker container (no network)
- **Tool Tested:** `health_check` (minimal overhead)
- **Warm-up:** 1 request before measurements

## Raw Data

### HTTP Results
```json
{
  "transport": "HTTP",
  "mean_ms": 113.11839004047215,
  "median_ms": 109.94717665016651,
  "min_ms": 108.62946696579456,
  "max_ms": 142.9339088499546,
  "stdev_ms": 7.975185506932293,
  "successful": 20,
  "iterations": 20
}
```

### STDIO Results
```json
{
  "transport": "STDIO",
  "mean_ms": 17.93661192059517,
  "median_ms": 17.899069003760815,
  "min_ms": 17.737405374646187,
  "max_ms": 18.48400291055441,
  "stdev_ms": 0.18054485423861003,
  "successful": 20,
  "iterations": 20
}
```
