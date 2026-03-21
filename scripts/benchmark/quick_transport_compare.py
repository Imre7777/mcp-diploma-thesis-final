#!/usr/bin/env python3
"""
Quick Transport Comparison: STDIO vs HTTP

A minimal script to compare MCP transport latencies without affecting
the running production system.

- HTTP: Tests public /health endpoint (no auth required)
- STDIO: Runs server locally as subprocess, sends health check

Usage:
    python scripts/benchmark/quick_transport_compare.py
    
    # Custom iterations
    python scripts/benchmark/quick_transport_compare.py --iterations 20
    
    # HTTP only (no local server needed)
    python scripts/benchmark/quick_transport_compare.py --http-only

No dependencies beyond standard library + httpx.
Does NOT touch Docker or production services.
"""

import argparse
import asyncio
import json
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Try to import httpx, fall back to urllib if not available
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    import urllib.request
    HAS_HTTPX = False


def test_http_latency(url: str, iterations: int = 10) -> dict:
    """Test HTTP latency via health endpoint."""
    print(f"\n{'='*50}")
    print(f"HTTP Transport Test")
    print(f"URL: {url}")
    print(f"Iterations: {iterations}")
    print(f"{'='*50}")
    
    times = []
    errors = 0
    
    for i in range(iterations):
        start = time.perf_counter()
        try:
            if HAS_HTTPX:
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(url)
                    if response.status_code == 200:
                        elapsed = time.perf_counter() - start
                        times.append(elapsed * 1000)  # Convert to ms
                    else:
                        errors += 1
            else:
                req = urllib.request.urlopen(url, timeout=10)
                _ = req.read()
                elapsed = time.perf_counter() - start
                times.append(elapsed * 1000)
        except Exception as e:
            errors += 1
            print(f"  Error on iteration {i+1}: {e}")
        
        # Progress dot
        print(".", end="", flush=True)
    
    print()  # Newline after dots
    
    if times:
        return {
            "transport": "HTTP",
            "url": url,
            "iterations": iterations,
            "successful": len(times),
            "errors": errors,
            "times_ms": times,
            "mean_ms": statistics.mean(times),
            "median_ms": statistics.median(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        }
    else:
        return {"transport": "HTTP", "error": "All requests failed", "errors": errors}


def test_stdio_latency(iterations: int = 10) -> dict:
    """Test STDIO latency by running server as subprocess."""
    print(f"\n{'='*50}")
    print(f"STDIO Transport Test")
    print(f"Iterations: {iterations}")
    print(f"{'='*50}")
    
    # Find main.py
    project_root = Path(__file__).parent.parent.parent
    main_py = project_root / "main.py"
    
    if not main_py.exists():
        return {"transport": "STDIO", "error": f"main.py not found at {main_py}"}
    
    times = []
    errors = 0
    
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
    
    for i in range(iterations):
        start = time.perf_counter()
        try:
            # Run server as subprocess with timeout
            proc = subprocess.Popen(
                [sys.executable, str(main_py)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(project_root),
            )
            
            # Send initialize request
            stdout, stderr = proc.communicate(
                input=(init_request + "\n").encode(),
                timeout=10
            )
            
            elapsed = time.perf_counter() - start
            
            # Check if we got a valid response
            if stdout and b"jsonrpc" in stdout:
                times.append(elapsed * 1000)
            else:
                errors += 1
                if i == 0:  # Only print first error
                    print(f"\n  No valid response. stderr: {stderr.decode()[:200]}")
            
        except subprocess.TimeoutExpired:
            proc.kill()
            errors += 1
        except Exception as e:
            errors += 1
            if i == 0:
                print(f"\n  Error: {e}")
        
        # Progress dot
        print(".", end="", flush=True)
    
    print()  # Newline after dots
    
    if times:
        return {
            "transport": "STDIO",
            "iterations": iterations,
            "successful": len(times),
            "errors": errors,
            "times_ms": times,
            "mean_ms": statistics.mean(times),
            "median_ms": statistics.median(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        }
    else:
        return {"transport": "STDIO", "error": "All requests failed", "errors": errors}


def test_stdio_with_fastmcp(iterations: int = 10) -> dict:
    """Test STDIO using FastMCP client (more accurate)."""
    try:
        from fastmcp import Client
    except ImportError:
        return {"transport": "STDIO (FastMCP)", "error": "fastmcp not installed"}
    
    print(f"\n{'='*50}")
    print(f"STDIO Transport Test (FastMCP Client)")
    print(f"Iterations: {iterations}")
    print(f"{'='*50}")
    
    project_root = Path(__file__).parent.parent.parent
    main_py = project_root / "main.py"
    
    if not main_py.exists():
        return {"transport": "STDIO", "error": f"main.py not found at {main_py}"}
    
    times = []
    errors = 0
    
    async def run_test():
        nonlocal times, errors
        
        try:
            # Use FastMCP client to connect via STDIO
            async with Client(f"python {main_py}") as client:
                print("  Connected to STDIO server")
                
                for i in range(iterations):
                    start = time.perf_counter()
                    try:
                        # Call health_check tool
                        result = await client.call_tool("health_check", {})
                        elapsed = time.perf_counter() - start
                        times.append(elapsed * 1000)
                    except Exception as e:
                        errors += 1
                        if i == 0:
                            print(f"\n  Tool call error: {e}")
                    
                    print(".", end="", flush=True)
                    
        except Exception as e:
            print(f"\n  Connection error: {e}")
            errors = iterations
    
    asyncio.run(run_test())
    print()
    
    if times:
        return {
            "transport": "STDIO (FastMCP)",
            "iterations": iterations,
            "successful": len(times),
            "errors": errors,
            "times_ms": times,
            "mean_ms": statistics.mean(times),
            "median_ms": statistics.median(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        }
    else:
        return {"transport": "STDIO (FastMCP)", "error": "All requests failed", "errors": errors}


def print_comparison(results: list[dict]):
    """Print comparison table."""
    print(f"\n{'='*60}")
    print("TRANSPORT COMPARISON RESULTS")
    print(f"{'='*60}")
    
    print(f"\n{'Transport':<20} {'Mean (ms)':<12} {'Median (ms)':<12} {'Min (ms)':<10} {'Max (ms)':<10}")
    print("-" * 64)
    
    valid_results = []
    for r in results:
        if "error" in r:
            print(f"{r['transport']:<20} ERROR: {r['error']}")
        else:
            print(f"{r['transport']:<20} {r['mean_ms']:<12.1f} {r['median_ms']:<12.1f} {r['min_ms']:<10.1f} {r['max_ms']:<10.1f}")
            valid_results.append(r)
    
    # Calculate difference if we have both
    if len(valid_results) == 2:
        r1, r2 = valid_results
        diff = abs(r1['mean_ms'] - r2['mean_ms'])
        faster = r1 if r1['mean_ms'] < r2['mean_ms'] else r2
        slower = r2 if r1['mean_ms'] < r2['mean_ms'] else r1
        
        print(f"\n{'='*60}")
        print(f"ANALYSIS")
        print(f"{'='*60}")
        print(f"  {faster['transport']} is {diff:.1f} ms faster than {slower['transport']}")
        print(f"  Speedup: {slower['mean_ms'] / faster['mean_ms']:.2f}x")
        
        if "HTTP" in slower['transport']:
            print(f"\n  HTTP overhead breakdown (estimated):")
            print(f"    - TLS handshake:    ~30-50 ms")
            print(f"    - Network latency:  ~{diff - 50:.0f} ms")
            print(f"    - Total overhead:   ~{diff:.0f} ms")


def save_results(results: list[dict], output_dir: Path):
    """Save results to file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON
    json_path = output_dir / f"transport_compare_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump({
            "timestamp": timestamp,
            "results": results,
        }, f, indent=2)
    print(f"\nResults saved to: {json_path}")
    
    return json_path


def main():
    parser = argparse.ArgumentParser(description="Quick Transport Comparison")
    parser.add_argument("--iterations", type=int, default=10, help="Iterations per test")
    parser.add_argument("--http-only", action="store_true", help="Test HTTP only")
    parser.add_argument("--stdio-only", action="store_true", help="Test STDIO only")
    parser.add_argument("--url", default="https://leowiki-mcp.stream/health", help="HTTP URL")
    parser.add_argument("--use-fastmcp", action="store_true", help="Use FastMCP client for STDIO")
    
    args = parser.parse_args()
    
    print(f"\n{'#'*60}")
    print(f"# MCP TRANSPORT COMPARISON")
    print(f"# {datetime.now().isoformat()}")
    print(f"{'#'*60}")
    
    results = []
    
    # Test HTTP
    if not args.stdio_only:
        http_result = test_http_latency(args.url, args.iterations)
        results.append(http_result)
    
    # Test STDIO
    if not args.http_only:
        if args.use_fastmcp:
            stdio_result = test_stdio_with_fastmcp(args.iterations)
        else:
            stdio_result = test_stdio_latency(args.iterations)
        results.append(stdio_result)
    
    # Print comparison
    print_comparison(results)
    
    # Save results
    output_dir = Path(__file__).parent.parent.parent / "data" / "benchmark"
    output_dir.mkdir(parents=True, exist_ok=True)
    save_results(results, output_dir)


if __name__ == "__main__":
    main()
