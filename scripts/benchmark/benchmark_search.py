#!/usr/bin/env python3
"""
Direct Search Benchmark

Tests semantic search performance directly against Qdrant,
measuring embedding generation + vector search time.

This is the "pure" search performance without MCP protocol overhead.

Usage:
    # Run with all 78 queries:
    python scripts/benchmark/benchmark_search.py
    
    # Quick test with 10 queries:
    python scripts/benchmark/benchmark_search.py --limit 10
    
    # Multiple iterations for more accurate stats:
    python scripts/benchmark/benchmark_search.py --iterations 3

Requirements:
    - OPENAI_API_KEY environment variable
    - Running Qdrant instance (docker)
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

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.embeddings import EmbeddingService
from src.backends.qdrant import QdrantBackend
from src.config.server_config import ServerConfig


def load_query_catalog() -> list[dict]:
    """Load the 78 ground-truth Q&A pairs."""
    catalog_path = PROJECT_ROOT / "data" / "benchmark" / "query_catalog.json"
    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["qa_pairs"]


def run_benchmark(
    queries: list[dict],
    config: ServerConfig,
    iterations: int = 1,
    limit_results: int = 5,
) -> dict:
    """
    Benchmark semantic search performance.
    
    Measures:
    - Embedding generation time
    - Vector search time
    - Total query time
    """
    # Initialize services
    print("Initializing services...")
    embedding_service = EmbeddingService(
        api_key=config.openai_api_key,
        model=config.embedding_model,
    )
    
    db = QdrantBackend(
        url=config.vector_db_url,
        api_key=config.vector_db_api_key,
    )
    
    print(f"  Embedding model: {config.embedding_model}")
    print(f"  Qdrant URL: {config.vector_db_url}")
    print(f"  Collection: {config.default_collection}")
    
    results = {
        "config": {
            "embedding_model": config.embedding_model,
            "qdrant_url": config.vector_db_url,
            "collection": config.default_collection,
            "result_limit": limit_results,
        },
        "total_queries": len(queries),
        "iterations": iterations,
        "timings": [],
        "errors": [],
    }
    
    print(f"\nRunning benchmark: {len(queries)} queries x {iterations} iterations")
    print("="*60)
    
    for i, qa in enumerate(queries):
        query_id = qa["id"]
        question = qa["question"]
        difficulty = qa.get("difficulty", "unknown")
        
        embedding_times = []
        search_times = []
        total_times = []
        
        for iter_num in range(iterations):
            try:
                # Measure embedding generation
                embed_start = time.perf_counter()
                query_vector = embedding_service.embed_query(question)
                embed_time = time.perf_counter() - embed_start
                
                # Measure vector search
                search_start = time.perf_counter()
                search_results = db.search(
                    query_vector=query_vector,
                    collection=config.default_collection,
                    limit=limit_results,
                    filters=None,
                )
                search_time = time.perf_counter() - search_start
                
                total_time = embed_time + search_time
                
                embedding_times.append(embed_time * 1000)  # Convert to ms
                search_times.append(search_time * 1000)
                total_times.append(total_time * 1000)
                
            except Exception as e:
                results["errors"].append({
                    "query_id": query_id,
                    "iteration": iter_num,
                    "error": str(e),
                })
        
        if total_times:
            results["timings"].append({
                "query_id": query_id,
                "question": question[:60] + "..." if len(question) > 60 else question,
                "difficulty": difficulty,
                "embedding_ms": {
                    "mean": statistics.mean(embedding_times),
                    "min": min(embedding_times),
                    "max": max(embedding_times),
                },
                "search_ms": {
                    "mean": statistics.mean(search_times),
                    "min": min(search_times),
                    "max": max(search_times),
                },
                "total_ms": {
                    "mean": statistics.mean(total_times),
                    "min": min(total_times),
                    "max": max(total_times),
                },
            })
        
        # Progress
        if (i + 1) % 10 == 0 or i == len(queries) - 1:
            last = results["timings"][-1] if results["timings"] else None
            if last:
                print(f"  [{i+1:3d}/{len(queries)}] {query_id}: embed={last['embedding_ms']['mean']:.0f}ms, search={last['search_ms']['mean']:.0f}ms, total={last['total_ms']['mean']:.0f}ms")
    
    # Calculate overall statistics
    all_embed = [t["embedding_ms"]["mean"] for t in results["timings"]]
    all_search = [t["search_ms"]["mean"] for t in results["timings"]]
    all_total = [t["total_ms"]["mean"] for t in results["timings"]]
    
    if all_total:
        results["summary"] = {
            "embedding_ms": {
                "mean": statistics.mean(all_embed),
                "median": statistics.median(all_embed),
                "stdev": statistics.stdev(all_embed) if len(all_embed) > 1 else 0,
                "min": min(all_embed),
                "max": max(all_embed),
            },
            "search_ms": {
                "mean": statistics.mean(all_search),
                "median": statistics.median(all_search),
                "stdev": statistics.stdev(all_search) if len(all_search) > 1 else 0,
                "min": min(all_search),
                "max": max(all_search),
            },
            "total_ms": {
                "mean": statistics.mean(all_total),
                "median": statistics.median(all_total),
                "stdev": statistics.stdev(all_total) if len(all_total) > 1 else 0,
                "min": min(all_total),
                "max": max(all_total),
                "p95": sorted(all_total)[int(len(all_total) * 0.95)] if len(all_total) >= 20 else max(all_total),
            },
            "by_difficulty": {},
            "errors": len(results["errors"]),
        }
        
        # Stats by difficulty
        for diff in ["easy", "medium", "hard"]:
            diff_times = [t["total_ms"]["mean"] for t in results["timings"] if t["difficulty"] == diff]
            if diff_times:
                results["summary"]["by_difficulty"][diff] = {
                    "count": len(diff_times),
                    "mean_ms": statistics.mean(diff_times),
                    "median_ms": statistics.median(diff_times),
                }
    
    return results


def generate_report(results: dict, output_path: Path) -> str:
    """Generate markdown report."""
    report = []
    report.append("# Direct Search Benchmark Results\n")
    report.append(f"**Generated:** {datetime.now().isoformat()}\n")
    report.append(f"**Embedding Model:** {results['config']['embedding_model']}\n")
    report.append(f"**Qdrant:** {results['config']['qdrant_url']}\n")
    report.append(f"**Collection:** {results['config']['collection']}\n")
    report.append(f"**Queries:** {results['total_queries']}\n")
    report.append(f"**Iterations:** {results['iterations']}\n\n")
    
    if "summary" in results:
        s = results["summary"]
        
        report.append("## Summary\n")
        report.append("| Metric | Mean (ms) | Median (ms) | P95 (ms) | Min (ms) | Max (ms) |")
        report.append("|--------|-----------|-------------|----------|----------|----------|")
        report.append(f"| Embedding | {s['embedding_ms']['mean']:.1f} | {s['embedding_ms']['median']:.1f} | - | {s['embedding_ms']['min']:.1f} | {s['embedding_ms']['max']:.1f} |")
        report.append(f"| Search | {s['search_ms']['mean']:.1f} | {s['search_ms']['median']:.1f} | - | {s['search_ms']['min']:.1f} | {s['search_ms']['max']:.1f} |")
        report.append(f"| **Total** | **{s['total_ms']['mean']:.1f}** | **{s['total_ms']['median']:.1f}** | **{s['total_ms']['p95']:.1f}** | {s['total_ms']['min']:.1f} | {s['total_ms']['max']:.1f} |")
        report.append("\n")
        
        report.append("## By Difficulty\n")
        report.append("| Difficulty | Count | Mean (ms) | Median (ms) |")
        report.append("|------------|-------|-----------|-------------|")
        for diff in ["easy", "medium", "hard"]:
            if diff in s["by_difficulty"]:
                d = s["by_difficulty"][diff]
                report.append(f"| {diff} | {d['count']} | {d['mean_ms']:.1f} | {d['median_ms']:.1f} |")
        report.append("\n")
        
        report.append("## Time Breakdown\n")
        embed_pct = s['embedding_ms']['mean'] / s['total_ms']['mean'] * 100
        search_pct = s['search_ms']['mean'] / s['total_ms']['mean'] * 100
        report.append(f"- **Embedding generation:** {s['embedding_ms']['mean']:.1f} ms ({embed_pct:.0f}%)\n")
        report.append(f"- **Vector search:** {s['search_ms']['mean']:.1f} ms ({search_pct:.0f}%)\n")
        report.append(f"- **Total:** {s['total_ms']['mean']:.1f} ms\n\n")
        
        if s["errors"] > 0:
            report.append(f"**Errors:** {s['errors']}\n")
    
    report_text = "\n".join(report)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    
    return report_text


def main():
    parser = argparse.ArgumentParser(description="Direct Search Benchmark")
    parser.add_argument("--limit", type=int, default=None, help="Limit queries")
    parser.add_argument("--iterations", type=int, default=1, help="Iterations per query")
    parser.add_argument("--results", type=int, default=5, help="Search results limit")
    parser.add_argument("--qdrant", default=None, help="Qdrant URL override")
    
    args = parser.parse_args()
    
    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable required")
        sys.exit(1)
    
    # Load config
    config = ServerConfig()
    if args.qdrant:
        config.vector_db_url = args.qdrant
    
    # Load queries
    queries = load_query_catalog()
    if args.limit:
        queries = queries[:args.limit]
    
    print(f"\nDirect Search Benchmark")
    print(f"=======================")
    print(f"Queries: {len(queries)}")
    print(f"Iterations: {args.iterations}")
    
    # Run benchmark
    results = run_benchmark(queries, config, args.iterations, args.results)
    
    # Save results
    output_dir = PROJECT_ROOT / "data" / "benchmark"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON
    json_path = output_dir / f"search_benchmark_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults: {json_path}")
    
    # Markdown
    md_path = output_dir / f"search_benchmark_{timestamp}.md"
    report = generate_report(results, md_path)
    print(f"Report: {md_path}")
    
    # Print summary
    if "summary" in results:
        s = results["summary"]
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"  Embedding: {s['embedding_ms']['mean']:.1f} ms (mean)")
        print(f"  Search:    {s['search_ms']['mean']:.1f} ms (mean)")
        print(f"  Total:     {s['total_ms']['mean']:.1f} ms (mean)")
        print(f"  P95:       {s['total_ms']['p95']:.1f} ms")
        print(f"  Errors:    {s['errors']}")


if __name__ == "__main__":
    main()
