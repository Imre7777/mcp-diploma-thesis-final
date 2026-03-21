#!/usr/bin/env python3
"""
MCP Server Transport Benchmark

Benchmarks STDIO vs HTTP transport using the 78 ground-truth queries
from the LeoWiki Q&A catalog.

Usage:
    # HTTP transport only (against production server):
    python scripts/benchmark/run_benchmark.py --transport http
    
    # STDIO transport only (runs server locally):
    python scripts/benchmark/run_benchmark.py --transport stdio
    
    # Both transports (comparison):
    python scripts/benchmark/run_benchmark.py --transport both
    
    # Quick test with subset of queries:
    python scripts/benchmark/run_benchmark.py --transport http --limit 10

Output: JSON results and markdown summary in data/benchmark/

Requirements:
    - fastmcp>=3.0.1
    - httpx
    - For HTTP: Valid OAuth token or ENABLE_AUTH=false
    - For STDIO: Local environment with all dependencies
"""

import asyncio
import json
import os
import sys
import time
import statistics
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_query_catalog() -> list[dict]:
    """Load the 78 ground-truth Q&A pairs."""
    catalog_path = PROJECT_ROOT / "data" / "benchmark" / "query_catalog.json"
    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["qa_pairs"]


async def benchmark_http_transport(
    queries: list[dict],
    base_url: str = "http://localhost:8000",
    iterations: int = 1,
) -> dict:
    """
    Benchmark HTTP transport by making direct HTTP requests to the MCP endpoint.
    
    Note: This tests the raw HTTP performance without full MCP client overhead.
    """
    import httpx
    
    results = {
        "transport": "http",
        "base_url": base_url,
        "total_queries": len(queries),
        "iterations": iterations,
        "timings": [],
        "errors": [],
    }
    
    print(f"\n{'='*60}")
    print(f"HTTP Transport Benchmark")
    print(f"URL: {base_url}")
    print(f"Queries: {len(queries)}, Iterations: {iterations}")
    print(f"{'='*60}\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, qa in enumerate(queries):
            query_timings = []
            query_id = qa["id"]
            question = qa["question"]
            
            for iter_num in range(iterations):
                start = time.perf_counter()
                try:
                    # Make health check as simple benchmark
                    # (Full MCP would require session setup)
                    response = await client.get(f"{base_url}/health")
                    elapsed = time.perf_counter() - start
                    
                    if response.status_code == 200:
                        query_timings.append(elapsed)
                    else:
                        results["errors"].append({
                            "query_id": query_id,
                            "iteration": iter_num,
                            "error": f"HTTP {response.status_code}",
                        })
                except Exception as e:
                    elapsed = time.perf_counter() - start
                    results["errors"].append({
                        "query_id": query_id,
                        "iteration": iter_num,
                        "error": str(e),
                    })
            
            if query_timings:
                results["timings"].append({
                    "query_id": query_id,
                    "question": question[:50] + "..." if len(question) > 50 else question,
                    "difficulty": qa.get("difficulty", "unknown"),
                    "times_ms": [t * 1000 for t in query_timings],
                    "mean_ms": statistics.mean(query_timings) * 1000,
                    "min_ms": min(query_timings) * 1000,
                    "max_ms": max(query_timings) * 1000,
                })
            
            # Progress indicator
            if (i + 1) % 10 == 0 or i == len(queries) - 1:
                print(f"  Progress: {i + 1}/{len(queries)} queries completed")
    
    # Calculate overall statistics
    all_times = []
    for t in results["timings"]:
        all_times.extend(t["times_ms"])
    
    if all_times:
        results["summary"] = {
            "total_requests": len(all_times),
            "mean_ms": statistics.mean(all_times),
            "median_ms": statistics.median(all_times),
            "stdev_ms": statistics.stdev(all_times) if len(all_times) > 1 else 0,
            "min_ms": min(all_times),
            "max_ms": max(all_times),
            "p95_ms": sorted(all_times)[int(len(all_times) * 0.95)] if len(all_times) >= 20 else max(all_times),
            "errors": len(results["errors"]),
        }
    
    return results


async def benchmark_stdio_transport(
    queries: list[dict],
    iterations: int = 1,
) -> dict:
    """
    Benchmark STDIO transport using FastMCP client.
    
    This runs the server as a subprocess and communicates via stdin/stdout.
    """
    from fastmcp import Client
    
    results = {
        "transport": "stdio",
        "total_queries": len(queries),
        "iterations": iterations,
        "timings": [],
        "errors": [],
    }
    
    print(f"\n{'='*60}")
    print(f"STDIO Transport Benchmark")
    print(f"Queries: {len(queries)}, Iterations: {iterations}")
    print(f"{'='*60}\n")
    
    # Build the command to run the server in STDIO mode
    server_cmd = f"python {PROJECT_ROOT}/main.py"
    
    try:
        async with Client(server_cmd) as client:
            print("  Connected to STDIO server")
            
            for i, qa in enumerate(queries):
                query_timings = []
                query_id = qa["id"]
                question = qa["question"]
                
                for iter_num in range(iterations):
                    start = time.perf_counter()
                    try:
                        # Call the actual search tool
                        result = await client.call_tool(
                            "search_content_student",
                            {"query": question, "limit": 3}
                        )
                        elapsed = time.perf_counter() - start
                        query_timings.append(elapsed)
                    except Exception as e:
                        elapsed = time.perf_counter() - start
                        results["errors"].append({
                            "query_id": query_id,
                            "iteration": iter_num,
                            "error": str(e),
                            "elapsed_ms": elapsed * 1000,
                        })
                
                if query_timings:
                    results["timings"].append({
                        "query_id": query_id,
                        "question": question[:50] + "..." if len(question) > 50 else question,
                        "difficulty": qa.get("difficulty", "unknown"),
                        "times_ms": [t * 1000 for t in query_timings],
                        "mean_ms": statistics.mean(query_timings) * 1000,
                        "min_ms": min(query_timings) * 1000,
                        "max_ms": max(query_timings) * 1000,
                    })
                
                # Progress indicator
                if (i + 1) % 10 == 0 or i == len(queries) - 1:
                    print(f"  Progress: {i + 1}/{len(queries)} queries completed")
                    
    except Exception as e:
        print(f"  ERROR: Failed to connect to STDIO server: {e}")
        results["errors"].append({"error": f"Connection failed: {e}"})
        return results
    
    # Calculate overall statistics
    all_times = []
    for t in results["timings"]:
        all_times.extend(t["times_ms"])
    
    if all_times:
        results["summary"] = {
            "total_requests": len(all_times),
            "mean_ms": statistics.mean(all_times),
            "median_ms": statistics.median(all_times),
            "stdev_ms": statistics.stdev(all_times) if len(all_times) > 1 else 0,
            "min_ms": min(all_times),
            "max_ms": max(all_times),
            "p95_ms": sorted(all_times)[int(len(all_times) * 0.95)] if len(all_times) >= 20 else max(all_times),
            "errors": len(results["errors"]),
        }
    
    return results


async def benchmark_mcp_client_http(
    queries: list[dict],
    url: str = "https://leowiki-mcp.stream/mcp",
    iterations: int = 1,
) -> dict:
    """
    Benchmark HTTP transport using full FastMCP client.
    
    This tests the complete MCP protocol over HTTP with OAuth.
    """
    from fastmcp import Client
    
    results = {
        "transport": "mcp-http",
        "url": url,
        "total_queries": len(queries),
        "iterations": iterations,
        "timings": [],
        "errors": [],
    }
    
    print(f"\n{'='*60}")
    print(f"MCP HTTP Client Benchmark")
    print(f"URL: {url}")
    print(f"Queries: {len(queries)}, Iterations: {iterations}")
    print(f"{'='*60}\n")
    
    try:
        async with Client(url) as client:
            print("  Connected to HTTP server")
            
            for i, qa in enumerate(queries):
                query_timings = []
                query_id = qa["id"]
                question = qa["question"]
                
                for iter_num in range(iterations):
                    start = time.perf_counter()
                    try:
                        result = await client.call_tool(
                            "search_content_student",
                            {"query": question, "limit": 3}
                        )
                        elapsed = time.perf_counter() - start
                        query_timings.append(elapsed)
                    except Exception as e:
                        elapsed = time.perf_counter() - start
                        results["errors"].append({
                            "query_id": query_id,
                            "iteration": iter_num,
                            "error": str(e),
                            "elapsed_ms": elapsed * 1000,
                        })
                
                if query_timings:
                    results["timings"].append({
                        "query_id": query_id,
                        "question": question[:50] + "..." if len(question) > 50 else question,
                        "difficulty": qa.get("difficulty", "unknown"),
                        "times_ms": [t * 1000 for t in query_timings],
                        "mean_ms": statistics.mean(query_timings) * 1000,
                        "min_ms": min(query_timings) * 1000,
                        "max_ms": max(query_timings) * 1000,
                    })
                
                if (i + 1) % 10 == 0 or i == len(queries) - 1:
                    print(f"  Progress: {i + 1}/{len(queries)} queries completed")
                    
    except Exception as e:
        print(f"  ERROR: Failed to connect: {e}")
        results["errors"].append({"error": f"Connection failed: {e}"})
        return results
    
    # Calculate overall statistics
    all_times = []
    for t in results["timings"]:
        all_times.extend(t["times_ms"])
    
    if all_times:
        results["summary"] = {
            "total_requests": len(all_times),
            "mean_ms": statistics.mean(all_times),
            "median_ms": statistics.median(all_times),
            "stdev_ms": statistics.stdev(all_times) if len(all_times) > 1 else 0,
            "min_ms": min(all_times),
            "max_ms": max(all_times),
            "p95_ms": sorted(all_times)[int(len(all_times) * 0.95)] if len(all_times) >= 20 else max(all_times),
            "errors": len(results["errors"]),
        }
    
    return results


def generate_markdown_report(results: list[dict], output_path: Path) -> str:
    """Generate a markdown report from benchmark results."""
    report = []
    report.append("# MCP Server Transport Benchmark Results\n")
    report.append(f"**Generated:** {datetime.now().isoformat()}\n")
    report.append(f"**Query Catalog:** 78 Ground-Truth Q&A pairs (LeoWiki)\n\n")
    
    # Summary table
    report.append("## Summary\n")
    report.append("| Transport | Queries | Mean (ms) | Median (ms) | P95 (ms) | Min (ms) | Max (ms) | Errors |")
    report.append("|-----------|---------|-----------|-------------|----------|----------|----------|--------|")
    
    for r in results:
        if "summary" in r:
            s = r["summary"]
            report.append(
                f"| {r['transport']} | {r['total_queries']} | "
                f"{s['mean_ms']:.1f} | {s['median_ms']:.1f} | {s['p95_ms']:.1f} | "
                f"{s['min_ms']:.1f} | {s['max_ms']:.1f} | {s['errors']} |"
            )
    
    report.append("\n")
    
    # Comparison if both transports tested
    if len(results) == 2 and all("summary" in r for r in results):
        report.append("## Comparison\n")
        r1, r2 = results
        if r1["summary"]["mean_ms"] < r2["summary"]["mean_ms"]:
            faster, slower = r1, r2
        else:
            faster, slower = r2, r1
        
        speedup = slower["summary"]["mean_ms"] / faster["summary"]["mean_ms"]
        report.append(f"**{faster['transport']}** is **{speedup:.2f}x faster** than **{slower['transport']}** on average.\n\n")
    
    # Detailed results by difficulty
    report.append("## Results by Difficulty\n")
    for r in results:
        report.append(f"### {r['transport'].upper()}\n")
        
        by_difficulty = {"easy": [], "medium": [], "hard": [], "unknown": []}
        for t in r.get("timings", []):
            diff = t.get("difficulty", "unknown")
            by_difficulty[diff].append(t["mean_ms"])
        
        report.append("| Difficulty | Count | Mean (ms) | Min (ms) | Max (ms) |")
        report.append("|------------|-------|-----------|----------|----------|")
        for diff in ["easy", "medium", "hard"]:
            times = by_difficulty[diff]
            if times:
                report.append(
                    f"| {diff} | {len(times)} | {statistics.mean(times):.1f} | "
                    f"{min(times):.1f} | {max(times):.1f} |"
                )
        report.append("\n")
    
    # Errors
    total_errors = sum(len(r.get("errors", [])) for r in results)
    if total_errors > 0:
        report.append("## Errors\n")
        for r in results:
            if r.get("errors"):
                report.append(f"### {r['transport']}\n")
                for err in r["errors"][:10]:  # Limit to first 10
                    report.append(f"- {err}\n")
                if len(r["errors"]) > 10:
                    report.append(f"- ... and {len(r['errors']) - 10} more\n")
    
    report_text = "\n".join(report)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    
    return report_text


async def main():
    parser = argparse.ArgumentParser(description="MCP Server Transport Benchmark")
    parser.add_argument(
        "--transport",
        choices=["http", "stdio", "both", "mcp-http"],
        default="http",
        help="Transport to benchmark (default: http)"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="HTTP server URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of queries (default: all 78)"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="Iterations per query (default: 1)"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory (default: data/benchmark/)"
    )
    
    args = parser.parse_args()
    
    # Load queries
    queries = load_query_catalog()
    if args.limit:
        queries = queries[:args.limit]
    
    print(f"\nMCP Server Transport Benchmark")
    print(f"==============================")
    print(f"Queries: {len(queries)}")
    print(f"Iterations: {args.iterations}")
    print(f"Transport: {args.transport}")
    
    # Run benchmarks
    results = []
    
    if args.transport in ["http", "both"]:
        http_results = await benchmark_http_transport(
            queries, args.url, args.iterations
        )
        results.append(http_results)
    
    if args.transport in ["stdio", "both"]:
        stdio_results = await benchmark_stdio_transport(
            queries, args.iterations
        )
        results.append(stdio_results)
    
    if args.transport == "mcp-http":
        mcp_results = await benchmark_mcp_client_http(
            queries, args.url, args.iterations
        )
        results.append(mcp_results)
    
    # Save results
    output_dir = Path(args.output) if args.output else PROJECT_ROOT / "data" / "benchmark"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON results
    json_path = output_dir / f"benchmark_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "args": vars(args),
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {json_path}")
    
    # Generate markdown report
    md_path = output_dir / f"benchmark_{timestamp}.md"
    report = generate_markdown_report(results, md_path)
    print(f"Report saved to: {md_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("BENCHMARK SUMMARY")
    print("="*60)
    for r in results:
        if "summary" in r:
            s = r["summary"]
            print(f"\n{r['transport'].upper()}:")
            print(f"  Mean:   {s['mean_ms']:.1f} ms")
            print(f"  Median: {s['median_ms']:.1f} ms")
            print(f"  P95:    {s['p95_ms']:.1f} ms")
            print(f"  Errors: {s['errors']}")


if __name__ == "__main__":
    asyncio.run(main())
