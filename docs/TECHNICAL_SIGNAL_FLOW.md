# LeoWiki MCP Server - Technischer Signalfluss

**Zielgruppe:** Entwickler, die den Server verstehen, erweitern oder warten müssen.

---

## Inhaltsverzeichnis

1. [Architekturübersicht](#1-architekturübersicht)
2. [Request-Lifecycle: Vom Client zur Antwort](#2-request-lifecycle-vom-client-zur-antwort)
3. [Authentifizierung (OAuth 2.1)](#3-authentifizierung-oauth-21)
4. [Middleware-Kette](#4-middleware-kette)
5. [RBAC (Role-Based Access Control)](#5-rbac-role-based-access-control)
6. [Tools im Detail](#6-tools-im-detail)
7. [Resources und Prompts](#7-resources-und-prompts)
8. [Query Logging](#8-query-logging)
9. [Dependency Injection (Lifespan)](#9-dependency-injection-lifespan)
10. [Konfiguration](#10-konfiguration)
11. [Code-Referenz nach Funktion](#11-code-referenz-nach-funktion)

---

## 1. Architekturübersicht

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INTERNET                                        │
│                     https://leowiki-mcp.stream                               │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ Port 443 (HTTPS)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           mcp-caddy (Reverse Proxy)                          │
│  • TLS Terminierung (Let's Encrypt)                                         │
│  • HTTP/2, HTTP/3 Support                                                   │
│  • Security Headers (HSTS, X-Frame-Options, etc.)                           │
│  Datei: Caddyfile                                                           │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ Port 8000 (HTTP intern)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Application (app)                             │
│  Datei: main.py                                                             │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │            ScalekitAuthMiddleware (HTTP-Level)                       │   │
│  │  • JWT Token Validation via Scalekit SDK                            │   │
│  │  • WWW-Authenticate Header für OAuth 2.1                            │   │
│  │  Datei: src/middleware/scalekit_auth.py                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     FastMCP Application (mcp)                        │   │
│  │  Gemountet auf "/" → Handelt /mcp Pfad                              │   │
│  │                                                                      │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │  Middleware-Kette (in Reihenfolge):                           │  │   │
│  │  │  1. RequestLoggingMiddleware  → Correlation IDs, Timing       │  │   │
│  │  │  2. UserContextMiddleware     → JWT Claims → Context          │  │   │
│  │  │  3. RBACEnforcementMiddleware → Tool-Filterung & Zugriff      │  │   │
│  │  │  4. AuditLoggingMiddleware    → DSGVO-konformes Logging       │  │   │
│  │  │  Datei: src/middleware/mcp_middleware.py                      │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  │                                    │                                 │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │                      Tool Handler                              │  │   │
│  │  │  • search_content_student                                     │  │   │
│  │  │  • search_content_teacher                                     │  │   │
│  │  │  • get_collection_stats                                       │  │   │
│  │  │  • get_query_statistics                                       │  │   │
│  │  │  • health_check                                               │  │   │
│  │  │  Datei: src/tools/search_tools.py, main.py                    │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ Port 6333 (HTTP intern)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            mcp-qdrant (Vector DB)                            │
│  • ~3400 Dokumente mit Embeddings (3072 Dimensionen)                        │
│  • Cosine Similarity Search                                                  │
│  Datei: src/backends/qdrant.py                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Request-Lifecycle: Vom Client zur Antwort

### Beispiel: Student führt Suche aus

```
Claude Desktop/Web App
        │
        │ POST /mcp
        │ Headers: Authorization: Bearer <JWT>
        │ Body: {"method": "tools/call", "params": {"name": "search_content_student", ...}}
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ 1. CADDY (Caddyfile)                                                          │
│    • TLS terminieren                                                          │
│    • Request an localhost:8000 weiterleiten                                   │
└───────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ 2. ScalekitAuthMiddleware (src/middleware/scalekit_auth.py:68)                │
│                                                                                │
│    async def __call__(self, request: Request, call_next):                     │
│        # Prüft ob /mcp ein Public Endpoint ist → NEIN                         │
│        if self._is_public_endpoint(request.url.path):                         │
│            return await call_next(request)                                    │
│                                                                                │
│        # Extrahiert Bearer Token aus Authorization Header                     │
│        token = auth_header.split("Bearer ", 1)[1].strip()                     │
│                                                                                │
│        # Validiert Token mit Scalekit SDK                                     │
│        is_valid = self.scalekit_client.validate_access_token(token, options)  │
│                                                                                │
│        # Bei Erfolg: Weiter zum nächsten Handler                              │
│        return await call_next(request)                                        │
│                                                                                │
│    KLASSEN:                                                                    │
│    - ScalekitClient (scalekit SDK)                                            │
│    - TokenValidationOptions (scalekit SDK)                                    │
└───────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ 3. FastMCP Protocol Handler (mcp_app, main.py:234)                            │
│                                                                                │
│    mcp_app = mcp.http_app(path="/mcp")                                        │
│    app.mount("/", mcp_app)                                                    │
│                                                                                │
│    # FastMCP parst MCP JSON-RPC Request                                       │
│    # Ruft registrierte Middleware-Kette auf                                   │
└───────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ 4. RequestLoggingMiddleware (src/middleware/mcp_middleware.py:26)             │
│                                                                                │
│    async def on_request(self, context: MiddlewareContext, call_next):         │
│        request_id = str(uuid.uuid4())[:8]  # z.B. "a1b2c3d4"                  │
│        start_time = time.time()                                               │
│                                                                                │
│        # Speichert request_id im FastMCP Context                              │
│        await context.fastmcp_context.set_state("request_id", request_id)      │
│                                                                                │
│        logger.info(f"[{request_id}] → tools/call")                            │
│                                                                                │
│        result = await call_next(context)  # Weiter zur nächsten Middleware    │
│                                                                                │
│        duration_ms = (time.time() - start_time) * 1000                        │
│        logger.info(f"[{request_id}] ✓ completed in {duration_ms:.1f}ms")      │
│                                                                                │
│        return result                                                          │
└───────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ 5. UserContextMiddleware (src/middleware/mcp_middleware.py:83)                │
│                                                                                │
│    async def on_request(self, context: MiddlewareContext, call_next):         │
│        headers = get_http_headers()                                           │
│        auth_header = headers.get("authorization", "")                         │
│                                                                                │
│        # JWT dekodieren (ohne Signatur-Verifikation, da bereits validiert)    │
│        claims = jwt.decode(token, options={"verify_signature": False})        │
│                                                                                │
│        # Rolle aus JWT extrahieren (mehrere Claim-Namen werden geprüft)       │
│        user_role = (                                                          │
│            claims.get("role") or                                              │
│            claims.get("roles") or                                             │
│            claims.get("groups") → "admin"/"teacher" check                     │
│            "student"  # Default                                               │
│        )                                                                       │
│                                                                                │
│        # User-Daten in FastMCP Context speichern                              │
│        await context.fastmcp_context.set_state("user_id", user_id)            │
│        await context.fastmcp_context.set_state("user_email", user_email)      │
│        await context.fastmcp_context.set_state("user_role", user_role)        │
│        await context.fastmcp_context.set_state("user_scopes", user_scopes)    │
│                                                                                │
│        return await call_next(context)                                        │
└───────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ 6. RBACEnforcementMiddleware (src/middleware/mcp_middleware.py:187)           │
│                                                                                │
│    TOOL_PERMISSIONS = {                                                       │
│        "search_content_student": {"student", "teacher", "admin"},             │
│        "search_content_teacher": {"teacher", "admin"},                        │
│        "get_collection_stats": {"admin"},                                     │
│        "get_query_statistics": {"admin"},                                     │
│        "list_resources": {"admin"},                                           │
│        "read_resource": {"admin"},                                            │
│        # health_check, list_prompts, get_prompt → nicht gelistet = alle       │
│    }                                                                           │
│                                                                                │
│    async def on_call_tool(self, context: MiddlewareContext, call_next):       │
│        tool_name = context.message.name  # "search_content_student"           │
│        required_roles = self.TOOL_PERMISSIONS.get(tool_name, set())           │
│                                                                                │
│        user_role = await context.fastmcp_context.get_state("user_role")       │
│                                                                                │
│        if user_role not in required_roles:                                    │
│            raise ToolError(f"Access denied...")  # HTTP 403                   │
│                                                                                │
│        return await call_next(context)  # Weiter zum Tool                     │
└───────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ 7. AuditLoggingMiddleware (src/middleware/mcp_middleware.py:312)              │
│                                                                                │
│    async def on_call_tool(self, context: MiddlewareContext, call_next):       │
│        user_id_hash = hash(user_id)  # Pseudonymisierung für DSGVO            │
│                                                                                │
│        result = await call_next(context)  # Tool ausführen                    │
│                                                                                │
│        logger.info(f"[AUDIT] tool={tool_name}, user={user_id_hash}, ...")     │
│        return result                                                          │
└───────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ 8. Tool: search_content_student (src/tools/search_tools.py:185)               │
│                                                                                │
│    @mcp.tool(name="search_content_student", ...)                              │
│    async def search_content_student(query: str, limit: int, ctx: Context):    │
│                                                                                │
│        # 8a. Services initialisieren (lazy, thread-safe)                      │
│        db, embedding_service = _get_services()                                │
│                                                                                │
│        # 8b. Embedding generieren                                             │
│        await ctx.report_progress(1, 4, "Generiere Embedding...")              │
│        query_embedding = embedding_service.embed_query(query)                 │
│        # → OpenAI API Call: text-embedding-3-large                            │
│                                                                                │
│        # 8c. Qdrant-Suche mit RBAC-Filter                                     │
│        await ctx.report_progress(3, 4, "Durchsuche Wissensdatenbank...")      │
│        raw_results = db.search(                                               │
│            query_vector=query_embedding,                                      │
│            collection="educational_content",                                  │
│            limit=fetch_limit                                                  │
│        )                                                                       │
│                                                                                │
│        # 8d. RBAC: Teacher-Content herausfiltern                              │
│        for result in raw_results:                                             │
│            source = result.payload.get("source", "")                          │
│            if source.startswith("teacher:") or source.startswith("class:"):   │
│                continue  # NICHT für Schüler sichtbar                         │
│            results.append(result)                                             │
│                                                                                │
│        # 8e. Ergebnisse formatieren                                           │
│        formatted = _format_search_results(results, query)                     │
│                                                                                │
│        # 8f. Query Logging (für Statistiken)                                  │
│        query_logger = get_query_logger()                                      │
│        query_logger.log_query(query, formatted, user_role, "search_...", ...) │
│                                                                                │
│        return {"content": [{"type": "text", "text": formatted}]}              │
└───────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ 9. Response zurück durch die Middleware-Kette                                 │
│                                                                                │
│    AuditLoggingMiddleware ← loggt Erfolg                                      │
│    RBACEnforcementMiddleware ← durchreichen                                   │
│    UserContextMiddleware ← durchreichen                                       │
│    RequestLoggingMiddleware ← loggt Duration                                  │
│    FastMCP ← JSON-RPC Response formatieren                                    │
│    FastAPI ← HTTP Response                                                    │
│    Caddy ← TLS verschlüsseln                                                  │
└───────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
    Client erhält Antwort
```

---

## 3. Authentifizierung (OAuth 2.1)

### Architektur

```
┌──────────────────┐         ┌─────────────────┐
│  Claude Desktop  │◄────────│  Scalekit Auth  │
│  (OAuth Client)  │  tokens │   Server        │
└────────┬─────────┘         └─────────────────┘
         │ Bearer Token
         ▼
┌──────────────────┐
│   MCP Server     │ ← Protected Resource
│ (validates JWT)  │
└──────────────────┘
```

### Code-Locations

| Komponente | Datei | Zeile |
|------------|-------|-------|
| Auth Middleware Klasse | `src/middleware/scalekit_auth.py` | 26 |
| Token-Validierung | `src/middleware/scalekit_auth.py` | 124-145 |
| Public Endpoints | `src/middleware/scalekit_auth.py` | 169-195 |
| OAuth Discovery | `main.py` | 304-343 |
| Scalekit Config | `src/config/server_config.py` | 193-228 |

### JWT Claims Extraktion

```python
# src/middleware/mcp_middleware.py:133-164
user_role = (
    claims.get("role") or           # Einzelner String
    claims.get("roles") or          # Array
    claims.get("user_role") or      # Alternative
    claims.get("custom:role") or    # Custom Claim
    "student"                       # Default
)

# Zusätzlich: groups Claim prüfen
groups = claims.get("groups", [])
if "admin" in groups:
    user_role = "admin"
elif "teacher" in groups:
    user_role = "teacher"
```

### Neue Rolle hinzufügen

1. **JWT muss Rolle enthalten** (Scalekit Dashboard konfigurieren)
2. **`UserContextMiddleware` erweitern** (Zeile ~150):
   ```python
   elif "direktor" in groups:
       user_role = "direktor"
   ```
3. **`TOOL_PERMISSIONS` erweitern** (Zeile ~210):
   ```python
   "get_collection_stats": {"direktor", "admin"},
   ```

---

## 4. Middleware-Kette

### Ausführungsreihenfolge

```python
# main.py:160-163
mcp.add_middleware(RequestLoggingMiddleware())    # 1. Zuerst
mcp.add_middleware(UserContextMiddleware())       # 2. 
mcp.add_middleware(RBACEnforcementMiddleware())   # 3.
mcp.add_middleware(AuditLoggingMiddleware())      # 4. Zuletzt (vor Tool)
```

### Middleware-Hooks

| Hook | Wann | Middleware |
|------|------|------------|
| `on_request` | Jeder MCP Request | RequestLogging, UserContext |
| `on_list_tools` | `tools/list` | RBACEnforcement (filtert Liste) |
| `on_call_tool` | `tools/call` | RBACEnforcement, AuditLogging |

### Context State

```python
# Schreiben (in UserContextMiddleware):
await context.fastmcp_context.set_state("user_role", "teacher")

# Lesen (in RBACEnforcementMiddleware oder Tools):
user_role = await context.fastmcp_context.get_state("user_role")
```

**Verfügbare State Keys:**
- `request_id` - Correlation ID (8 Zeichen)
- `user_id` - JWT `sub` Claim
- `user_email` - JWT `email` Claim
- `user_role` - Extrahierte Rolle (student/teacher/admin)
- `user_scopes` - Set von Scopes aus JWT

---

## 5. RBAC (Role-Based Access Control)

### Berechtigungsmatrix

```python
# src/middleware/mcp_middleware.py:210-228
TOOL_PERMISSIONS = {
    # Tool-Name                    # Erlaubte Rollen
    "search_content_student":      {"student", "teacher", "admin"},
    "search_content_teacher":      {"teacher", "admin"},
    "get_collection_stats":        {"admin"},
    "get_query_statistics":        {"admin"},
    "list_resources":              {"admin"},
    "read_resource":               {"admin"},
    # Nicht gelistet = für ALLE
}
```

### Tool-Filterung (on_list_tools)

```python
# src/middleware/mcp_middleware.py:230-273
async def on_list_tools(self, context, call_next):
    all_tools = await call_next(context)  # Alle Tools holen
    user_role = await context.fastmcp_context.get_state("user_role")
    
    filtered_tools = []
    for tool in all_tools:
        required_roles = self.TOOL_PERMISSIONS.get(tool.name, set())
        
        # Kein Eintrag = für alle sichtbar
        if not required_roles:
            filtered_tools.append(tool)
            continue
        
        # User hat passende Rolle?
        if user_role in required_roles:
            filtered_tools.append(tool)
    
    return filtered_tools
```

### Content-Filterung (in Tools)

```python
# src/tools/search_tools.py:296-307
for result in raw_results:
    source = result.payload.get("source", "")
    
    # Schüler sehen KEINE teacher: oder class: URLs
    if source.startswith("teacher:") or source.startswith("class:"):
        continue  # Überspringen
    
    results.append(result)
```

### Sichtbarkeit ändern

**Datei:** `src/middleware/mcp_middleware.py`, Zeile 210

```python
# Vorher: Stats nur für Admin
"get_collection_stats": {"admin"},

# Nachher: Stats auch für Lehrer
"get_collection_stats": {"teacher", "admin"},
```

---

## 6. Tools im Detail

### Tool-Registrierung

```python
# src/tools/search_tools.py:160-172
def register_search_tools(mcp: FastMCP) -> None:
    @mcp.tool(
        name="search_content_student",
        description="Search educational content with student-level access",
        annotations=ToolAnnotations(
            title="LeoWiki Student Search",
            readOnlyHint=True,      # Keine Seiteneffekte
            idempotentHint=True,    # Idempotent
            openWorldHint=False,    # Bekannter Datensatz
        ),
        tags={"search", "read-only", "student"}
    )
    async def search_content_student(query: str, limit: int = 10, ctx: Context = None):
        ...
```

### Tool-Übersicht

| Tool | Datei | Zeile | RBAC |
|------|-------|-------|------|
| `search_content_student` | `search_tools.py` | 174 | student, teacher, admin |
| `search_content_teacher` | `search_tools.py` | 385 | teacher, admin |
| `get_collection_stats` | `search_tools.py` | 554 | admin |
| `get_query_statistics` | `search_tools.py` | 683 | admin |
| `health_check` | `main.py` | 209 | alle |

### Lazy Service Initialization

```python
# src/tools/search_tools.py:34-76
_db: Optional[QdrantBackend] = None
_embedding_service: Optional[EmbeddingService] = None
_init_lock = threading.Lock()

def _get_services():
    global _db, _embedding_service
    
    # Fast Path: Bereits initialisiert
    if _db is not None and _embedding_service is not None:
        return _db, _embedding_service
    
    # Slow Path: Mit Lock initialisieren (thread-safe)
    with _init_lock:
        if _db is None:
            _db = create_vector_backend(...)
        if _embedding_service is None:
            _embedding_service = EmbeddingService(...)
    
    return _db, _embedding_service
```

### Progress Reporting

```python
# In Tool-Funktion:
await ctx.report_progress(0, 4, "Analysiere Suchanfrage...")
await ctx.report_progress(1, 4, "Generiere Embedding...")
await ctx.report_progress(2, 4, "Wende Zugriffs-Filter an...")
await ctx.report_progress(3, 4, "Durchsuche Wissensdatenbank...")
```

---

## 7. Resources und Prompts

### Resources (Admin-Only)

```python
# src/resources/metadata.py - Statische Resources
@mcp.resource(uri="leowiki://categories", name="Content Categories", ...)
@mcp.resource(uri="leowiki://access-levels", name="Access Level Documentation", ...)
@mcp.resource(uri="leowiki://search-hints", name="Search Tips", ...)
@mcp.resource(uri="leowiki://system-prompt", name="Assistant Behavior Guidelines", ...)

# src/resources/content.py - Dynamische Resources
@mcp.resource(uri="leowiki://stats", name="Collection Statistics", ...)
@mcp.resource(uri="leowiki://recent/{count}", name="Recent Updates", ...)
```

### Prompts (Alle Rollen)

```python
# src/prompts/educational.py
@mcp.prompt(name="explain_topic", description="Generate a structured explanation", ...)
@mcp.prompt(name="summarize_search", description="Summarize search results", ...)
```

### FastMCP 3.0 Transforms

```python
# main.py:198-201
from fastmcp.server.transforms import ResourcesAsTools, PromptsAsTools

mcp.add_transform(ResourcesAsTools(mcp))  # Resources als Tools exponieren
mcp.add_transform(PromptsAsTools(mcp))    # Prompts als Tools exponieren
```

**Warum?** Claude Desktop (Remote-Server) unterstützt primär Tools. Die Transforms machen Resources/Prompts als Tools aufrufbar (`list_resources`, `read_resource`, `list_prompts`, `get_prompt`).

---

## 8. Query Logging

### Architektur

```
Tool-Aufruf → QueryLogger.log_query() → data/statistics/queries.jsonl
```

### Code-Locations

| Komponente | Datei | Zeile |
|------------|-------|-------|
| QueryLogger Klasse | `src/utils/query_logger.py` | 28 |
| Singleton Getter | `src/utils/query_logger.py` | 145 |
| Integration in search_content_student | `src/tools/search_tools.py` | 337-349 |
| Integration in search_content_teacher | `src/tools/search_tools.py` | 506-518 |
| get_query_statistics Tool | `src/tools/search_tools.py` | 683 |

### Log-Format (JSONL)

```json
{
  "timestamp": "2026-02-05T10:30:00.123456",
  "query": "Was ist OOP?",
  "response_preview": "OOP steht für...",
  "response_length": 1234,
  "user_role": "student",
  "tool_name": "search_content_student",
  "result_count": 5,
  "user_id_hash": "1234567890",
  "request_id": "a1b2c3d4",
  "duration_ms": null
}
```

### Thread-Safety

```python
# src/utils/query_logger.py:15
_write_lock = threading.Lock()

def _write_entry(self, entry: dict):
    with _write_lock:
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
```

---

## 9. Dependency Injection (Lifespan)

### AppContext Klasse

```python
# src/server/lifespan.py:30-46
@dataclass
class AppContext:
    qdrant: QdrantBackend           # Vektor-DB Connection
    embedding_service: EmbeddingService  # OpenAI API
    config: ServerConfig            # Konfiguration
    cache: dict                     # In-Memory Cache
```

### Lifespan Context Manager

```python
# src/server/lifespan.py:48-145
@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    # STARTUP
    qdrant = QdrantBackend(url=config.vector_db_url, ...)
    embedding_service = EmbeddingService(api_key=config.openai_api_key, ...)
    cache = {}
    
    try:
        yield AppContext(qdrant, embedding_service, config, cache)
    finally:
        # SHUTDOWN
        cache.clear()
        logger.info("Cleanup complete")
```

### Verwendung in Tools

```python
# In Tool via ctx.request_context.lifespan_context
# ABER: Wir nutzen lazy initialization stattdessen (search_tools.py:40)
```

---

## 10. Konfiguration

### ServerConfig Klasse

**Datei:** `src/config/server_config.py`

```python
class ServerConfig(BaseSettings):
    # Transport
    transport: Literal["stdio", "http", "both"] = "stdio"
    
    # HTTP
    http_host: str = "0.0.0.0"
    http_port: int = 8000
    
    # Qdrant
    vector_db_url: str = "http://localhost:6334"
    default_collection: str = "educational_content"
    
    # Embeddings
    openai_api_key: str | None = None
    embedding_model: str = "text-embedding-3-large"
    vector_dimensions: int = 3072
    
    # Auth
    enable_auth: bool = True
    scalekit_env_url: str | None = None
    scalekit_client_id: str | None = None
    scalekit_client_secret: str | None = None
    
    # RBAC
    enable_rbac: bool = True
    default_user_role: str = "student"
    
    model_config = SettingsConfigDict(env_file=".env", ...)
```

### Environment Variables

```bash
# .env
OPENAI_API_KEY=sk-...
VECTOR_DB_URL=http://qdrant:6333
ENABLE_AUTH=true
SCALEKIT_ENV_URL=https://...
SCALEKIT_CLIENT_ID=...
SCALEKIT_CLIENT_SECRET=...
```

---

## 11. Code-Referenz nach Funktion

### Authentifizierung

| Funktion | Datei | Zeile |
|----------|-------|-------|
| JWT Validierung | `src/middleware/scalekit_auth.py` | 124 |
| Public Endpoints | `src/middleware/scalekit_auth.py` | 169 |
| OAuth Discovery | `main.py` | 304 |
| JWT Claims Extraktion | `src/middleware/mcp_middleware.py` | 117 |

### RBAC

| Funktion | Datei | Zeile |
|----------|-------|-------|
| TOOL_PERMISSIONS | `src/middleware/mcp_middleware.py` | 210 |
| Tool-Filterung | `src/middleware/mcp_middleware.py` | 230 |
| Zugriffsprüfung | `src/middleware/mcp_middleware.py` | 275 |
| Content-Filterung | `src/tools/search_tools.py` | 296 |

### Tools

| Funktion | Datei | Zeile |
|----------|-------|-------|
| Tool-Registrierung | `src/tools/search_tools.py` | 160 |
| Student Search | `src/tools/search_tools.py` | 185 |
| Teacher Search | `src/tools/search_tools.py` | 385 |
| Collection Stats | `src/tools/search_tools.py` | 554 |
| Query Statistics | `src/tools/search_tools.py` | 683 |
| Health Check | `main.py` | 209 |

### Services

| Funktion | Datei | Zeile |
|----------|-------|-------|
| Lazy Init | `src/tools/search_tools.py` | 40 |
| Qdrant Backend | `src/backends/qdrant.py` | - |
| Embedding Service | `src/utils/embeddings.py` | - |
| Query Logger | `src/utils/query_logger.py` | 28 |

### Konfiguration

| Funktion | Datei | Zeile |
|----------|-------|-------|
| ServerConfig | `src/config/server_config.py` | 20 |
| Lifespan | `src/server/lifespan.py` | 48 |
| App Setup | `main.py` | 96 |

---

## Anhang: Fehlerbehandlung

### Sicherheitsregel

**Niemals Implementierungsdetails nach außen geben!**

```python
# FALSCH:
return {"error": f"QdrantException: {str(e)}"}

# RICHTIG:
logger.error(f"Qdrant error: {e}", exc_info=True)  # Server-seitig loggen
return {"error": "Es ist ein Fehler aufgetreten. Bitte erneut versuchen."}
```

### Betroffene Stellen

| Datei | Zeile | Beschreibung |
|-------|-------|--------------|
| `search_tools.py` | 372-382 | Student Search |
| `search_tools.py` | 541-551 | Teacher Search |
| `search_tools.py` | 671-679 | Collection Stats |
| `qdrant.py` | 110-117 | Health Check |
| `oauth_flow.py` | 198-202 | Token Exchange |
| `content.py` | 73-78 | Stats Resource |

---

**Dokument Version:** 1.0  
**Erstellt:** 2026-02-05  
**Server Version:** 2.1.0
