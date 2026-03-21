#!/bin/bash
# Docker STDIO Transport Test
# Runs MCP server in isolated container, tests STDIO latency
# Does NOT affect production system

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONTAINER_NAME="mcp-stdio-test-$$"  # Unique name with PID
ITERATIONS=${1:-10}

echo "============================================================"
echo "DOCKER STDIO TRANSPORT TEST"
echo "============================================================"
echo "Container: $CONTAINER_NAME (temporary)"
echo "Iterations: $ITERATIONS"
echo "Production system: UNAFFECTED"
echo "============================================================"

# Find the MCP server image (docker-compose prefixes with project name)
IMAGE_NAME=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "mcp.*server" | head -1)

if [ -z "$IMAGE_NAME" ]; then
    echo "ERROR: No MCP server image found"
    echo "Build it first: docker compose build mcp-server"
    exit 1
fi

echo "Using image: $IMAGE_NAME"

# Create a Python script to run inside the container
TEST_SCRIPT=$(cat <<'PYTHON_EOF'
import json
import statistics
import subprocess
import sys
import time

iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 10

print(f"\nRunning {iterations} STDIO tests...\n")

# MCP initialize request
init_request = json.dumps({
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "benchmark", "version": "1.0"}
    }
})

times = []
errors = 0

for i in range(iterations):
    start = time.perf_counter()
    try:
        proc = subprocess.Popen(
            ["python", "/app/main.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd="/app",
        )
        stdout, stderr = proc.communicate(
            input=(init_request + "\n").encode(),
            timeout=30
        )
        elapsed = time.perf_counter() - start
        
        if stdout and b"jsonrpc" in stdout:
            times.append(elapsed * 1000)
            print(f"  Test {i+1}: {elapsed*1000:.1f} ms")
        else:
            errors += 1
            if i == 0:
                print(f"  Test {i+1}: FAILED - {stderr.decode()[:100]}")
    except Exception as e:
        errors += 1
        print(f"  Test {i+1}: ERROR - {e}")

print("\n" + "="*50)
print("STDIO RESULTS")
print("="*50)

if times:
    result = {
        "transport": "STDIO (Docker)",
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
    
    # Output JSON for parsing
    print("\n---JSON_START---")
    print(json.dumps(result, indent=2))
    print("---JSON_END---")
else:
    print("  All tests failed!")
    sys.exit(1)
PYTHON_EOF
)

echo ""
echo "Starting isolated test container..."
echo ""

# Run test in isolated container
# - Uses same image as production
# - Different container name
# - No network (not needed for STDIO)
# - No volume mounts (isolated)
# - Removed after completion (--rm)
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
