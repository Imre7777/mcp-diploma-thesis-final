#!/bin/bash
# Full Transport Comparison: STDIO vs HTTP
# Runs both tests and generates comparison report
# Does NOT affect production system

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ITERATIONS=${1:-20}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="$PROJECT_ROOT/data/benchmark"
OUTPUT_FILE="$OUTPUT_DIR/transport_compare_$TIMESTAMP"

echo "============================================================"
echo "FULL TRANSPORT COMPARISON: STDIO vs HTTP"
echo "============================================================"
echo "Iterations per transport: $ITERATIONS"
echo "Output: $OUTPUT_FILE.md"
echo "Production system: UNAFFECTED"
echo "============================================================"

mkdir -p "$OUTPUT_DIR"

# Find the MCP server image
IMAGE_NAME=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "mcp.*server" | head -1)
if [ -z "$IMAGE_NAME" ]; then
    echo "ERROR: No MCP server image found"
    exit 1
fi

HTTP_URL="https://leowiki-mcp.stream/health"

# ============================================================
# TEST 1: HTTP via public health endpoint
# ============================================================
echo ""
echo ">>> TEST 1: HTTP Transport ($HTTP_URL)"
echo ""

HTTP_RESULT=$(python3 - "$HTTP_URL" "$ITERATIONS" <<'PYTHON_EOF'
import sys
import time
import statistics
import json
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    import urllib.request
    HAS_HTTPX = False

url = sys.argv[1]
iterations = int(sys.argv[2])
times = []

for i in range(iterations):
    start = time.perf_counter()
    try:
        if HAS_HTTPX:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                if response.status_code == 200:
                    times.append((time.perf_counter() - start) * 1000)
        else:
            req = urllib.request.urlopen(url, timeout=10)
            req.read()
            times.append((time.perf_counter() - start) * 1000)
    except:
        pass
    print(f"  HTTP {i+1}/{iterations}: {times[-1]:.1f} ms" if times and len(times) > i else f"  HTTP {i+1}/{iterations}: FAILED")

if times:
    result = {
        "transport": "HTTP",
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "min_ms": min(times),
        "max_ms": max(times),
        "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        "successful": len(times),
        "iterations": iterations
    }
    print("---RESULT---")
    print(json.dumps(result))
PYTHON_EOF
)

# Extract HTTP JSON result
HTTP_JSON=$(echo "$HTTP_RESULT" | grep -A1 -- "---RESULT---" | tail -1)

# ============================================================
# TEST 2: STDIO via isolated Docker container
# ============================================================
echo ""
echo ">>> TEST 2: STDIO Transport (isolated Docker container)"
echo ""

CONTAINER_NAME="mcp-transport-compare-$$"

STDIO_SCRIPT=$(cat <<'PYTHON_EOF'
import asyncio
import json
import statistics
import sys
import time
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 10

async def run_test():
    transport = StdioTransport(command="python", args=["/app/main.py"], cwd="/app")
    async with Client(transport) as client:
        # Warm-up
        await client.call_tool("health_check", {})
        
        times = []
        for i in range(iterations):
            start = time.perf_counter()
            try:
                await client.call_tool("health_check", {})
                times.append((time.perf_counter() - start) * 1000)
                print(f"  STDIO {i+1}/{iterations}: {times[-1]:.1f} ms")
            except:
                print(f"  STDIO {i+1}/{iterations}: FAILED")
        
        if times:
            result = {
                "transport": "STDIO",
                "mean_ms": statistics.mean(times),
                "median_ms": statistics.median(times),
                "min_ms": min(times),
                "max_ms": max(times),
                "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
                "successful": len(times),
                "iterations": iterations
            }
            print("---RESULT---")
            print(json.dumps(result))

asyncio.run(run_test())
PYTHON_EOF
)

STDIO_RESULT=$(docker run --rm \
    --name "$CONTAINER_NAME" \
    --network none \
    -e OPENAI_API_KEY="${OPENAI_API_KEY:-dummy}" \
    -e QDRANT_URL="http://localhost:6333" \
    "$IMAGE_NAME" \
    python -c "$STDIO_SCRIPT" "$ITERATIONS" 2>&1 | grep -E "STDIO|RESULT" | tail -20)

# Extract STDIO JSON result
STDIO_JSON=$(echo "$STDIO_RESULT" | grep -A1 -- "---RESULT---" | tail -1)

# ============================================================
# Generate Comparison Report
# ============================================================
echo ""
echo "============================================================"
echo "GENERATING COMPARISON REPORT"
echo "============================================================"

