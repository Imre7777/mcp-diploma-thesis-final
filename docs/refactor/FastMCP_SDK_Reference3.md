# FastMCP SDK Complete Reference for Educational MCP Servers

A comprehensive guide to FastMCP v2.x SDK features for building professional educational MCP servers. This document focuses on features and patterns NOT yet implemented in your current LeoWiki MCP server.

---

## Table of Contents

1. [Server Initialization Options](#1-server-initialization-options)
2. [Resources System](#2-resources-system)
3. [Prompts System](#3-prompts-system)
4. [Context Object (Full API)](#4-context-object-full-api)
5. [Tool Advanced Features](#5-tool-advanced-features)
6. [Media Classes (Image, Audio)](#6-media-classes-image-audio)
7. [HTTP Streamable Transport](#7-http-streamable-transport)
8. [Server Composition](#8-server-composition)
9. [Middleware System](#9-middleware-system)
10. [Tags and Visibility](#10-tags-and-visibility)
11. [Lifespan and Dependency Injection](#11-lifespan-and-dependency-injection)
12. [Testing with FastMCP Client](#12-testing-with-fastmcp-client)
13. [Implementation Recommendations for LeoWiki](#13-implementation-recommendations-for-leowiki)

---

## 1. Server Initialization Options

### Current Implementation (Your Code)
```python
mcp = FastMCP(
    name=config.server_name,
    stateless_http=True
)
```

### Full Constructor Options
```python
from fastmcp import FastMCP

mcp = FastMCP(
    # Basic identity
    name="MCP Educational Server",              # Server name (shown to clients)
    instructions="Search HTL Leonding's wiki",  # Instructions for LLMs on how to use this server
    
    # HTTP Transport settings
    stateless_http=True,                        # Enable stateless mode for horizontal scaling
    json_response=True,                         # Disable SSE, pure JSON responses (simpler)
    
    # Security
    mask_error_details=True,                    # Hide internal errors from clients (PRODUCTION!)
    
    # Behavior
    on_duplicate_tools="error",                 # "error" | "warn" | "replace" | "ignore"
    
    # Tags for organization
    tags={"educational", "search", "htl"},      # Server-level tags
    
    # Lifespan for dependency injection
    lifespan=app_lifespan,                      # Async context manager
    
    # Dependencies for deployment
    dependencies=["qdrant-client", "openai"],   # Packages needed when deployed
)
```

### Key Settings You Should Add
```python
mcp = FastMCP(
    name=config.server_name,
    instructions="""
    This MCP server provides access to HTL Leonding's educational wiki (LeoWiki).
    Use search_content to find information about courses, tutorials, and school resources.
    Results are filtered by your access level (student, teacher, admin).
    """,
    stateless_http=True,
    json_response=False,          # Keep SSE for progress reporting
    mask_error_details=True,      # IMPORTANT for production security
    on_duplicate_tools="error",   # Catch registration errors early
)
```

---

## 2. Resources System

Resources expose read-only data to LLM clients. Think of them as GET endpoints that provide context.

### Static Resources
```python
import json

@mcp.resource(
    uri="leowiki://categories",
    name="Available Categories",
    description="List of all content categories in LeoWiki",
    mime_type="application/json",
    tags={"metadata", "navigation"}
)
def get_categories() -> str:
    """Returns available content categories."""
    categories = [
        {"id": "sew", "name": "Software Engineering", "count": 150},
        {"id": "nwt", "name": "Netzwerktechnik", "count": 89},
        {"id": "medientechnik", "name": "Medientechnik", "count": 67},
        {"id": "allgemein", "name": "Allgemeine Infos", "count": 234},
    ]
    return json.dumps(categories, ensure_ascii=False)


@mcp.resource(
    uri="leowiki://stats",
    name="Collection Statistics",
    description="Statistics about the educational content database",
    mime_type="application/json"
)
async def get_stats() -> str:
    """Returns database statistics."""
    # Access your Qdrant backend
    collection_info = await get_collection_info()
    return json.dumps({
        "total_documents": collection_info.points_count,
        "categories": len(get_categories()),
        "last_updated": "2026-01-26T10:00:00Z"
    })
```

### Resource Templates (Dynamic URIs)
```python
@mcp.resource(
    uri="leowiki://topic/{topic_id}",
    name="Topic Details",
    description="Get detailed information about a specific topic",
    mime_type="application/json"
)
async def get_topic(topic_id: str) -> str:
    """
    Retrieve detailed content for a specific topic.
    
    Example URIs:
    - leowiki://topic/sew-java-basics
    - leowiki://topic/nwt-subnetting
    """
    content = await fetch_topic_from_qdrant(topic_id)
    return json.dumps(content, ensure_ascii=False)


@mcp.resource(
    uri="leowiki://search-history/{user_id}",
    name="User Search History",
    description="Recent searches for a specific user"
)
async def get_search_history(user_id: str, ctx: Context) -> str:
    """Get search history (requires teacher/admin role)."""
    # Access user context from authentication
    user_role = ctx.get_state("user_role")
    if user_role not in ["teacher", "admin"]:
        return json.dumps({"error": "Access denied"})
    
    history = await fetch_user_history(user_id)
    return json.dumps(history)
```

### Wildcard Resource Templates
```python
@mcp.resource(
    uri="leowiki://documents/{path*}",
    name="Document Browser",
    description="Access documents by path",
    mime_type="text/markdown"
)
def get_document(path: str) -> str:
    """
    Access documents using hierarchical paths.
    
    Example URIs:
    - leowiki://documents/sew/java/oop
    - leowiki://documents/nwt/cisco/routing/basics
    """
    return load_document_by_path(path)
```

### Resource Annotations
```python
from fastmcp.resources import ResourceAnnotations

@mcp.resource(
    uri="leowiki://recent-updates",
    annotations=ResourceAnnotations(
        audience=["user", "assistant"],  # Who can see this
    )
)
def get_recent_updates() -> str:
    """Recently updated content."""
    return json.dumps(get_updates_from_db())
```

---

## 3. Prompts System

Prompts are reusable templates that guide LLM interactions. They're extremely useful for educational contexts.

### Basic Prompts
```python
from fastmcp.prompts import Message

@mcp.prompt(
    name="explain_topic",
    description="Generate an explanation request for a topic"
)
def explain_topic(
    topic: str,
    difficulty: str = "intermediate",
    language: str = "german"
) -> str:
    """Creates a prompt for explaining educational topics."""
    return f"""Erkläre das Thema "{topic}" auf {difficulty}-Niveau.
    
Bitte strukturiere die Erklärung wie folgt:
1. Kurze Definition
2. Kernkonzepte
3. Praktische Beispiele
4. Häufige Fehler/Missverständnisse
5. Weiterführende Themen

Sprache: {language}"""


@mcp.prompt(
    name="create_quiz",
    description="Generate quiz questions for a topic"
)
def create_quiz(
    topic: str,
    num_questions: int = 5,
    question_type: str = "multiple_choice"
) -> str:
    """Creates a quiz generation prompt."""
    return f"""Erstelle {num_questions} {question_type} Fragen zum Thema "{topic}".

Für jede Frage:
- Eine klare Fragestellung
- 4 Antwortmöglichkeiten (bei Multiple Choice)
- Die korrekte Antwort markieren
- Kurze Erklärung warum die Antwort richtig ist

Format: JSON"""
```

### Multi-Message Prompts
```python
@mcp.prompt(
    name="tutoring_session",
    description="Start an interactive tutoring session"
)
def tutoring_session(
    subject: str,
    student_level: str = "beginner"
) -> list[Message]:
    """Creates a multi-turn tutoring prompt."""
    return [
        Message(
            role="user",
            content=f"""Ich möchte {subject} lernen. Mein aktuelles Niveau: {student_level}.
            
Bitte führe mich Schritt für Schritt durch die wichtigsten Konzepte.
Stelle nach jeder Erklärung eine Verständnisfrage."""
        ),
        Message(
            role="assistant", 
            content=f"""Willkommen zur Lerneinheit über {subject}! 
            
Ich werde dir die Konzepte schrittweise erklären und dein Verständnis überprüfen. 
Lass uns beginnen mit den Grundlagen..."""
        )
    ]
```

### Context-Aware Prompts
```python
@mcp.prompt(
    name="search_assistant",
    description="Help user formulate better search queries"
)
async def search_assistant(
    initial_query: str,
    ctx: Context
) -> str:
    """Uses server resources to improve search queries."""
    # Read available categories from our own resource
    categories_data = await ctx.read_resource("leowiki://categories")
    categories = json.loads(categories_data.content)
    
    category_list = ", ".join([c["name"] for c in categories])
    
    return f"""Der Benutzer sucht nach: "{initial_query}"

Verfügbare Kategorien: {category_list}

Hilf dem Benutzer, seine Suchanfrage zu verfeinern:
1. Schlage relevante Kategorien vor
2. Empfehle spezifischere Suchbegriffe
3. Frage nach dem Kontext (Unterrichtsfach, Jahrgang, etc.)"""
```

---

## 4. Context Object (Full API)

The Context object provides access to MCP session capabilities. You're currently only using basic features.

### Complete Context API
```python
from fastmcp import FastMCP, Context

@mcp.tool
async def comprehensive_search(
    query: str,
    ctx: Context
) -> dict:
    """Demonstrates all Context features."""
    
    # ═══════════════════════════════════════════════════════════
    # 1. LOGGING - Send messages to the MCP client
    # ═══════════════════════════════════════════════════════════
    await ctx.debug(f"Starting search for: {query}")
    await ctx.info(f"Searching educational content...")
    await ctx.warning("Large result set expected")
    await ctx.error("Connection timeout - retrying...")  # For actual errors
    
    # ═══════════════════════════════════════════════════════════
    # 2. PROGRESS REPORTING - For long-running operations
    # ═══════════════════════════════════════════════════════════
    total_steps = 4
    
    await ctx.report_progress(0, total_steps, "Generating embedding...")
    embedding = await generate_embedding(query)
    
    await ctx.report_progress(1, total_steps, "Searching Qdrant...")
    raw_results = await search_qdrant(embedding)
    
    await ctx.report_progress(2, total_steps, "Filtering by access level...")
    filtered = filter_by_rbac(raw_results, ctx.get_state("user_role"))
    
    await ctx.report_progress(3, total_steps, "Formatting results...")
    formatted = format_results(filtered)
    
    await ctx.report_progress(4, total_steps, "Complete!")
    
    # ═══════════════════════════════════════════════════════════
    # 3. RESOURCE ACCESS - Read server's own resources
    # ═══════════════════════════════════════════════════════════
    categories = await ctx.read_resource("leowiki://categories")
    stats = await ctx.read_resource("leowiki://stats")
    
    # ═══════════════════════════════════════════════════════════
    # 4. LLM SAMPLING - Request completions from client's LLM
    # ═══════════════════════════════════════════════════════════
    # Useful for: summarization, translation, reformatting
    if len(formatted) > 5:
        summary_request = f"Fasse diese {len(formatted)} Suchergebnisse kurz zusammen:\n{formatted}"
        summary = await ctx.sample(summary_request)
        # summary.text contains the LLM's response
    
    # ═══════════════════════════════════════════════════════════
    # 5. SESSION STATE - Store/retrieve per-session data
    # ═══════════════════════════════════════════════════════════
    # Get state (set by middleware)
    user_id = ctx.get_state("user_id")
    user_role = ctx.get_state("user_role")
    user_scopes = ctx.get_state("user_scopes")
    
    # Set state for later tools in same session
    ctx.set_state("last_query", query)
    ctx.set_state("result_count", len(formatted))
    
    # ═══════════════════════════════════════════════════════════
    # 6. LIFESPAN CONTEXT - Access injected dependencies
    # ═══════════════════════════════════════════════════════════
    app: AppContext = ctx.lifespan_context
    # app.qdrant, app.embedding_service, app.config, etc.
    
    # ═══════════════════════════════════════════════════════════
    # 7. REQUEST METADATA
    # ═══════════════════════════════════════════════════════════
    request_id = ctx.request_id
    session_id = ctx.session_id
    
    return {"results": formatted, "count": len(formatted)}
```

### Practical Progress Reporting Example
```python
@mcp.tool(
    name="bulk_index",
    description="Index multiple documents (admin only)"
)
async def bulk_index(
    document_ids: list[str],
    ctx: Context
) -> dict:
    """Index multiple documents with progress tracking."""
    
    user_role = ctx.get_state("user_role")
    if user_role != "admin":
        raise ToolError("Admin access required")
    
    total = len(document_ids)
    indexed = 0
    errors = []
    
    for i, doc_id in enumerate(document_ids):
        await ctx.report_progress(
            i, 
            total, 
            f"Indexing document {i+1}/{total}: {doc_id}"
        )
        
        try:
            await index_document(doc_id)
            indexed += 1
        except Exception as e:
            await ctx.warning(f"Failed to index {doc_id}: {e}")
            errors.append({"id": doc_id, "error": str(e)})
    
    await ctx.report_progress(total, total, "Indexing complete!")
    await ctx.info(f"Successfully indexed {indexed}/{total} documents")
    
    return {
        "total": total,
        "indexed": indexed,
        "errors": errors
    }
```

---

## 5. Tool Advanced Features

### Tool Annotations (Hints for Clients)
```python
from fastmcp.tools import ToolAnnotations

@mcp.tool(
    name="search_content",
    description="Search educational content",
    annotations=ToolAnnotations(
        title="LeoWiki Search",           # Human-readable title
        readOnlyHint=True,                # Signals: no side effects, safe to cache
        idempotentHint=True,              # Same input = same output
        openWorldHint=False,              # Results are bounded/known
    ),
    tags={"search", "read-only"}
)
async def search_content(query: str, ctx: Context) -> dict:
    """Search with proper annotations for better client behavior."""
    pass


@mcp.tool(
    name="update_document",
    annotations=ToolAnnotations(
        readOnlyHint=False,               # Has side effects
        destructiveHint=False,            # Doesn't delete data
        idempotentHint=True,              # Safe to retry
    )
)
async def update_document(doc_id: str, content: str) -> dict:
    """Update a document (not read-only)."""
    pass
```

### Parameter Metadata with Pydantic Field
```python
from typing import Annotated
from pydantic import Field

@mcp.tool
async def advanced_search(
    query: Annotated[str, Field(
        description="Search query text",
        min_length=1,
        max_length=500,
        examples=["Java Grundlagen", "Netzwerk Subnetting"]
    )],
    
    limit: Annotated[int, Field(
        description="Maximum results to return",
        ge=1,
        le=100,
        default=10
    )],
    
    categories: Annotated[list[str], Field(
        description="Filter by categories",
        default=[],
        max_length=5
    )],
    
    include_metadata: Annotated[bool, Field(
        description="Include source metadata in results",
        default=True
    )],
    
    ctx: Context
) -> dict:
    """Search with fully documented parameters."""
    pass
```

### Hiding Parameters from LLM Schema
```python
from fastmcp import Context
from fastmcp.server.dependencies import Secret

@mcp.tool
async def admin_operation(
    action: str,
    # These won't appear in the tool schema sent to LLMs:
    ctx: Context,                          # Always hidden
    internal_flag: Annotated[bool, Secret] = False,  # Hidden via Secret
) -> dict:
    """Parameters marked with Context or Secret are hidden."""
    pass
```

---

## 6. Media Classes (Image, Audio)

FastMCP provides helper classes for returning binary media from tools.

### Image Returns
```python
from fastmcp import Image
from PIL import Image as PILImage
from io import BytesIO

@mcp.tool
async def generate_diagram(
    topic: str,
    diagram_type: str = "flowchart"
) -> Image:
    """Generate a diagram for educational content."""
    
    # Create diagram using matplotlib, PIL, etc.
    fig = create_matplotlib_diagram(topic, diagram_type)
    
    # Save to bytes
    buffer = BytesIO()
    fig.savefig(buffer, format='png')
    buffer.seek(0)
    
    return Image(
        data=buffer.getvalue(),
        format="png"
    )


@mcp.tool
async def get_wiki_image(image_path: str) -> Image:
    """Retrieve an image from the wiki."""
    # From file path
    return Image(path=f"/var/data/wiki/images/{image_path}")
    
    # Or from PIL
    # pil_image = PILImage.open(path)
    # return Image.from_pil(pil_image)
```

### Image in Resources
```python
@mcp.resource(
    uri="leowiki://logo",
    mime_type="image/png"
)
def get_logo() -> Image:
    """Returns the school logo."""
    return Image(path="/var/data/assets/htl-logo.png")
```

### Audio Returns
```python
from fastmcp import Audio

@mcp.tool
async def text_to_speech(
    text: str,
    language: str = "de"
) -> Audio:
    """Convert text to speech for accessibility."""
    
    # Generate audio using TTS service
    audio_data = await tts_service.synthesize(text, language)
    
    return Audio(
        data=audio_data,
        format="mp3"
    )
```

---

## 7. HTTP Streamable Transport

### Complete HTTP Configuration
```python
from fastmcp import FastMCP

# Stateless mode for horizontal scaling (your current setup)
mcp = FastMCP(
    name="LeoWiki MCP",
    stateless_http=True,    # No server-side session state
    json_response=False,    # Keep SSE for streaming/progress
)

# Run options
if __name__ == "__main__":
    mcp.run(
        transport="http",           # or "streamable-http"
        host="0.0.0.0",
        port=8000,
        path="/mcp",               # Endpoint path
        log_level="info",
    )
```

### FastAPI Integration (Your Current Pattern - Enhanced)
```python
from fastapi import FastAPI
from fastmcp import FastMCP

# Create FastMCP instance
mcp = FastMCP(
    name="LeoWiki Educational Server",
    stateless_http=True
)

# Get ASGI app with custom path
mcp_app = mcp.http_app(path="/mcp")

# Create FastAPI wrapper
app = FastAPI(
    title="LeoWiki MCP Server",
    version="2.0.0",
    lifespan=mcp_app.lifespan  # Use FastMCP's lifespan
)

# Mount MCP
app.mount("/", mcp_app)

# Add your custom endpoints
@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/.well-known/oauth-protected-resource")
async def oauth_discovery():
    return get_oauth_metadata()
```

### Multiple MCP Servers in One FastAPI App
```python
from fastapi import FastAPI
from fastmcp import FastMCP

# Create separate MCP servers
search_mcp = FastMCP(name="SearchServer", stateless_http=True)
admin_mcp = FastMCP(name="AdminServer", stateless_http=True)

# Register tools on each
@search_mcp.tool
async def search_content(query: str): pass

@admin_mcp.tool
async def manage_users(action: str): pass

# Mount both
app = FastAPI()
app.mount("/search", search_mcp.http_app(path="/mcp"))
app.mount("/admin", admin_mcp.http_app(path="/mcp"))

# Now accessible at:
# - http://localhost:8000/search/mcp
# - http://localhost:8000/admin/mcp
```

---

## 8. Server Composition

Combine multiple FastMCP servers into a unified system.

### Using mount() - Live Link
```python
from fastmcp import FastMCP

# Create specialized sub-servers
search_server = FastMCP(name="SearchModule")
admin_server = FastMCP(name="AdminModule")
analytics_server = FastMCP(name="AnalyticsModule")

@search_server.tool
async def search_content(query: str): pass

@admin_server.tool
async def manage_collection(action: str): pass

@analytics_server.tool
async def get_usage_stats(): pass

# Create main server and mount sub-servers
main_server = FastMCP(name="LeoWiki MCP")

# Mount with prefixes - tools become: search_search_content, admin_manage_collection
main_server.mount(search_server, prefix="search")
main_server.mount(admin_server, prefix="admin")
main_server.mount(analytics_server, prefix="analytics")

# Or mount without prefix (tools keep original names)
# main_server.mount(search_server)
```

### Using import_server() - Static Copy
```python
# import_server copies components at startup (faster, but changes not reflected)
await main_server.import_server(search_server, prefix="search")

# Good for: production deployments where mounted servers don't change
# mount() is better for: development, dynamic server composition
```

### Practical Modular Architecture
```python
# src/tools/search.py
from fastmcp import FastMCP

search_mcp = FastMCP(name="SearchService")

@search_mcp.tool
async def search_content(query: str, limit: int = 10): pass

@search_mcp.tool
async def get_similar(doc_id: str): pass

@search_mcp.resource("search://stats")
def search_stats(): pass

# src/tools/content.py
content_mcp = FastMCP(name="ContentService")

@content_mcp.tool
async def get_document(doc_id: str): pass

@content_mcp.resource("content://categories")
def get_categories(): pass

# src/tools/admin.py
admin_mcp = FastMCP(name="AdminService")

@admin_mcp.tool
async def index_document(doc_id: str): pass

@admin_mcp.tool
async def delete_document(doc_id: str): pass

# main.py
from fastmcp import FastMCP
from src.tools.search import search_mcp
from src.tools.content import content_mcp
from src.tools.admin import admin_mcp

main = FastMCP(
    name="LeoWiki MCP Server",
    stateless_http=True,
    lifespan=app_lifespan
)

# Compose the server
main.mount(search_mcp, prefix="search")
main.mount(content_mcp, prefix="content")
main.mount(admin_mcp, prefix="admin")

# Results in tools:
# - search_search_content
# - search_get_similar
# - content_get_document
# - admin_index_document
# - admin_delete_document
```

---

## 9. Middleware System

Add cross-cutting concerns like logging, auth checks, rate limiting.

### Creating Custom Middleware
```python
from fastmcp.server.middleware import Middleware, MiddlewareContext
import time
import uuid

class RequestLoggingMiddleware(Middleware):
    """Log all MCP requests with timing."""
    
    async def on_request(self, context: MiddlewareContext, call_next):
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # Add to context for access in tools
        if context.fastmcp_context:
            context.fastmcp_context.set_state("request_id", request_id)
        
        logger.info(f"[{request_id}] Starting {context.method}")
        
        # Call the next middleware/handler
        result = await call_next(context)
        
        duration_ms = (time.time() - start_time) * 1000
        logger.info(f"[{request_id}] Completed in {duration_ms:.2f}ms")
        
        return result


class RBACMiddleware(Middleware):
    """Enforce role-based access control on tools."""
    
    def __init__(self, tool_permissions: dict[str, set[str]]):
        self.tool_permissions = tool_permissions
    
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        tool_name = context.message.name
        required_roles = self.tool_permissions.get(tool_name, set())
        
        if required_roles:
            user_role = context.fastmcp_context.get_state("user_role") or "guest"
            
            if user_role not in required_roles:
                from fastmcp.exceptions import ToolError
                raise ToolError(
                    f"Access denied: {tool_name} requires one of {required_roles}"
                )
        
        return await call_next(context)


# Apply middleware
mcp.add_middleware(RequestLoggingMiddleware())
mcp.add_middleware(RBACMiddleware({
    "manage_collection": {"admin"},
    "index_document": {"admin", "teacher"},
    "delete_document": {"admin"},
    "get_usage_stats": {"admin", "teacher"},
    # search_content has no restrictions
}))
```

### Built-in Middleware (FastMCP 2.9+)
```python
from fastmcp.server.middleware.logging import StructuredLoggingMiddleware
from fastmcp.server.middleware.timing import TimingMiddleware
from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware

mcp.add_middleware(ErrorHandlingMiddleware(include_traceback=False))
mcp.add_middleware(TimingMiddleware())
mcp.add_middleware(StructuredLoggingMiddleware())
```

### Authentication Extraction Middleware
```python
from fastmcp.server.dependencies import get_http_headers
import jwt

class JWTUserContextMiddleware(Middleware):
    """Extract user info from JWT and populate session state."""
    
    async def on_request(self, context: MiddlewareContext, call_next):
        headers = get_http_headers() or {}
        auth_header = headers.get("authorization", "")
        
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                # Token already validated by auth middleware
                # Just extract claims
                claims = jwt.decode(token, options={"verify_signature": False})
                
                if context.fastmcp_context:
                    context.fastmcp_context.set_state("user_id", claims.get("sub"))
                    context.fastmcp_context.set_state("user_email", claims.get("email"))
                    context.fastmcp_context.set_state("user_role", 
                        claims.get("role", "student"))
                    context.fastmcp_context.set_state("user_scopes", 
                        set(claims.get("scope", "").split()))
            except Exception:
                pass  # Invalid token handled by auth middleware
        
        return await call_next(context)
```

---

## 10. Tags and Visibility

### Organizing with Tags
```python
# Server-level tags
mcp = FastMCP(name="LeoWiki", tags={"educational", "htl-leonding"})

# Tool tags
@mcp.tool(tags={"search", "read-only", "student"})
async def search_content(query: str): pass

@mcp.tool(tags={"admin", "write", "dangerous"})
async def delete_all_content(): pass

# Resource tags
@mcp.resource("leowiki://stats", tags={"metadata", "public"})
def get_stats(): pass

# Prompt tags
@mcp.prompt(tags={"tutoring", "german"})
def explain_topic(topic: str): pass
```

### Dynamic Visibility Control
```python
# Enable/disable tools dynamically
mcp.disable("delete_all_content")  # Hide from clients

# Later...
mcp.enable("delete_all_content")   # Show again

# Filter by tags
mcp.disable(tag="dangerous")       # Hide all dangerous tools
mcp.enable(tag="dangerous")        # Show them again
```

---

## 11. Lifespan and Dependency Injection

### Complete Lifespan Pattern
```python
from contextlib import asynccontextmanager
from dataclasses import dataclass
from collections.abc import AsyncIterator
from qdrant_client import AsyncQdrantClient

@dataclass
class AppContext:
    """Type-safe container for all injected dependencies."""
    qdrant: AsyncQdrantClient
    embedding_service: EmbeddingService
    config: ServerConfig
    cache: dict  # Simple in-memory cache

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """
    Initialize resources at startup, cleanup at shutdown.
    
    This runs ONCE when the server starts, not per-request.
    """
    logger.info("Starting server initialization...")
    
    # Initialize Qdrant client
    qdrant = AsyncQdrantClient(
        url=config.vector_db_url,
        api_key=config.vector_db_api_key,
        timeout=30
    )
    
    # Initialize embedding service
    embedding_service = EmbeddingService(
        api_key=config.openai_api_key,
        model=config.embedding_model
    )
    
    # Load configuration
    server_config = ServerConfig()
    
    # Create cache
    cache = {}
    
    logger.info("✓ All dependencies initialized")
    
    try:
        yield AppContext(
            qdrant=qdrant,
            embedding_service=embedding_service,
            config=server_config,
            cache=cache
        )
    finally:
        # Cleanup on shutdown
        logger.info("Shutting down...")
        await qdrant.close()
        logger.info("✓ Cleanup complete")


# Use in server
mcp = FastMCP(
    name="LeoWiki MCP",
    lifespan=app_lifespan
)

# Access in tools
@mcp.tool
async def search_content(query: str, ctx: Context) -> dict:
    app: AppContext = ctx.lifespan_context
    
    # Use injected dependencies
    embedding = app.embedding_service.embed_query(query)
    results = await app.qdrant.search(
        collection_name=app.config.default_collection,
        query_vector=embedding,
        limit=10
    )
    return format_results(results)
```

---

## 12. Testing with FastMCP Client

### In-Memory Testing
```python
import pytest
from fastmcp import FastMCP, Client

# Your server
mcp = FastMCP(name="TestServer")

@mcp.tool
async def add(a: int, b: int) -> int:
    return a + b

@pytest.fixture
async def client():
    """Fixture providing connected MCP client."""
    async with Client(mcp) as c:  # Direct connection, no network!
        yield c

async def test_add_tool(client):
    """Test the add tool."""
    result = await client.call_tool("add", {"a": 5, "b": 3})
    assert result.content[0].text == "8"

async def test_list_tools(client):
    """Test tool listing."""
    tools = await client.list_tools()
    tool_names = [t.name for t in tools]
    assert "add" in tool_names
```

### Testing with Context
```python
async def test_search_with_context(client):
    """Test search tool that uses context."""
    # The client handles context injection automatically
    result = await client.call_tool(
        "search_content",
        {"query": "Java Grundlagen", "limit": 5}
    )
    
    data = json.loads(result.content[0].text)
    assert "results" in data
    assert len(data["results"]) <= 5
```

### Testing Resources
```python
async def test_resource_access(client):
    """Test reading a resource."""
    result = await client.read_resource("leowiki://categories")
    categories = json.loads(result.content)
    
    assert isinstance(categories, list)
    assert len(categories) > 0
```

### Testing Prompts
```python
async def test_prompt_generation(client):
    """Test prompt template."""
    prompts = await client.list_prompts()
    assert "explain_topic" in [p.name for p in prompts]
    
    result = await client.get_prompt(
        "explain_topic",
        arguments={"topic": "OOP", "difficulty": "beginner"}
    )
    
    assert "OOP" in result.messages[0].content.text
```

---

## 13. Implementation Recommendations for LeoWiki

Based on your current codebase, here are prioritized recommendations:

### High Priority (Immediate Impact)

1. **Add Resources for Static Data**
```python
# Categories, stats, schema info - things LLMs need for context
@mcp.resource("leowiki://categories")
@mcp.resource("leowiki://stats")
@mcp.resource("leowiki://schema")
```

2. **Add Educational Prompts**
```python
# Help students formulate better queries
@mcp.prompt("explain_topic")
@mcp.prompt("create_quiz")
@mcp.prompt("compare_concepts")
```

3. **Implement Full Context Features**
```python
# Progress reporting for searches
# Logging for debugging
# Resource access within tools
```

4. **Add Tool Annotations**
```python
# Mark search_content as readOnlyHint=True
# Improves client caching and UX
```

### Medium Priority (Professional Polish)

5. **Add Middleware for RBAC**
```python
# Move role checking from tools to middleware
# Cleaner separation of concerns
```

6. **Implement Proper Error Handling**
```python
# mask_error_details=True
# Custom ToolError messages
```

7. **Add Tags for Organization**
```python
# Tags help with filtering and documentation
```

### Lower Priority (Advanced Features)

8. **Server Composition**
```python
# Split into search_mcp, admin_mcp, analytics_mcp
# Mount into main server
```

9. **Image Support**
```python
# Return diagrams, charts, logos
```

10. **Caching Middleware**
```python
# Cache expensive Qdrant searches
```

---

## Quick Reference Card

```
# Server
mcp = FastMCP(name, instructions, stateless_http, mask_error_details, lifespan, tags)

# Tools
@mcp.tool(name, description, annotations, tags)
async def my_tool(param: str, ctx: Context) -> dict

# Resources
@mcp.resource(uri, name, description, mime_type, tags)
def my_resource() -> str

@mcp.resource("proto://{param}")  # Template
def my_template(param: str) -> str

# Prompts
@mcp.prompt(name, description, tags)
def my_prompt(topic: str) -> str | list[Message]

# Context API
await ctx.info/debug/warning/error("message")
await ctx.report_progress(current, total, message)
await ctx.read_resource("uri")
await ctx.sample("prompt for LLM")
ctx.get_state("key") / ctx.set_state("key", value)
ctx.lifespan_context  # Access injected dependencies

# Composition
main.mount(sub_server, prefix="sub")
await main.import_server(sub_server, prefix="sub")

# Middleware
mcp.add_middleware(MyMiddleware())

# Visibility
mcp.enable("tool_name") / mcp.disable("tool_name")
mcp.enable(tag="tag") / mcp.disable(tag="tag")

# Running
mcp.run(transport="http", host="0.0.0.0", port=8000)
```

---

*Document Version: 1.0 | FastMCP v2.13.x | January 2026*
