#!/bin/bash
# Docker STDIO Warm Request Test
# Measures per-request latency (not cold start)
# Uses FastMCP client for fair comparison with HTTP
# Does NOT affect production system

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONTAINER_NAME="mcp-stdio-warm-test-$$"
ITERATIONS=${1:-10}

echo "============================================================"
echo "DOCKER STDIO WARM REQUEST TEST"
echo "============================================================"
echo "Container: $CONTAINER_NAME (temporary)"
echo "Iterations: $ITERATIONS"
echo "Mode: Warm requests (server stays running)"
echo "Production system: UNAFFECTED"
echo "============================================================"

# Find the MCP server image
IMAGE_NAME=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "mcp.*server" | head -1)

if [ -z "$IMAGE_NAME" ]; then
    echo "ERROR: No MCP server image found"
    exit 1
fi

echo "Using image: $IMAGE_NAME"

# Test script that keeps connection open
TEST_SCRIPT=$(cat <<'PYTHON_EOF'
import asyncio
import json
import statistics
import sys
import time
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 10

async def run_warm_test():
    print(f"\nConnecting to STDIO server...")
    
    # Use FastMCP client with explicit STDIO transport
    transport = StdioTransport(
        command="python",
        args=["/app/main.py"],
        cwd="/app"
    )
    
    async with Client(transport) as client:
        print("Connected! Running warm request tests...\n")
        
        times = []
        errors = 0
        
        # Warm-up request (not counted)
        print("  Warm-up request...")
        try:
            await client.call_tool("health_check", {})
            print("  Warm-up complete.\n")
        except Exception as e:
            print(f"  Warm-up failed: {e}")
        
        # Actual test requests
        for i in range(iterations):
            start = time.perf_counter()
            try:
                result = await client.call_tool("health_check", {})
                elapsed = time.perf_counter() - start
                times.append(elapsed * 1000)
                print(f"  Request {i+1}: {elapsed*1000:.1f} ms")
            except Exception as e:
                errors += 1
                print(f"  Request {i+1}: ERROR - {e}")
        
        print("\n" + "="*50)
        print("STDIO WARM REQUEST RESULTS")
        print("="*50)
        
        if times:
            result = {
                "transport": "STDIO (Docker, warm)",
                "iterations": iterations,
                "successful": len(times),
                "errors": errors,
                "mean_ms": statistics.mean(times),
                "median_ms": statistics.median(times),
                "min_ms": min(times),
                "max_ms": max(times),
                "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
            }
            print(f"  Mean:   {result['mean_ms']:.1f} ms")
            print(f"  Median: {result['median_ms']:.1f} ms")
            print(f"  Min:    {result['min_ms']:.1f} ms")
            print(f"  Max:    {result['max_ms']:.1f} ms")
            print(f"  StdDev: {result['stdev_ms']:.1f} ms")
            print(f"\n  Success: {len(times)}/{iterations}")
            
            print("\n---JSON_START---")
            print(json.dumps(result, indent=2))
            print("---JSON_END---")
        else:
            print("  All tests failed!")
            sys.exit(1)

asyncio.run(run_warm_test())
PYTHON_EOF
)

echo ""
echo "Starting isolated test container..."
echo ""

# Run test in isolated container
docker run --rm \
    --name "$CONTAINER_NAME" \
    --network none \
    -e OPENAI_API_KEY="${OPENAI_API_KEY:-dummy}" \
    -e QDRANT_URL="http://localhost:6333" \
    "$IMAGE_NAME" \
    python -c "$TEST_SCRIPT" "$ITERATIONS"

echo ""
echo "============================================================"
echo "Test complete. Container removed automatically."
echo "Production system was NOT affected."
echo "============================================================"