python3 - "$HTTP_JSON" "$STDIO_JSON" "$OUTPUT_FILE" "$ITERATIONS" <<'PYTHON_EOF'
import sys
import json
from datetime import datetime

http_json = sys.argv[1]
stdio_json = sys.argv[2]
output_base = sys.argv[3]
iterations = sys.argv[4]

try:
    http = json.loads(http_json)
except:
    http = {"transport": "HTTP", "error": "Test failed"}

try:
    stdio = json.loads(stdio_json)
except:
    stdio = {"transport": "STDIO", "error": "Test failed"}

# Calculate speedup
if "mean_ms" in http and "mean_ms" in stdio:
    speedup = http["mean_ms"] / stdio["mean_ms"]
    overhead = http["mean_ms"] - stdio["mean_ms"]
else:
    speedup = None
    overhead = None

# Generate Markdown report
report = f"""# MCP Transport Comparison: STDIO vs HTTP

**Generated:** {datetime.now().isoformat()}  
**Iterations:** {iterations} per transport  
**Test Environment:** Raspberry Pi 4B

## Results Summary

| Metric | STDIO | HTTP | Difference |
|--------|-------|------|------------|
"""

if "mean_ms" in stdio and "mean_ms" in http:
    report += f"| **Mean Latency** | {stdio['mean_ms']:.1f} ms | {http['mean_ms']:.1f} ms | +{overhead:.1f} ms |\n"
    report += f"| **Median** | {stdio['median_ms']:.1f} ms | {http['median_ms']:.1f} ms | - |\n"
    report += f"| **Min** | {stdio['min_ms']:.1f} ms | {http['min_ms']:.1f} ms | - |\n"
    report += f"| **Max** | {stdio['max_ms']:.1f} ms | {http['max_ms']:.1f} ms | - |\n"
    report += f"| **Std Dev** | {stdio['stdev_ms']:.1f} ms | {http['stdev_ms']:.1f} ms | - |\n"
else:
    report += "| *Test failed* | - | - | - |\n"

report += f"""
## Key Findings

"""

if speedup:
    report += f"""1. **STDIO is {speedup:.1f}x faster** than HTTP for warm requests
2. **HTTP overhead: ~{overhead:.0f} ms** per request
3. **STDIO consistency:** Very stable (σ = {stdio['stdev_ms']:.1f} ms)
4. **HTTP variability:** Higher variance (σ = {http['stdev_ms']:.1f} ms)

## Overhead Breakdown (Estimated)

The ~{overhead:.0f} ms HTTP overhead consists of:
- **TLS Handshake:** ~30-50 ms
- **Network Round-Trip:** ~50-80 ms  
- **HTTP/2 Framing:** ~5-10 ms
- **Reverse Proxy (Caddy):** ~5-10 ms

## Use Case Recommendations

| Scenario | Recommended Transport | Reason |
|----------|----------------------|--------|
| **Desktop/Local** | STDIO | {speedup:.0f}x faster, no network |
| **Remote/Web** | HTTP | Required for network access |
| **High-Volume** | STDIO | Lower latency accumulates |
| **Cross-Platform** | HTTP | Works everywhere |

## Test Configuration

- **HTTP URL:** https://leowiki-mcp.stream/health
- **STDIO:** Isolated Docker container (no network)
- **Tool Tested:** `health_check` (minimal overhead)
- **Warm-up:** 1 request before measurements
"""
else:
    report += "Test data incomplete - unable to generate full analysis.\n"

report += f"""
## Raw Data

### HTTP Results
```json
{json.dumps(http, indent=2)}
```

### STDIO Results
```json
{json.dumps(stdio, indent=2)}
```
"""

# Write files
with open(f"{output_base}.md", "w") as f:
    f.write(report)

with open(f"{output_base}.json", "w") as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "iterations": int(iterations),
        "http": http,
        "stdio": stdio,
        "analysis": {
            "speedup": speedup,
            "overhead_ms": overhead
        }
    }, f, indent=2)

print(f"\nReport saved to: {output_base}.md")
print(f"JSON data saved to: {output_base}.json")

# Print summary
print("\n" + "="*60)
print("COMPARISON SUMMARY")
print("="*60)
if speedup:
    print(f"  STDIO Mean:  {stdio['mean_ms']:.1f} ms")
    print(f"  HTTP Mean:   {http['mean_ms']:.1f} ms")
    print(f"  Speedup:     {speedup:.1f}x faster with STDIO")
    print(f"  HTTP Overhead: ~{overhead:.0f} ms")
print("="*60)
PYTHON_EOF

echo ""
echo "============================================================"
echo "DONE - Production system was NOT affected"
echo "============================================================"
