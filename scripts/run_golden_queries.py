#!/usr/bin/env python3
"""
Golden Query Test Runner for LeoWiki MCP Server

Runs the 8 golden queries directly against Qdrant via HTTP
and prints raw results with scores, titles, and keyword matches.

Usage:
    # Against production server (needs OPENAI_API_KEY for query embeddings):
    export OPENAI_API_KEY=sk-...
    python scripts/run_golden_queries.py

    # Against local Qdrant (Docker):
    python scripts/run_golden_queries.py --qdrant http://localhost:6333

Output: Markdown table you can paste into the testing protocol.
"""

import json
import sys
import os
import time
import argparse

# Add the project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

GOLDEN_QUERIES = [
    {
        "id": "GQ01",
        "name": "DA Format (Word?)",
        "text": "Darf ich meine Diplomarbeit mit MS Word schreiben?",
        "gold_contains": ["Diplomarbeit", "Format", "Word"],
    },
    {
        "id": "GQ02",
        "name": "Matura Klausurtag",
        "text": "Wann ist Einlass am Klausurtag der Matura?",
        "gold_contains": ["Matura", "Klausur", "Einlass"],
    },
    {
        "id": "GQ03",
        "name": "Office365 Mail",
        "text": "Ab wann gibt es die neuen Office365 Mail Accounts?",
        "gold_contains": ["Office365", "Mail", "Account"],
    },
    {
        "id": "GQ04",
        "name": "Exkursion organisieren",
        "text": "Was ist zu beachten, wenn ich eine Exkursion organisiere?",
        "gold_contains": ["Exkursion", "organisieren", "Leitfaden", "Genehmigung"],
    },
    {
        "id": "GQ05",
        "name": "Exkursion Antrag",
        "text": "Wo finde ich das Antragsformular für Exkursionen?",
        "gold_contains": ["Exkursion", "Antrag", "Formular", "Download"],
    },
    {
        "id": "GQ06",
        "name": "DA kein Thema",
        "text": "Was ist wenn ich kein Thema für eine Diplomarbeit finde?",
        "gold_contains": ["Diplomarbeit", "Thema", "Betreuung", "Koordinator"],
    },
    {
        "id": "GQ07",
        "name": "Company Thesis Day",
        "text": "Was ist der Company Thesis Day?",
        "gold_contains": ["Company Thesis Day", "Diplomarbeit", "Firmen"],
    },
    {
        "id": "GQ08",
        "name": "Dresscode Präsentation",
        "text": "Wie lautet der Dresscode für Diplomarbeitspräsentationen?",
        "gold_contains": ["Diplomarbeit", "Präsentation", "Dresscode", "Kleidung"],
    },
]


def check_keywords(text: str, keywords: list[str]) -> tuple[list[str], list[str]]:
    """Check which gold keywords appear in the result text."""
    text_lower = text.lower()
    hit = [k for k in keywords if k.lower() in text_lower]
    miss = [k for k in keywords if k.lower() not in text_lower]
    return hit, miss


