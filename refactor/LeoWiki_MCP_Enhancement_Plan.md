# LeoWiki MCP Server - Professional Enhancement Plan

**Project:** HTL Leonding Educational MCP Server (Diploma Thesis)  
**Current Version:** 1.0.0  
**Target Version:** 2.0.0  
**Author:** Imre  
**Date:** January 2026  

---

## Executive Summary

This document outlines a comprehensive plan to transform the existing LeoWiki MCP server from a functional prototype into a production-grade, professional educational platform. The enhancements leverage FastMCP v2.x capabilities that are currently unused, improving user experience, security, maintainability, and showcasing advanced MCP patterns suitable for a diploma thesis.

**Estimated Total Effort:** 20-30 hours  
**Recommended Timeline:** 2-3 weeks

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Target Architecture](#2-target-architecture)
3. [Implementation Phases](#3-implementation-phases)
4. [Phase 1: Core Enhancements](#4-phase-1-core-enhancements)
5. [Phase 2: Resources & Prompts](#5-phase-2-resources--prompts)
6. [Phase 3: Advanced Features](#6-phase-3-advanced-features)
7. [Phase 4: Testing & Documentation](#7-phase-4-testing--documentation)
8. [File Structure Changes](#8-file-structure-changes)
9. [Migration Guide](#9-migration-guide)
10. [Risk Assessment](#10-risk-assessment)

---

## 1. Current State Analysis

### 1.1 What's Working Well ✅

| Component | Status | Notes |
|-----------|--------|-------|
| FastMCP Integration | ✅ Good | Basic setup with stateless_http |
| OAuth 2.1 (Scalekit) | ✅ Excellent | Full implementation with middleware |
| Qdrant Vector DB | ✅ Good | Connection and search working |
| RBAC System | ✅ Good | Role-based filtering implemented |
| HTTP Streamable | ✅ Good | Proper transport configuration |
| Docker Deployment | ✅ Good | docker-compose with Caddy |
| Project Structure | ✅ Good | Modular src/ organization |

### 1.2 Gaps & Opportunities 🔄

| Feature | Current State | Impact |
|---------|---------------|--------|
| **Resources** | ❌ Not implemented | LLMs lack context about wiki structure |
| **Prompts** | ❌ Not implemented | No reusable educational workflows |
| **Context.report_progress** | ❌ Not used | Users don't see search progress |
| **Context.info/debug** | ❌ Not used | No client-side logging |
| **Tool Annotations** | ❌ Not used | Clients can't optimize behavior |
| **Middleware (custom)** | ❌ Not used | RBAC logic mixed in tools |
| **Server Composition** | ❌ Not used | Monolithic structure |
| **Error Masking** | ❌ Not enabled | Internal errors could leak |
| **Server Instructions** | ❌ Not set | LLMs don't know how to use server |
| **Tags** | ❌ Not used | No tool organization |
| **Testing (MCP Client)** | ❌ Not used | Only HTTP tests exist |

### 1.3 Current Tool Inventory

```
Tools (2):
├── search_content      - Semantic search with RBAC
└── health_check        - Server status

Resources (0): None

Prompts (0): None
```

---

## 2. Target Architecture

### 2.1 Enhanced Tool Inventory

```
Tools (8):
├── Search Module
│   ├── search_content          - Semantic search (enhanced)
│   ├── search_similar          - Find similar documents
│   └── search_by_category      - Category-filtered search
├── Content Module  
│   ├── get_document            - Retrieve full document
│   └── list_recent_updates     - Recently changed content
├── Admin Module (role-gated)
│   ├── get_collection_stats    - Database statistics
│   ├── reindex_document        - Trigger re-indexing
│   └── health_check            - Server health (enhanced)

Resources (6):
├── leowiki://categories        - Available content categories
├── leowiki://stats             - Collection statistics
├── leowiki://schema            - Content schema documentation
├── leowiki://topic/{id}        - Dynamic topic details
├── leowiki://search-hints      - Search tips for users
└── leowiki://access-levels     - RBAC level descriptions

Prompts (5):
├── explain_topic               - Educational explanation template
├── create_quiz                 - Quiz generation workflow
├── compare_concepts            - Side-by-side comparison
├── summarize_search            - Summarize search results
└── learning_path               - Generate learning roadmap
```

### 2.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                       │
├─────────────────────────────────────────────────────────────────┤
│  /.well-known/oauth-protected-resource  │  /health  │  /docs   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Main MCP Server                          │ │
│  │  FastMCP(name="LeoWiki MCP", lifespan=app_lifespan)        │ │
│  ├────────────────────────────────────────────────────────────┤ │
│  │                      Middleware Stack                       │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌────────────────────┐  │ │
│  │  │ RequestLog   │→│ UserContext  │→│ RBACEnforcement    │  │ │
│  │  └──────────────┘ └──────────────┘ └────────────────────┘  │ │
│  ├────────────────────────────────────────────────────────────┤ │
│  │                    Mounted Servers                          │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │ │
│  │  │ search_mcp   │ │ content_mcp  │ │ admin_mcp    │        │ │
│  │  │ (3 tools)    │ │ (2 tools)    │ │ (3 tools)    │        │ │
│  │  │ (2 resources)│ │ (2 resources)│ │ (2 resources)│        │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘        │ │
│  ├────────────────────────────────────────────────────────────┤ │
│  │                    Shared Prompts                           │ │
│  │  explain_topic │ create_quiz │ compare_concepts │ ...      │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
├──────────────────────────────┼───────────────────────────────────┤
│                    Lifespan Context                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Qdrant    │  │  Embedding  │  │   Config    │              │
│  │   Client    │  │   Service   │  │   Object    │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Implementation Phases

### Phase Overview

| Phase | Focus | Duration | Priority |
|-------|-------|----------|----------|
| **Phase 1** | Core Enhancements | 4-6 hours | 🔴 Critical |
| **Phase 2** | Resources & Prompts | 6-8 hours | 🟠 High |
| **Phase 3** | Advanced Features | 6-10 hours | 🟡 Medium |
| **Phase 4** | Testing & Docs | 4-6 hours | 🟢 Important |

### Dependency Graph

```
Phase 1 ──────┬──────> Phase 2 ──────> Phase 3
              │                            │
              └────────────────────────────┼──────> Phase 4
```

---

## 4. Phase 1: Core Enhancements

**Goal:** Establish professional foundation without breaking existing functionality.

### 4.1 Enhanced Server Initialization

**File:** `main.py`

```python
# BEFORE
mcp = FastMCP(
    name=config.server_name,
    stateless_http=True
)

# AFTER
mcp = FastMCP(
    name=config.server_name,
    
    # Instructions help LLMs understand how to use the server
    instructions="""
    LeoWiki MCP Server - HTL Leonding Educational Content
    
    This server provides access to HTL Leonding's internal wiki (LeoWiki).
    
    CAPABILITIES:
    - Semantic search across educational content
    - Access to course materials, tutorials, and documentation
    - Role-based content filtering (student/teacher/admin)
    
    USAGE TIPS:
    - Use search_content for finding information
    - Specify categories to narrow results
    - Check leowiki://categories resource for available topics
    
    LANGUAGE: Content is primarily in German.
    """,
    
    # Transport settings
    stateless_http=True,
    json_response=False,  # Keep SSE for progress reporting
    
    # Security (CRITICAL for production)
    mask_error_details=True,
    
    # Behavior
    on_duplicate_tools="error",
    
    # Organization
    tags={"educational", "htl-leonding", "leowiki"},
    
    # Dependency injection
    lifespan=app_lifespan,
)
```

### 4.2 Implement Lifespan for Dependency Injection

**File:** `src/server/lifespan.py` (NEW)

```python
from contextlib import asynccontextmanager
from dataclasses import dataclass
from collections.abc import AsyncIterator
from fastmcp import FastMCP
from qdrant_client import AsyncQdrantClient
import logging

from src.config.server_config import ServerConfig
from src.utils.embeddings import EmbeddingService

logger = logging.getLogger(__name__)

@dataclass
class AppContext:
    """Type-safe container for injected dependencies."""
    qdrant: AsyncQdrantClient
    embedding_service: EmbeddingService
    config: ServerConfig
    cache: dict  # Simple query cache

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Initialize and cleanup application resources."""
    config = ServerConfig()
    
    logger.info("=" * 60)
    logger.info("Initializing LeoWiki MCP Server...")
    logger.info("=" * 60)
    
    # Initialize Qdrant (async client for better performance)
    logger.info("Connecting to Qdrant...")
    qdrant = AsyncQdrantClient(
        url=config.vector_db_url,
        api_key=config.vector_db_api_key,
        timeout=30
    )
    
    # Initialize embedding service
    logger.info("Initializing embedding service...")
    embedding_service = EmbeddingService(
        api_key=config.openai_api_key,
        model=config.embedding_model
    )
    
    # Simple cache for repeated queries
    cache = {}
    
    logger.info("✓ All dependencies initialized successfully")
    logger.info("=" * 60)
    
    try:
        yield AppContext(
            qdrant=qdrant,
            embedding_service=embedding_service,
            config=config,
            cache=cache
        )
    finally:
        logger.info("Shutting down LeoWiki MCP Server...")
        await qdrant.close()
        logger.info("✓ Cleanup complete")
```

### 4.3 Enhanced Search Tool with Progress Reporting

**File:** `src/tools/search.py` (REFACTORED)

```python
from fastmcp import FastMCP, Context
from fastmcp.tools import ToolAnnotations
from fastmcp.exceptions import ToolError
from typing import Annotated
from pydantic import Field
import logging

from src.server.lifespan import AppContext

logger = logging.getLogger(__name__)

def create_search_server() -> FastMCP:
    """Create the search module MCP server."""
    
    search_mcp = FastMCP(
        name="SearchModule",
        tags={"search"}
    )
    
    @search_mcp.tool(
        name="search_content",
        description="Search educational content with semantic search and RBAC filtering",
        annotations=ToolAnnotations(
            title="LeoWiki Search",
            readOnlyHint=True,      # Safe to cache, no side effects
            idempotentHint=True,    # Same input = same output
            openWorldHint=False,    # Results are from known dataset
        ),
        tags={"search", "read-only", "student"}
    )
    async def search_content(
        query: Annotated[str, Field(
            description="Search query text (German or English)",
            min_length=1,
            max_length=500,
            examples=["Java Grundlagen", "Netzwerk Subnetting", "OOP Konzepte"]
        )],
        limit: Annotated[int, Field(
            description="Maximum number of results",
            ge=1,
            le=50,
            default=10
        )] = 10,
        categories: Annotated[list[str], Field(
            description="Filter by categories (e.g., ['sew', 'nwt'])",
            default=[],
            max_length=5
        )] = [],
        ctx: Context = None
    ) -> dict:
        """
        Search educational content using semantic similarity.
        
        Results are automatically filtered based on your access level:
        - Students see student-level content
        - Teachers see student + teacher content
        - Admins see all content
        """
        app: AppContext = ctx.lifespan_context
        user_role = ctx.get_state("user_role") or "student"
        
        try:
            # Step 1: Generate embedding
            await ctx.report_progress(0, 4, "Analyzing query...")
            await ctx.info(f"Searching for: {query[:50]}...")
            
            query_embedding = app.embedding_service.embed_query(query)
            
            # Step 2: Build filters
            await ctx.report_progress(1, 4, "Applying access filters...")
            
            filters = build_rbac_filter(user_role, app.config)
            if categories:
                filters = add_category_filter(filters, categories)
            
            # Step 3: Execute search
            await ctx.report_progress(2, 4, "Searching knowledge base...")
            
            results = await app.qdrant.search(
                collection_name=app.config.default_collection,
                query_vector=query_embedding,
                query_filter=filters,
                limit=limit,
                with_payload=True
            )
            
            # Step 4: Format results
            await ctx.report_progress(3, 4, "Formatting results...")
            
            formatted = format_search_results(results)
            
            await ctx.report_progress(4, 4, "Search complete!")
            await ctx.info(f"Found {len(formatted)} results")
            
            return {
                "query": query,
                "results": formatted,
                "total": len(formatted),
                "filters_applied": {
                    "access_level": user_role,
                    "categories": categories or "all"
                }
            }
            
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            await ctx.error(f"Search failed: {type(e).__name__}")
            raise ToolError("Search temporarily unavailable. Please try again.")
    
    return search_mcp
```

### 4.4 Custom Middleware Implementation

**File:** `src/middleware/mcp_middleware.py` (NEW)

```python
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.dependencies import get_http_headers
from fastmcp.exceptions import ToolError
import jwt
import time
import uuid
import logging

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(Middleware):
    """Log all MCP requests with timing and correlation IDs."""
    
    async def on_request(self, context: MiddlewareContext, call_next):
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        if context.fastmcp_context:
            context.fastmcp_context.set_state("request_id", request_id)
        
        logger.info(f"[{request_id}] → {context.method}")
        
        try:
            result = await call_next(context)
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"[{request_id}] ✓ {context.method} ({duration_ms:.1f}ms)")
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[{request_id}] ✗ {context.method} ({duration_ms:.1f}ms): {e}")
            raise


class UserContextMiddleware(Middleware):
    """Extract user info from JWT and populate session state."""
    
    async def on_request(self, context: MiddlewareContext, call_next):
        headers = get_http_headers() or {}
        auth_header = headers.get("authorization", "")
        
        user_id = None
        user_email = None
        user_role = "student"  # Default
        
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                # Token already validated by Scalekit middleware
                claims = jwt.decode(token, options={"verify_signature": False})
                user_id = claims.get("sub")
                user_email = claims.get("email")
                user_role = claims.get("role", "student")
            except Exception:
                pass  # Use defaults
        
        if context.fastmcp_context:
            context.fastmcp_context.set_state("user_id", user_id)
            context.fastmcp_context.set_state("user_email", user_email)
            context.fastmcp_context.set_state("user_role", user_role)
        
        return await call_next(context)


class RBACEnforcementMiddleware(Middleware):
    """Enforce role-based access control at the tool level."""
    
    # Tools that require specific roles
    TOOL_PERMISSIONS = {
        "admin_reindex_document": {"admin"},
        "admin_get_collection_stats": {"admin", "teacher"},
        "admin_bulk_operation": {"admin"},
    }
    
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        tool_name = context.message.name
        required_roles = self.TOOL_PERMISSIONS.get(tool_name, set())
        
        if required_roles:
            user_role = context.fastmcp_context.get_state("user_role") or "guest"
            
            if user_role not in required_roles:
                logger.warning(
                    f"Access denied: {user_role} tried to access {tool_name}"
                )
                raise ToolError(
                    f"Access denied. This operation requires: {', '.join(required_roles)}"
                )
        
        return await call_next(context)
```

### 4.5 Phase 1 Checklist

| Task | File(s) | Est. Time |
|------|---------|-----------|
| ☐ Update FastMCP initialization | `main.py` | 30 min |
| ☐ Create lifespan module | `src/server/lifespan.py` | 45 min |
| ☐ Refactor search tool | `src/tools/search.py` | 60 min |
| ☐ Create middleware module | `src/middleware/mcp_middleware.py` | 60 min |
| ☐ Wire middleware in main.py | `main.py` | 20 min |
| ☐ Test basic functionality | - | 30 min |

**Total Phase 1:** ~4-5 hours

---

## 5. Phase 2: Resources & Prompts

**Goal:** Add read-only data exposure and reusable LLM interaction templates.

### 5.1 Static Resources

**File:** `src/resources/metadata.py` (NEW)

```python
from fastmcp import FastMCP
import json

def register_metadata_resources(mcp: FastMCP):
    """Register static metadata resources."""
    
    @mcp.resource(
        uri="leowiki://categories",
        name="Content Categories",
        description="List of all available content categories in LeoWiki",
        mime_type="application/json",
        tags={"metadata", "navigation"}
    )
    def get_categories() -> str:
        """Returns available content categories with counts."""
        categories = [
            {
                "id": "sew",
                "name": "Software Engineering",
                "name_de": "Softwareentwicklung",
                "description": "Programming, OOP, Design Patterns, etc.",
                "icon": "💻"
            },
            {
                "id": "nwt",
                "name": "Network Technology",
                "name_de": "Netzwerktechnik",
                "description": "Networking, Cisco, Protocols, etc.",
                "icon": "🌐"
            },
            {
                "id": "medientechnik",
                "name": "Media Technology",
                "name_de": "Medientechnik",
                "description": "Graphics, Video, Audio, Web Design",
                "icon": "🎨"
            },
            {
                "id": "syp",
                "name": "Systems Engineering",
                "name_de": "Systemplanung",
                "description": "Project management, Requirements, Testing",
                "icon": "📊"
            },
            {
                "id": "allgemein",
                "name": "General Information",
                "name_de": "Allgemeine Informationen",
                "description": "School info, Schedules, Guidelines",
                "icon": "📚"
            }
        ]
        return json.dumps(categories, ensure_ascii=False, indent=2)
    
    
    @mcp.resource(
        uri="leowiki://access-levels",
        name="Access Level Documentation",
        description="Explains the RBAC access levels and their permissions",
        mime_type="application/json",
        tags={"metadata", "rbac", "documentation"}
    )
    def get_access_levels() -> str:
        """Returns RBAC level descriptions."""
        levels = {
            "student": {
                "name": "Student",
                "description": "Access to student-level educational content",
                "can_access": ["student"],
                "typical_users": "HTL students"
            },
            "teacher": {
                "name": "Teacher", 
                "description": "Access to student and teacher content including exam materials",
                "can_access": ["student", "teacher"],
                "typical_users": "HTL teachers and staff"
            },
            "admin": {
                "name": "Administrator",
                "description": "Full access to all content and administrative functions",
                "can_access": ["student", "teacher", "admin"],
                "typical_users": "IT administrators, department heads"
            }
        }
        return json.dumps(levels, ensure_ascii=False, indent=2)
    
    
    @mcp.resource(
        uri="leowiki://search-hints",
        name="Search Tips",
        description="Tips for effective searching in LeoWiki",
        mime_type="text/markdown",
        tags={"help", "documentation"}
    )
    def get_search_hints() -> str:
        """Returns search usage tips."""
        return """# LeoWiki Search Tips

## Effective Queries
- Use **specific terms**: "Java ArrayList iteration" works better than "Java"
- Try **German terms**: Content is primarily in German
- Combine concepts: "OOP Vererbung Polymorphismus"

## Category Filtering
Available categories: `sew`, `nwt`, `medientechnik`, `syp`, `allgemein`

Example: Search "Subnetting" in category "nwt"

## Access Levels
Your results are filtered based on your role:
- **Students**: See course materials and tutorials
- **Teachers**: Also see exam materials and solutions
- **Admins**: See all content including internal docs

## Not Finding Results?
1. Try broader search terms
2. Remove category filters
3. Check for spelling (especially German terms)
4. Use synonyms (e.g., "Netzwerk" vs "Network")
"""
```

### 5.2 Dynamic Resource Templates

**File:** `src/resources/content.py` (NEW)

```python
from fastmcp import FastMCP, Context
import json

def register_content_resources(mcp: FastMCP):
    """Register dynamic content resources."""
    
    @mcp.resource(
        uri="leowiki://stats",
        name="Collection Statistics",
        description="Current statistics about the LeoWiki knowledge base",
        mime_type="application/json",
        tags={"metadata", "stats"}
    )
    async def get_stats(ctx: Context) -> str:
        """Returns live database statistics."""
        from src.server.lifespan import AppContext
        
        app: AppContext = ctx.lifespan_context
        
        try:
            collection_info = await app.qdrant.get_collection(
                app.config.default_collection
            )
            
            stats = {
                "collection": app.config.default_collection,
                "total_documents": collection_info.points_count,
                "vector_dimensions": collection_info.config.params.vectors.size,
                "status": "healthy",
                "last_checked": datetime.now().isoformat()
            }
        except Exception as e:
            stats = {
                "status": "error",
                "error": str(e)
            }
        
        return json.dumps(stats, indent=2)
    
    
    @mcp.resource(
        uri="leowiki://topic/{topic_id}",
        name="Topic Details",
        description="Detailed information about a specific topic",
        mime_type="application/json",
        tags={"content", "dynamic"}
    )
    async def get_topic(topic_id: str, ctx: Context) -> str:
        """
        Retrieve detailed content for a specific topic.
        
        Example URIs:
        - leowiki://topic/sew-java-oop
        - leowiki://topic/nwt-subnetting-basics
        """
        from src.server.lifespan import AppContext
        
        app: AppContext = ctx.lifespan_context
        user_role = ctx.get_state("user_role") or "student"
        
        # Search for the specific topic
        results = await app.qdrant.scroll(
            collection_name=app.config.default_collection,
            scroll_filter={
                "must": [
                    {"key": "topic_id", "match": {"value": topic_id}}
                ]
            },
            limit=1,
            with_payload=True
        )
        
        if not results[0]:
            return json.dumps({
                "error": "Topic not found",
                "topic_id": topic_id
            })
        
        topic = results[0][0]
        
        # Check access level
        topic_level = topic.payload.get("access_level", "student")
        if not has_access(user_role, topic_level):
            return json.dumps({
                "error": "Access denied",
                "required_level": topic_level,
                "your_level": user_role
            })
        
        return json.dumps({
            "id": topic_id,
            "title": topic.payload.get("title"),
            "content": topic.payload.get("text"),
            "category": topic.payload.get("category"),
            "access_level": topic_level,
            "metadata": {
                "author": topic.payload.get("author"),
                "last_updated": topic.payload.get("updated_at"),
                "source": topic.payload.get("source")
            }
        }, ensure_ascii=False, indent=2)
    
    
    @mcp.resource(
        uri="leowiki://recent/{count}",
        name="Recent Updates",
        description="Recently updated content",
        mime_type="application/json",
        tags={"content", "dynamic"}
    )
    async def get_recent(count: int, ctx: Context) -> str:
        """Get recently updated documents."""
        count = min(count, 20)  # Cap at 20
        
        # Implementation to fetch recent by timestamp
        # ...
        
        return json.dumps(recent_items)
```

### 5.3 Educational Prompts

**File:** `src/prompts/educational.py` (NEW)

```python
from fastmcp import FastMCP, Context
from fastmcp.prompts import Message

def register_educational_prompts(mcp: FastMCP):
    """Register educational prompt templates."""
    
    @mcp.prompt(
        name="explain_topic",
        description="Generate a structured explanation for an educational topic",
        tags={"education", "explanation", "german"}
    )
    def explain_topic(
        topic: str,
        difficulty: str = "intermediate",
        include_examples: bool = True
    ) -> str:
        """
        Creates a pedagogically structured explanation request.
        
        Args:
            topic: The topic to explain (e.g., "Polymorphismus", "TCP/IP")
            difficulty: beginner, intermediate, or advanced
            include_examples: Whether to include practical examples
        """
        difficulty_map = {
            "beginner": "Anfänger (keine Vorkenntnisse)",
            "intermediate": "Fortgeschritten (Grundkenntnisse vorhanden)",
            "advanced": "Experte (vertiefte Kenntnisse)"
        }
        
        prompt = f"""Erkläre das Thema "{topic}" für einen Schüler auf dem Niveau: {difficulty_map.get(difficulty, difficulty)}.

Strukturiere deine Erklärung wie folgt:

## 1. Definition
Eine klare, präzise Definition des Konzepts.

## 2. Kernkonzepte
Die wichtigsten Aspekte, die man verstehen muss.

## 3. Warum ist das wichtig?
Praktische Relevanz und Anwendungsgebiete.
"""
        
        if include_examples:
            prompt += """
## 4. Praktische Beispiele
Konkrete Codebeispiele oder Anwendungsfälle.

## 5. Häufige Fehler
Typische Missverständnisse und wie man sie vermeidet.
"""
        
        prompt += """
## Zusammenfassung
Die wichtigsten Punkte in 2-3 Sätzen.

Sprache: Deutsch
Kontext: HTL Leonding, Informatik-Ausbildung
"""
        return prompt
    
    
    @mcp.prompt(
        name="create_quiz",
        description="Generate quiz questions for a topic",
        tags={"education", "quiz", "assessment"}
    )
    def create_quiz(
        topic: str,
        num_questions: int = 5,
        question_type: str = "mixed",
        difficulty: str = "intermediate"
    ) -> str:
        """
        Creates a quiz generation prompt.
        
        Args:
            topic: Subject for the quiz
            num_questions: Number of questions (1-10)
            question_type: multiple_choice, true_false, short_answer, or mixed
            difficulty: beginner, intermediate, advanced
        """
        num_questions = min(max(num_questions, 1), 10)
        
        type_instructions = {
            "multiple_choice": "Multiple-Choice mit 4 Optionen (A-D)",
            "true_false": "Wahr/Falsch-Fragen",
            "short_answer": "Kurzantwort-Fragen",
            "mixed": "Eine Mischung aus verschiedenen Fragetypen"
        }
        
        return f"""Erstelle ein Quiz zum Thema "{topic}".

**Anforderungen:**
- Anzahl Fragen: {num_questions}
- Fragetyp: {type_instructions.get(question_type, question_type)}
- Schwierigkeitsgrad: {difficulty}

**Für jede Frage:**
1. Klare Fragestellung
2. Bei Multiple-Choice: 4 Optionen, eine richtig
3. Korrekte Antwort markiert
4. Kurze Erklärung (1-2 Sätze)

**Format:** 
```json
{{
  "topic": "{topic}",
  "questions": [
    {{
      "id": 1,
      "type": "multiple_choice",
      "question": "...",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct": "B",
      "explanation": "..."
    }}
  ]
}}
```

Sprache: Deutsch
Kontext: HTL Informatik-Ausbildung
"""
    
    
    @mcp.prompt(
        name="compare_concepts",
        description="Compare two or more related concepts",
        tags={"education", "comparison", "analysis"}
    )
    def compare_concepts(
        concepts: str,  # Comma-separated: "Vererbung, Komposition"
        aspects: str = "definition,usage,advantages,disadvantages"
    ) -> str:
        """
        Creates a comparison prompt for related concepts.
        
        Args:
            concepts: Comma-separated list of concepts to compare
            aspects: Comma-separated aspects to compare
        """
        concept_list = [c.strip() for c in concepts.split(",")]
        aspect_list = [a.strip() for a in aspects.split(",")]
        
        return f"""Vergleiche die folgenden Konzepte: {', '.join(concept_list)}

Erstelle eine strukturierte Vergleichsanalyse mit folgenden Aspekten:

{chr(10).join(f'## {a.title()}' for a in aspect_list)}

**Format:**
Verwende eine Vergleichstabelle wo sinnvoll.

**Abschluss:**
- Wann sollte man welches Konzept verwenden?
- Praktische Entscheidungshilfe

Sprache: Deutsch
Kontext: HTL Informatik-Ausbildung
"""
    
    
    @mcp.prompt(
        name="summarize_search",
        description="Summarize search results into a coherent answer",
        tags={"search", "summary"}
    )
    async def summarize_search(
        query: str,
        ctx: Context
    ) -> str:
        """
        Creates a prompt to summarize search results.
        Uses the server's search capability first.
        """
        # Read the categories resource for context
        categories = await ctx.read_resource("leowiki://categories")
        
        return f"""Der Benutzer hat nach "{query}" gesucht.

Verfügbare Kategorien im LeoWiki:
{categories.content}

Bitte:
1. Fasse die relevanten Suchergebnisse zusammen
2. Strukturiere die Information logisch
3. Hebe die wichtigsten Punkte hervor
4. Empfehle weiterführende Themen falls relevant

Sprache: Deutsch
"""
    
    
    @mcp.prompt(
        name="learning_path",
        description="Generate a learning roadmap for a topic",
        tags={"education", "planning", "curriculum"}
    )
    def learning_path(
        goal: str,
        current_level: str = "beginner",
        time_available: str = "1 month"
    ) -> list[Message]:
        """
        Creates a multi-turn learning path conversation.
        
        Args:
            goal: Learning goal (e.g., "Java Backend Development")
            current_level: Current knowledge level
            time_available: Time frame for learning
        """
        return [
            Message(
                role="user",
                content=f"""Ich möchte "{goal}" lernen.

Mein aktuelles Niveau: {current_level}
Verfügbare Zeit: {time_available}

Erstelle einen strukturierten Lernplan mit:
1. Voraussetzungen die ich prüfen sollte
2. Wochenweise Themenaufteilung
3. Empfohlene Ressourcen aus dem LeoWiki
4. Praktische Übungsprojekte
5. Meilensteine zur Selbstüberprüfung"""
            ),
            Message(
                role="assistant",
                content=f"""Gerne erstelle ich dir einen personalisierten Lernplan für "{goal}"!

Lass mich zuerst die verfügbaren Ressourcen im LeoWiki prüfen und dann einen strukturierten Plan erstellen..."""
            )
        ]
```

### 5.4 Phase 2 Checklist

| Task | File(s) | Est. Time |
|------|---------|-----------|
| ☐ Create metadata resources | `src/resources/metadata.py` | 60 min |
| ☐ Create dynamic resources | `src/resources/content.py` | 90 min |
| ☐ Create educational prompts | `src/prompts/educational.py` | 90 min |
| ☐ Register in main.py | `main.py` | 20 min |
| ☐ Test resources via Client | - | 30 min |
| ☐ Test prompts via Inspector | - | 30 min |

**Total Phase 2:** ~6-7 hours

---

## 6. Phase 3: Advanced Features

**Goal:** Implement server composition, additional tools, and production hardening.

### 6.1 Server Composition (Modular Architecture)

**File:** `src/servers/__init__.py` (NEW)

```python
from fastmcp import FastMCP

from src.servers.search import create_search_server
from src.servers.content import create_content_server
from src.servers.admin import create_admin_server

def compose_servers(main: FastMCP):
    """Compose all module servers into the main server."""
    
    # Create module servers
    search_mcp = create_search_server()
    content_mcp = create_content_server()
    admin_mcp = create_admin_server()
    
    # Mount with prefixes
    # Tools become: search_search_content, content_get_document, admin_reindex
    main.mount(search_mcp, prefix="search")
    main.mount(content_mcp, prefix="content")
    main.mount(admin_mcp, prefix="admin")
    
    return main
```

### 6.2 Additional Tools

**File:** `src/servers/content.py` (NEW)

```python
from fastmcp import FastMCP, Context
from fastmcp.tools import ToolAnnotations

def create_content_server() -> FastMCP:
    """Create the content module MCP server."""
    
    content_mcp = FastMCP(name="ContentModule", tags={"content"})
    
    @content_mcp.tool(
        name="get_document",
        description="Retrieve a complete document by ID",
        annotations=ToolAnnotations(readOnlyHint=True),
        tags={"content", "read-only"}
    )
    async def get_document(
        document_id: str,
        ctx: Context
    ) -> dict:
        """Retrieve full document content."""
        # Implementation
        pass
    
    @content_mcp.tool(
        name="list_recent_updates",
        description="List recently updated documents",
        annotations=ToolAnnotations(readOnlyHint=True),
        tags={"content", "read-only"}
    )
    async def list_recent_updates(
        limit: int = 10,
        category: str = None,
        ctx: Context = None
    ) -> dict:
        """List documents updated in the last 7 days."""
        # Implementation
        pass
    
    return content_mcp
```

**File:** `src/servers/admin.py` (NEW)

```python
from fastmcp import FastMCP, Context
from fastmcp.tools import ToolAnnotations
from fastmcp.exceptions import ToolError

def create_admin_server() -> FastMCP:
    """Create the admin module MCP server."""
    
    admin_mcp = FastMCP(name="AdminModule", tags={"admin"})
    
    @admin_mcp.tool(
        name="get_collection_stats",
        description="Get detailed collection statistics (teacher/admin only)",
        annotations=ToolAnnotations(readOnlyHint=True),
        tags={"admin", "stats"}
    )
    async def get_collection_stats(ctx: Context) -> dict:
        """
        Returns detailed database statistics.
        Requires: teacher or admin role
        """
        # RBAC enforced by middleware
        app: AppContext = ctx.lifespan_context
        
        collection = await app.qdrant.get_collection(
            app.config.default_collection
        )
        
        return {
            "collection": app.config.default_collection,
            "points_count": collection.points_count,
            "segments_count": collection.segments_count,
            "status": collection.status.value,
            "optimizer_status": collection.optimizer_status.status.value
        }
    
    @admin_mcp.tool(
        name="reindex_document",
        description="Trigger re-indexing of a document (admin only)",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True
        ),
        tags={"admin", "write"}
    )
    async def reindex_document(
        document_id: str,
        ctx: Context
    ) -> dict:
        """
        Re-index a specific document.
        Requires: admin role
        """
        await ctx.report_progress(0, 3, "Fetching document...")
        # Implementation
        await ctx.report_progress(1, 3, "Generating embedding...")
        # Implementation
        await ctx.report_progress(2, 3, "Updating index...")
        # Implementation
        await ctx.report_progress(3, 3, "Complete!")
        
        return {"status": "reindexed", "document_id": document_id}
    
    @admin_mcp.tool(
        name="health_check",
        description="Comprehensive health check of all systems",
        annotations=ToolAnnotations(readOnlyHint=True),
        tags={"admin", "monitoring"}
    )
    async def health_check(ctx: Context) -> dict:
        """Check health of all server components."""
        app: AppContext = ctx.lifespan_context
        
        checks = {}
        
        # Check Qdrant
        try:
            await app.qdrant.get_collections()
            checks["qdrant"] = {"status": "healthy"}
        except Exception as e:
            checks["qdrant"] = {"status": "unhealthy", "error": str(e)}
        
        # Check embedding service
        try:
            app.embedding_service.embed_query("test")
            checks["embedding"] = {"status": "healthy"}
        except Exception as e:
            checks["embedding"] = {"status": "unhealthy", "error": str(e)}
        
        overall = "healthy" if all(
            c["status"] == "healthy" for c in checks.values()
        ) else "degraded"
        
        return {
            "status": overall,
            "checks": checks,
            "server_version": app.config.server_version
        }
    
    return admin_mcp
```

### 6.3 Caching Layer

**File:** `src/utils/cache.py` (NEW)

```python
from functools import lru_cache
import hashlib
import time
from typing import Any

class QueryCache:
    """Simple TTL cache for search queries."""
    
    def __init__(self, ttl_seconds: int = 300, max_size: int = 100):
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._cache: dict[str, tuple[Any, float]] = {}
    
    def _make_key(self, query: str, **kwargs) -> str:
        """Create cache key from query and parameters."""
        key_data = f"{query}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, query: str, **kwargs) -> Any | None:
        """Get cached result if valid."""
        key = self._make_key(query, **kwargs)
        if key in self._cache:
            result, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl:
                return result
            del self._cache[key]
        return None
    
    def set(self, query: str, result: Any, **kwargs):
        """Cache a result."""
        if len(self._cache) >= self.max_size:
            # Remove oldest entry
            oldest = min(self._cache, key=lambda k: self._cache[k][1])
            del self._cache[oldest]
        
        key = self._make_key(query, **kwargs)
        self._cache[key] = (result, time.time())
    
    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()
```

### 6.4 Phase 3 Checklist

| Task | File(s) | Est. Time |
|------|---------|-----------|
| ☐ Refactor into module servers | `src/servers/*.py` | 120 min |
| ☐ Implement composition | `src/servers/__init__.py` | 30 min |
| ☐ Add content tools | `src/servers/content.py` | 60 min |
| ☐ Add admin tools | `src/servers/admin.py` | 90 min |
| ☐ Implement caching | `src/utils/cache.py` | 45 min |
| ☐ Integration testing | - | 60 min |

**Total Phase 3:** ~7-8 hours

---

## 7. Phase 4: Testing & Documentation

### 7.1 MCP Client Testing

**File:** `tests/test_mcp_tools.py` (NEW)

```python
import pytest
from fastmcp import Client
from main import mcp  # Import your composed server

@pytest.fixture
async def client():
    """Fixture providing connected MCP client."""
    async with Client(mcp) as c:
        yield c

class TestSearchTools:
    """Test search module tools."""
    
    async def test_search_content_basic(self, client):
        """Test basic search functionality."""
        result = await client.call_tool(
            "search_search_content",
            {"query": "Java Grundlagen", "limit": 5}
        )
        
        data = json.loads(result.content[0].text)
        assert "results" in data
        assert data["total"] <= 5
    
    async def test_search_with_category(self, client):
        """Test search with category filter."""
        result = await client.call_tool(
            "search_search_content",
            {"query": "Programmierung", "categories": ["sew"]}
        )
        
        data = json.loads(result.content[0].text)
        assert data["filters_applied"]["categories"] == ["sew"]
    
    async def test_search_empty_query_fails(self, client):
        """Test that empty query is rejected."""
        with pytest.raises(Exception):  # Validation error
            await client.call_tool(
                "search_search_content",
                {"query": "", "limit": 5}
            )

class TestResources:
    """Test resource access."""
    
    async def test_categories_resource(self, client):
        """Test categories resource."""
        result = await client.read_resource("leowiki://categories")
        
        categories = json.loads(result.content)
        assert isinstance(categories, list)
        assert len(categories) > 0
        assert all("id" in c for c in categories)
    
    async def test_stats_resource(self, client):
        """Test stats resource."""
        result = await client.read_resource("leowiki://stats")
        
        stats = json.loads(result.content)
        assert "total_documents" in stats
        assert stats["status"] == "healthy"
    
    async def test_topic_template(self, client):
        """Test dynamic topic resource."""
        result = await client.read_resource("leowiki://topic/test-topic-id")
        
        data = json.loads(result.content)
        # Either found or not found, but should return valid JSON
        assert "id" in data or "error" in data

class TestPrompts:
    """Test prompt templates."""
    
    async def test_list_prompts(self, client):
        """Test that prompts are registered."""
        prompts = await client.list_prompts()
        prompt_names = [p.name for p in prompts]
        
        assert "explain_topic" in prompt_names
        assert "create_quiz" in prompt_names
    
    async def test_explain_topic_prompt(self, client):
        """Test explain_topic prompt generation."""
        result = await client.get_prompt(
            "explain_topic",
            arguments={"topic": "OOP", "difficulty": "beginner"}
        )
        
        content = result.messages[0].content.text
        assert "OOP" in content
        assert "Definition" in content

class TestAdminTools:
    """Test admin module (would need auth mocking)."""
    
    async def test_health_check(self, client):
        """Test health check tool."""
        result = await client.call_tool("admin_health_check", {})
        
        data = json.loads(result.content[0].text)
        assert "status" in data
        assert "checks" in data
```

### 7.2 Documentation Updates

**File:** `README.md` (UPDATED sections)

```markdown
## MCP Capabilities

### Tools

| Tool | Description | Access Level |
|------|-------------|--------------|
| `search_search_content` | Semantic search | All users |
| `search_search_similar` | Find similar docs | All users |
| `content_get_document` | Retrieve document | All users |
| `content_list_recent` | Recent updates | All users |
| `admin_get_stats` | Collection stats | Teacher+ |
| `admin_reindex` | Re-index document | Admin only |
| `admin_health_check` | System health | Admin only |

### Resources

| URI | Description |
|-----|-------------|
| `leowiki://categories` | Content categories |
| `leowiki://stats` | Database statistics |
| `leowiki://access-levels` | RBAC documentation |
| `leowiki://topic/{id}` | Topic details |
| `leowiki://search-hints` | Search tips |

### Prompts

| Prompt | Description |
|--------|-------------|
| `explain_topic` | Educational explanation |
| `create_quiz` | Quiz generation |
| `compare_concepts` | Concept comparison |
| `summarize_search` | Search summary |
| `learning_path` | Learning roadmap |
```

### 7.3 Phase 4 Checklist

| Task | File(s) | Est. Time |
|------|---------|-----------|
| ☐ Create MCP client tests | `tests/test_mcp_tools.py` | 90 min |
| ☐ Test resources | `tests/test_mcp_resources.py` | 45 min |
| ☐ Test prompts | `tests/test_mcp_prompts.py` | 30 min |
| ☐ Update README | `README.md` | 45 min |
| ☐ Create API documentation | `docs/API.md` | 60 min |
| ☐ Final integration test | - | 30 min |

**Total Phase 4:** ~5-6 hours

---

## 8. File Structure Changes

### Current Structure
```
mcp-server/
├── main.py
├── src/
│   ├── auth/
│   ├── backends/
│   ├── config/
│   ├── interfaces/
│   ├── middleware/
│   ├── pipeline/
│   ├── server/
│   ├── tools/
│   │   └── search_tools.py
│   └── utils/
└── tests/
```

### Target Structure
```
mcp-server/
├── main.py                          # Simplified entry point
├── src/
│   ├── auth/                        # (unchanged)
│   ├── backends/                    # (unchanged)
│   ├── config/                      # (unchanged)
│   ├── interfaces/                  # (unchanged)
│   │
│   ├── middleware/
│   │   ├── auth.py                  # (existing)
│   │   ├── scalekit_auth.py         # (existing)
│   │   └── mcp_middleware.py        # NEW: MCP-level middleware
│   │
│   ├── server/
│   │   ├── base.py                  # (existing)
│   │   ├── http_server.py           # (existing)
│   │   ├── oauth_metadata.py        # (existing)
│   │   └── lifespan.py              # NEW: Dependency injection
│   │
│   ├── servers/                     # NEW: Modular MCP servers
│   │   ├── __init__.py              # Composition logic
│   │   ├── search.py                # Search module
│   │   ├── content.py               # Content module
│   │   └── admin.py                 # Admin module
│   │
│   ├── resources/                   # NEW: MCP Resources
│   │   ├── __init__.py
│   │   ├── metadata.py              # Static resources
│   │   └── content.py               # Dynamic resources
│   │
│   ├── prompts/                     # NEW: MCP Prompts
│   │   ├── __init__.py
│   │   └── educational.py           # Educational prompts
│   │
│   ├── tools/                       # REFACTORED
│   │   ├── __init__.py
│   │   └── search_tools.py          # Utility functions only
│   │
│   └── utils/
│       ├── embeddings.py            # (existing)
│       └── cache.py                 # NEW: Query cache
│
├── tests/
│   ├── test_mcp_tools.py            # NEW: Tool tests
│   ├── test_mcp_resources.py        # NEW: Resource tests
│   ├── test_mcp_prompts.py          # NEW: Prompt tests
│   └── ... (existing tests)
│
└── docs/
    └── API.md                       # NEW: API documentation
```

---

## 9. Migration Guide

### Step-by-Step Migration

#### Step 1: Create New Files (Non-Breaking)
```bash
# Create new directories
mkdir -p src/servers src/resources src/prompts docs

# Create new files
touch src/server/lifespan.py
touch src/middleware/mcp_middleware.py
touch src/servers/__init__.py
touch src/servers/search.py
touch src/servers/content.py
touch src/servers/admin.py
touch src/resources/__init__.py
touch src/resources/metadata.py
touch src/resources/content.py
touch src/prompts/__init__.py
touch src/prompts/educational.py
touch src/utils/cache.py
```

#### Step 2: Implement Lifespan (Non-Breaking)
1. Create `src/server/lifespan.py`
2. Test independently
3. Wire into main.py

#### Step 3: Implement Middleware (Non-Breaking)
1. Create `src/middleware/mcp_middleware.py`
2. Test independently
3. Add to main.py middleware stack

#### Step 4: Create Module Servers (Feature Addition)
1. Create search, content, admin servers
2. Keep existing tools working
3. Add new tools incrementally

#### Step 5: Add Resources (Feature Addition)
1. Create static resources first
2. Add dynamic resources
3. Test via MCP Inspector

#### Step 6: Add Prompts (Feature Addition)
1. Create educational prompts
2. Test via MCP Inspector
3. Refine based on feedback

#### Step 7: Enable Composition (Refactor)
1. Wire module servers into main
2. Update tool names in any clients
3. Run full test suite

#### Step 8: Cleanup & Documentation
1. Remove deprecated code
2. Update documentation
3. Final testing

### Rollback Plan

Each phase is designed to be independently reversible:

- **Phase 1**: Revert main.py changes
- **Phase 2**: Remove resource/prompt registrations
- **Phase 3**: Switch back to monolithic tools
- **Phase 4**: Tests are additive, no rollback needed

---

## 10. Risk Assessment

### Low Risk ✅

| Change | Risk | Mitigation |
|--------|------|------------|
| Add resources | None | Additive feature |
| Add prompts | None | Additive feature |
| Add middleware | Low | Tested independently |
| Add new tools | None | Additive feature |

### Medium Risk ⚠️

| Change | Risk | Mitigation |
|--------|------|------------|
| Lifespan refactor | Backend init changes | Test thoroughly |
| Tool naming (composition) | Client breaking | Document new names |
| Error masking | Hidden bugs | Good logging |

### Mitigation Strategies

1. **Feature Flags**: Use config to enable/disable new features
2. **Gradual Rollout**: Deploy to test environment first
3. **Comprehensive Testing**: MCP Client tests catch regressions
4. **Monitoring**: Enhanced logging shows issues quickly

---

## Summary

### Effort Distribution

| Phase | Hours | Priority |
|-------|-------|----------|
| Phase 1: Core | 4-5 | 🔴 Critical |
| Phase 2: Resources/Prompts | 6-7 | 🟠 High |
| Phase 3: Advanced | 7-8 | 🟡 Medium |
| Phase 4: Testing/Docs | 5-6 | 🟢 Important |
| **Total** | **22-26** | |

### Key Deliverables

1. ✅ Production-ready server initialization
2. ✅ Proper dependency injection via lifespan
3. ✅ 6 MCP Resources for context
4. ✅ 5 Educational prompts
5. ✅ 8 Tools (up from 2)
6. ✅ Custom middleware for RBAC
7. ✅ Modular server composition
8. ✅ Comprehensive MCP Client tests
9. ✅ Updated documentation

### Success Criteria

- [ ] All existing functionality preserved
- [ ] New features accessible via MCP Inspector
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Ready for diploma thesis presentation

---

*Document Version: 1.0*  
*Created: January 2026*  
*Target Completion: February 2026*
