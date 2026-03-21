# MCP Transport Comparison: STDIO vs HTTP

**Generated:** 2026-03-21T10:42:58  
**Test Environment:** Raspberry Pi 4B (Debian, Docker 24.x)  
**Iterations:** 20 per transport (+ 1 warm-up, not counted)  
**Success Rate:** 100% (40/40 requests)

## Methodology

### Test Setup
- **STDIO Test:** Isolated Docker container (`--network none`), FastMCP StdioTransport client
- **HTTP Test:** Public endpoint `https://leowiki-mcp.stream/health` via httpx client
- **Tool Tested:** `health_check` (minimal server-side processing)
- **Measurement:** Python `time.perf_counter()` (nanosecond precision)

### Test Procedure
1. Start isolated container (STDIO) / establish connection (HTTP)
2. Execute 1 warm-up request (discarded)
3. Execute 20 timed requests
4. Record individual latencies
5. Calculate statistics

## Measured Results

### STDIO Transport (Local Process Communication)

| Statistic | Value | Unit |
|-----------|------:|------|
| Mean | 17.94 | ms |
| Median | 17.90 | ms |
| Minimum | 17.74 | ms |
| Maximum | 18.48 | ms |
| Std Deviation | 0.18 | ms |
| Coefficient of Variation | 1.0% | - |

### HTTP Transport (Remote via TLS)

| Statistic | Value | Unit |
|-----------|------:|------|
| Mean | 113.12 | ms |
| Median | 109.95 | ms |
| Minimum | 108.63 | ms |
| Maximum | 142.93 | ms |
| Std Deviation | 7.98 | ms |
| Coefficient of Variation | 7.1% | - |

## Calculated Comparison

| Metric | Value | Calculation |
|--------|------:|-------------|
| **Speedup Factor** | 6.31x | HTTP_mean / STDIO_mean |
| **Absolute Overhead** | 95.18 ms | HTTP_mean - STDIO_mean |
| **Relative Overhead** | 530.7% | (HTTP_mean - STDIO_mean) / STDIO_mean × 100 |

## Statistical Observations

1. **STDIO Consistency:** Coefficient of variation = 1.0% (highly stable)
2. **HTTP Variability:** Coefficient of variation = 7.1% (network-induced variance)
3. **All 40 requests succeeded** (no timeouts, no errors)

## Limitations & Notes

- HTTP test includes: TLS negotiation, network latency, reverse proxy (Caddy), server processing
- STDIO test includes: IPC overhead, JSON-RPC serialization, server processing
- Individual component contributions (TLS, network, etc.) were **NOT measured separately**
- Tests run sequentially, not concurrently
- Results specific to this test environment (Raspberry Pi 4B)

## Raw Data

### HTTP Individual Measurements (20 iterations)
All values in milliseconds. Raw timing data available in accompanying JSON file.

### STDIO Individual Measurements (20 iterations)  
All values in milliseconds. Raw timing data available in accompanying JSON file.

## Reproducibility

To reproduce these results:

```bash
# On the Raspberry Pi with Docker running:
cd /home/imreo/mcp-diploma-thesis-final
./scripts/benchmark/full_transport_compare.sh 20
```

Requirements:
- Docker with mcp-server image built
- Network access to https://leowiki-mcp.stream
- Python 3.11+ with httpx installed

## JSON Data Reference

```json
{
  "timestamp": "2026-03-21T10:42:58.373090",
  "iterations": 20,
  "http": {
    "transport": "HTTP",
    "mean_ms": 113.11839004047215,
    "median_ms": 109.94717665016651,
    "min_ms": 108.62946696579456,
    "max_ms": 142.9339088499546,
    "stdev_ms": 7.975185506932293,
    "successful": 20,
    "iterations": 20
  },
  "stdio": {
    "transport": "STDIO",
    "mean_ms": 17.93661192059517,
    "median_ms": 17.899069003760815,
    "min_ms": 17.737405374646187,
    "max_ms": 18.48400291055441,
    "stdev_ms": 0.18054485423861003,
    "successful": 20,
    "iterations": 20
  },
  "analysis": {
    "speedup": 6.306563945367374,
    "overhead_ms": 95.18177811987698
  }
}
```