def run_via_qdrant_direct(server_url: str):
    """
    Run golden queries by calling the Qdrant backend directly
    (bypasses MCP protocol, gives raw scores).
    Requires: openai, qdrant-client packages + OPENAI_API_KEY env var.
    """
    try:
        from openai import OpenAI
        from qdrant_client import QdrantClient
    except ImportError:
        print("ERROR: Need 'openai' and 'qdrant-client' packages.")
        print("  pip install openai qdrant-client")
        sys.exit(1)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: Set OPENAI_API_KEY environment variable.")
        sys.exit(1)

    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    collection = os.getenv("COLLECTION", "educational_content")

    print(f"Qdrant URL:  {qdrant_url}")
    print(f"Collection:  {collection}")
    print(f"Embedding:   text-embedding-3-large (3072D)")
    print(f"Date:        {time.strftime('%Y-%m-%d %H:%M')}")
    print()

    openai_client = OpenAI(api_key=api_key)
    qdrant = QdrantClient(url=qdrant_url)

    # Verify connection
    try:
        info = qdrant.get_collection(collection)
        print(f"Collection points: {info.points_count}")
    except Exception as e:
        print(f"ERROR connecting to Qdrant: {e}")
        sys.exit(1)

    print()
    print("=" * 100)
    print("GOLDEN QUERY RESULTS")
    print("=" * 100)

    results_table = []

    for gq in GOLDEN_QUERIES:
        print(f"\n--- {gq['id']}: {gq['name']} ---")
        print(f"Query: {gq['text']}")

        # Generate embedding
        resp = openai_client.embeddings.create(
            model="text-embedding-3-large",
            input=gq["text"],
            dimensions=3072,
        )
        query_vector = resp.data[0].embedding

        # Search Qdrant (qdrant-client >= 1.7 uses query_points)
        from qdrant_client.models import PointStruct
        try:
            # New API (qdrant-client >= 1.7)
            search_result = qdrant.query_points(
                collection_name=collection,
                query=query_vector,
                limit=5,
            )
            results = search_result.points
        except AttributeError:
            # Old API fallback
            results = qdrant.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=5,
            )

        if not results:
            print("  NO RESULTS")
            results_table.append({
                "id": gq["id"],
                "name": gq["name"],
                "top_title": "(no results)",
                "top_score": 0,
                "keywords_hit": [],
                "keywords_miss": gq["gold_contains"],
            })
            continue

        top = results[0]
        # Handle both old and new Qdrant API response formats
        payload = getattr(top, 'payload', {}) or {}
        title = payload.get("title", "") or payload.get("Title", "Untitled")
        score = getattr(top, 'score', 0)
        source = payload.get("source", "") or payload.get("Source", "")
        text_preview = (payload.get("text", "") or payload.get("Text", ""))[:200]

        # Check all results for keyword matches (not just top)
        def get_payload(r):
            p = getattr(r, 'payload', {}) or {}
            return p
        
        all_text = " ".join(
            get_payload(r).get("title", "") + " " + get_payload(r).get("Title", "") + " " +
            get_payload(r).get("text", "") + " " + get_payload(r).get("Text", "")
            for r in results[:3]
        )
        hit, miss = check_keywords(all_text, gq["gold_contains"])

        print(f"  Top result: {title}")
        print(f"  Score:      {score:.4f}")
        print(f"  Source:     {source}")
        print(f"  Preview:    {text_preview[:100]}...")
        print(f"  Keywords:   HIT={hit}  MISS={miss}")

        # Show top 3
        for i, r in enumerate(results[:3]):
            p = get_payload(r)
            t = p.get("title", "") or p.get("Title", "?")
            s = getattr(r, 'score', 0)
            print(f"  #{i+1}: [{s:.4f}] {t[:50]}")

        results_table.append({
            "id": gq["id"],
            "name": gq["name"],
            "top_title": title,
            "top_score": score,
            "keywords_hit": hit,
            "keywords_miss": miss,
            "top3": [(get_payload(r).get("title", "") or get_payload(r).get("Title", "?"), getattr(r, 'score', 0)) for r in results[:3]],
        })

    # Print summary table (markdown)
    print()
    print()
    print("=" * 100)
    print("SUMMARY TABLE (paste into testing protocol)")
    print("=" * 100)
    print()
    print("| GQ ID | Name | Top Result | Score | Keywords Hit | Keywords Miss | Rel |")
    print("|-------|------|------------|-------|--------------|---------------|-----|")
    for r in results_table:
        hit_str = ", ".join(r["keywords_hit"]) if r["keywords_hit"] else "-"
        miss_str = ", ".join(r["keywords_miss"]) if r["keywords_miss"] else "-"
        hit_ratio = len(r["keywords_hit"])
        total_kw = hit_ratio + len(r["keywords_miss"])
        # Auto-suggest relevance based on keyword hit ratio
        if total_kw > 0:
            ratio = hit_ratio / total_kw
            if ratio >= 0.8:
                rel = 5
            elif ratio >= 0.6:
                rel = 4
            elif ratio >= 0.4:
                rel = 3
            elif ratio >= 0.2:
                rel = 2
            else:
                rel = 1
        else:
            rel = 1
        print(f"| {r['id']} | {r['name'][:20]} | {r['top_title'][:30]} | {r['top_score']:.3f} | {hit_str} | {miss_str} | {rel} |")

    # Also dump raw JSON for later use
    output_dir = os.path.join(PROJECT_ROOT, "data", "statistics")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "golden_query_results.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results_table, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nRaw results saved to: {output_file}")


def run_via_health_check(server_url: str):
    """Quick health check to verify server is reachable."""
    try:
        import httpx
    except ImportError:
        import urllib.request
        req = urllib.request.Request(f"{server_url}/health")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            print(f"Server: {data.get('server')} v{data.get('version')}")
            print(f"Auth:   {data.get('authentication')}")
            print(f"RBAC:   {data.get('rbac')}")
            return
    
    with httpx.Client(timeout=10) as client:
        resp = client.get(f"{server_url}/health")
        data = resp.json()
        print(f"Server: {data.get('server')} v{data.get('version')}")
        print(f"Auth:   {data.get('authentication')}")
        print(f"RBAC:   {data.get('rbac')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run golden queries against LeoWiki MCP server")
    parser.add_argument("--url", default="https://leowiki-mcp.stream",
                        help="Server base URL (default: production)")
    parser.add_argument("--qdrant", default=None,
                        help="Qdrant URL override (default: from QDRANT_URL env or localhost:6333)")
    parser.add_argument("--health-only", action="store_true",
                        help="Only check server health")
    args = parser.parse_args()

    if args.qdrant:
        os.environ["QDRANT_URL"] = args.qdrant

    print(f"Server URL: {args.url}")
    print()

    # Health check first
    print("--- Health Check ---")
    try:
        run_via_health_check(args.url)
    except Exception as e:
        print(f"Health check failed: {e}")
    print()

    if args.health_only:
        sys.exit(0)

    # Run golden queries
    run_via_qdrant_direct(args.url)
