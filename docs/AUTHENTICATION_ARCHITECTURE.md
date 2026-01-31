# Authentication Architecture - Controller vs. Middleware Pattern

**Projekt:** LeoWiki MCP Educational Server  
**Datum:** 31. Januar 2026  
**Autor:** Imre (HTL Diploma Thesis)

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Klassisches Controller-Pattern](#klassisches-controller-pattern)
3. [Modernes Middleware-Pattern](#modernes-middleware-pattern)
4. [Detaillierte Architektur-Diagramme](#detaillierte-architektur-diagramme)
5. [Code-Beispiele im Vergleich](#code-beispiele-im-vergleich)
6. [Die 3 Schichten im Detail](#die-3-schichten-im-detail)
7. [Vorteile & Nachteile](#vorteile--nachteile)
8. [Best Practices](#best-practices)
9. [Integration in diesem Projekt](#integration-in-diesem-projekt)

---

## Übersicht

### Die zentrale Frage

**"Wie wird Authentication in einem MCP-Server umgesetzt, wenn es keinen klassischen Controller gibt?"**

### Die Antwort

Statt **expliziter Auth-Checks in jedem Controller** nutzen wir **Middleware**, die **automatisch** vor allen geschützten Endpoints läuft. Das ist:
- ✅ **Sicherer** (kann nicht vergessen werden)
- ✅ **Wartbarer** (DRY - Don't Repeat Yourself)
- ✅ **Testbarer** (zentrale Test-Suite)
- ✅ **Professioneller** (Industry Standard)

---

## Klassisches Controller-Pattern

### Architektur-Diagramm

```
┌─────────────────────────────────────────────────────────────────┐
│              KLASSISCHES CONTROLLER-PATTERN                      │
│              (z.B. Spring Boot, Express.js)                      │
└─────────────────────────────────────────────────────────────────┘

                           HTTP Request
                     (GET /api/search?q=Java)
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Web Server          │
                    │   (Tomcat, Node.js)   │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Routing Layer        │
                    │  /api/search → ...    │
                    └───────────┬───────────┘
                                │
                                ▼
╔═══════════════════════════════════════════════════════════════╗
║                      CONTROLLER                                ║
║  (SearchController.java / search.controller.ts)                ║
╠═══════════════════════════════════════════════════════════════╣
║                                                                ║
║  public SearchResponse search(                                 ║
║      @RequestHeader("Authorization") String token,             ║
║      @RequestParam String query                                ║
║  ) {                                                           ║
║      // ❶ AUTH CHECK (manuell in JEDEM Controller!)          ║
║      User user = authService.validateToken(token);            ║
║      if (user == null) {                                      ║
║          throw new UnauthorizedException();  ← 401             ║
║      }                                                         ║
║                                                                ║
║      // ❷ RBAC CHECK (manuell!)                              ║
║      if (!user.hasRole("STUDENT")) {                          ║
║          throw new ForbiddenException();     ← 403             ║
║      }                                                         ║
║                                                                ║
║      // ❸ BUSINESS LOGIC                                     ║
║      return searchService.search(query, user.getRole());      ║
║  }                                                             ║
║                                                                ║
╚═══════════════════════════════════════════════════════════════╝
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Service Layer       │
                    │   (SearchService)     │
                    └───────────┬───────────┘
                                │
                                ▼
                            Database
```

### Probleme mit diesem Ansatz

#### ❌ Problem 1: Code-Duplikation

```java
// SearchController.java
@GetMapping("/search")
public SearchResponse search(@RequestHeader String token) {
    User user = authService.validateToken(token);  // ← Wiederholt
    if (user == null) throw new UnauthorizedException();
    // ...
}

// DocumentController.java
@GetMapping("/documents")
public Document getDocument(@RequestHeader String token) {
    User user = authService.validateToken(token);  // ← Wiederholt
    if (user == null) throw new UnauthorizedException();
    // ...
}

// StatsController.java
@GetMapping("/stats")
public Stats getStats(@RequestHeader String token) {
    User user = authService.validateToken(token);  // ← Wiederholt
    if (user == null) throw new UnauthorizedException();
    // ...
}
```

**Resultat:** Auth-Code in **JEDEM** Controller kopiert!

#### ❌ Problem 2: Fehleranfälligkeit

```java
// Entwickler vergisst Auth-Check!
@GetMapping("/admin/users")
public List<User> getAllUsers() {
    // 🚨 KEIN AUTH CHECK! 
    // 🚨 SECURITY VULNERABILITY!
    return userService.findAll();
}
```

**Resultat:** Ein vergessener Check = **Security Hole**!

#### ❌ Problem 3: Schwierig zu testen

```java
@Test
public void testSearch() {
    // Muss Auth mocken
    when(authService.validateToken(any())).thenReturn(testUser);
    
    // Muss Controller testen
    SearchResponse response = controller.search("Bearer token", "query");
    
    // Auth + Business Logic vermischt
}
```

**Resultat:** Tests sind kompliziert und langsam.

#### ❌ Problem 4: Inkonsistente Error Handling

```java
// Controller A
if (user == null) throw new UnauthorizedException();

// Controller B  
if (user == null) return ResponseEntity.status(401).build();

// Controller C
if (user == null) throw new AccessDeniedException();
```

**Resultat:** Inkonsistente API-Antworten!

---

## Modernes Middleware-Pattern

### Architektur-Diagramm

```
┌─────────────────────────────────────────────────────────────────┐
│               MODERNES MIDDLEWARE-PATTERN                        │
│               (FastAPI, Express.js, Spring WebFlux)              │
└─────────────────────────────────────────────────────────────────┘

                           HTTP Request
                 (POST /mcp + Authorization: Bearer xxx)
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Web Server          │
                    │   (Uvicorn/FastAPI)   │
                    └───────────┬───────────┘
                                │
                                ▼
╔═══════════════════════════════════════════════════════════════╗
║                    MIDDLEWARE CHAIN                            ║
║              (läuft AUTOMATISCH vor JEDEM Request)             ║
╠═══════════════════════════════════════════════════════════════╣
║                                                                ║
║  ┌────────────────────────────────────────────────┐          ║
║  │  ❶ ScalekitAuthMiddleware                     │          ║
║  │     (src/middleware/scalekit_auth.py)          │          ║
║  ├────────────────────────────────────────────────┤          ║
║  │  • Public Endpoints prüfen                     │          ║
║  │    (/health, /auth/login → durchlassen)        │          ║
║  │                                                 │          ║
║  │  • Bearer Token aus Header extrahieren         │          ║
║  │    Authorization: Bearer <token>               │          ║
║  │                                                 │          ║
║  │  • Token mit Scalekit SDK validieren           │          ║
║  │    scalekit_client.validate_access_token()     │          ║
║  │                                                 │          ║
║  │  • Bei Fehler: 401 + WWW-Authenticate          │          ║
║  │    → STOP (Request abgelehnt)                  │          ║
║  │                                                 │          ║
║  │  • Bei Erfolg: Request durchlassen ↓           │          ║
║  └────────────────────────────────────────────────┘          ║
║                          │ ✅ Token gültig                     ║
║                          ▼                                     ║
║  ┌────────────────────────────────────────────────┐          ║
║  │  ❷ RequestLoggingMiddleware (FastMCP)         │          ║
║  │     (src/middleware/mcp_middleware.py)         │          ║
║  ├────────────────────────────────────────────────┤          ║
║  │  • Correlation ID generieren                   │          ║
║  │  • Request-Start loggen                        │          ║
║  │  • Timing messen                               │          ║
║  └────────────────────────────────────────────────┘          ║
║                          │                                     ║
║                          ▼                                     ║
║  ┌────────────────────────────────────────────────┐          ║
║  │  ❸ UserContextMiddleware (FastMCP)            │          ║
║  │     (src/middleware/mcp_middleware.py)         │          ║
║  ├────────────────────────────────────────────────┤          ║
║  │  • JWT Claims aus Token extrahieren            │          ║
║  │    - user_id (sub)                             │          ║
║  │    - user_email                                │          ║
║  │    - user_role (student/teacher/admin)         │          ║
║  │                                                 │          ║
║  │  • In FastMCP Context schreiben                │          ║
║  │    ctx.set_state("user_role", role)            │          ║
║  └────────────────────────────────────────────────┘          ║
║                          │                                     ║
║                          ▼                                     ║
║  ┌────────────────────────────────────────────────┐          ║
║  │  ❹ RBACEnforcementMiddleware (FastMCP)        │          ║
║  │     (src/middleware/mcp_middleware.py)         │          ║
║  ├────────────────────────────────────────────────┤          ║
║  │  • Tool-Name aus Request holen                 │          ║
║  │  • Tool-Permissions prüfen                     │          ║
║  │    TOOL_PERMISSIONS = {                        │          ║
║  │      "get_collection_stats": {"teacher", ...}  │          ║
║  │    }                                            │          ║
║  │                                                 │          ║
║  │  • User-Role gegen Required-Roles prüfen       │          ║
║  │  • Bei Fehler: ToolError (Access Denied)       │          ║
║  └────────────────────────────────────────────────┘          ║
║                          │                                     ║
║                          ▼                                     ║
║  ┌────────────────────────────────────────────────┐          ║
║  │  ❺ AuditLoggingMiddleware (FastMCP)           │          ║
║  │     (src/middleware/mcp_middleware.py)         │          ║
║  ├────────────────────────────────────────────────┤          ║
║  │  • Tool-Invocation loggen (DSGVO-konform)      │          ║
║  │  • User-ID pseudonymisieren (hash)             │          ║
║  │  • Success/Failure tracken                     │          ║
║  └────────────────────────────────────────────────┘          ║
║                                                                ║
╚════════════════════════════╤═══════════════════════════════════╝
                             │ ✅ Alle Checks bestanden!
                             ▼
                ┌────────────────────────────┐
                │     MCP TOOL HANDLER       │
                │  (search_content_student)  │
                ├────────────────────────────┤
                │                            │
                │  async def search(...):    │
                │      # ✅ Auth bereits OK! │
                │      # ✅ User-Info da!    │
                │                            │
                │      role = ctx.get_state( │
                │          "user_role"       │
                │      )                     │
                │                            │
                │      # Nur Business Logic! │
                │      results = search(...)  │
                │      return results        │
                └────────────────────────────┘
```

### Vorteile auf einen Blick

#### ✅ Vorteil 1: DRY (Don't Repeat Yourself)

```python
# Auth-Code NUR EINMAL!
class ScalekitAuthMiddleware:
    async def __call__(self, request, call_next):
        # Token validieren
        is_valid = self.scalekit_client.validate_access_token(token)
        if not is_valid:
            return Response(status_code=401)
        return await call_next(request)

# Tools sind SAUBER - kein Auth-Code!
@mcp.tool()
async def search_content_student(query: str, ctx: Context):
    # Direkt Business Logic - Auth ist bereits erledigt!
    results = search(query)
    return results

@mcp.tool()
async def get_collection_stats(ctx: Context):
    # Auch hier: kein Auth-Code!
    stats = get_stats()
    return stats
```

#### ✅ Vorteil 2: Unmöglich zu vergessen

```python
# Middleware ist IMMER aktiv für ALLE Endpoints
# Ein Entwickler kann NICHT vergessen, Auth zu prüfen!

app.add_middleware(BaseHTTPMiddleware, dispatch=scalekit_auth_middleware)

# ↑ DIESE EINE ZEILE schützt ALLE Endpoints!
```

#### ✅ Vorteil 3: Einfach zu testen

```python
# Test 1: Middleware isoliert testen
def test_auth_middleware_rejects_invalid_token():
    middleware = ScalekitAuthMiddleware(config)
    response = await middleware(request_with_bad_token, mock_call_next)
    assert response.status_code == 401

# Test 2: Tool testen OHNE Auth-Komplexität
def test_search_tool():
    # Mock Context mit User-Info
    ctx = MockContext(state={"user_role": "student"})
    
    # Tool direkt testen
    result = await search_content_student("Java", ctx=ctx)
    
    assert len(result) > 0
```

#### ✅ Vorteil 4: Konsistente Error Handling

```python
# Middleware garantiert konsistente 401-Responses
if not is_valid:
    return Response(
        content='{"error": "invalid_token", ...}',
        status_code=401,
        headers={"WWW-Authenticate": 'Bearer realm="OAuth"'}
    )

# ALLE Auth-Fehler sehen gleich aus!
```

---

## Detaillierte Architektur-Diagramme

### 1. OAuth Authentication Flow (Login)

```
┌─────────────────────────────────────────────────────────────────┐
│                  OAUTH 2.1 AUTHENTICATION FLOW                   │
│                     (Initial User Login)                         │
└─────────────────────────────────────────────────────────────────┘

Step 1: User initiiert Login
┌──────────────┐
│ Claude/User  │
│ (LLM Client) │
└──────┬───────┘
       │
       │ GET /auth/login
       │
       ▼
┌─────────────────────────────────────┐
│  MCP Server                         │
│  oauth_flow.py                      │
│  ┌───────────────────────────────┐ │
│  │ @router.get("/auth/login")    │ │
│  │                               │ │
│  │ • CSRF State generieren       │ │
│  │ • Code Verifier generieren    │ │
│  │ • Session speichern           │ │
│  │ • Auth-URL bauen              │ │
│  └───────────────────────────────┘ │
└──────┬──────────────────────────────┘
       │
       │ 302 Redirect
       │ to: scalekit.com/oauth/authorize?
       │     client_id=xxx&
       │     state=abc123&
       │     redirect_uri=...
       │
       ▼
┌─────────────────────────────────────┐
│  Scalekit Authorization Server      │
│                                     │
│  ┌───────────────────────────────┐ │
│  │ User sieht Login-Seite        │ │
│  │ • Email eingeben              │ │
│  │ • Passwort eingeben           │ │
│  │ • Oder SSO (Google, etc.)     │ │
│  └───────────────────────────────┘ │
└──────┬──────────────────────────────┘
       │
       │ Nach erfolgreicher Authentifizierung
       │
       │ 302 Redirect
       │ to: our-server.com/callback?
       │     code=xyz789&
       │     state=abc123
       │
       ▼
┌─────────────────────────────────────┐
│  MCP Server                         │
│  oauth_flow.py                      │
│  ┌───────────────────────────────┐ │
│  │ @router.get("/callback")      │ │
│  │                               │ │
│  │ • State validieren (CSRF)     │ │
│  │ • Code gegen Token tauschen:  │ │
│  │                               │ │
│  │   POST /oauth/token           │ │────────┐
│  │   code=xyz789                 │ │        │
│  │   grant_type=auth_code        │ │        │
│  └───────────────────────────────┘ │        │
└─────────────────────────────────────┘        │
                                                │
                                                ▼
                                    ┌─────────────────────┐
                                    │ Scalekit Token EP   │
                                    │                     │
                                    │ Validiert Code      │
                                    │ Gibt zurück:        │
                                    │ • access_token      │
                                    │ • refresh_token     │
                                    │ • id_token (JWT)    │
                                    │ • expires_in        │
                                    └──────────┬──────────┘
                                               │
       ┌───────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  MCP Server                         │
│  oauth_flow.py                      │
│  ┌───────────────────────────────┐ │
│  │ • Session löschen             │ │
│  │ • Token zurückgeben an Client │ │
│  │                               │ │
│  │ return {                      │ │
│  │   "access_token": "...",      │ │
│  │   "token_type": "Bearer"      │ │
│  │ }                             │ │
│  └───────────────────────────────┘ │
└──────┬──────────────────────────────┘
       │
       │ JSON Response
       │
       ▼
┌──────────────┐
│ Claude/User  │
│              │
│ Speichert:   │
│ access_token │
└──────────────┘
```

### 2. API Request mit Token (jeder weitere Request)

```
┌─────────────────────────────────────────────────────────────────┐
│              AUTHENTICATED API REQUEST FLOW                      │
│         (Claude sendet Request mit Access Token)                 │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐
│ Claude/User  │
│              │
│ Hat Token:   │
│ Bearer xxx   │
└──────┬───────┘
       │
       │ POST /mcp
       │ Headers:
       │   Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
       │ Body:
       │   {"method": "tools/call", "params": {...}}
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  FastAPI Application                                            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  MIDDLEWARE CHAIN (Sequential Processing)              │   │
│  │                                                          │   │
│  │  [1] ScalekitAuthMiddleware                            │   │
│  │  ┌──────────────────────────────────────────────────┐ │   │
│  │  │ def __call__(request, call_next):               │ │   │
│  │  │                                                  │ │   │
│  │  │   # Check if public endpoint                    │ │   │
│  │  │   if path in ["/health", "/auth/login"]:        │ │   │
│  │  │       return await call_next(request) ─────┐    │ │   │
│  │  │                                            │    │ │   │
│  │  │   # Extract Bearer token                   │    │ │   │
│  │  │   auth = request.headers["authorization"]  │    │ │   │
│  │  │   token = auth.split("Bearer ")[1]         │    │ │   │
│  │  │                                            │    │ │   │
│  │  │   # Validate with Scalekit SDK             │    │ │   │
│  │  │   is_valid = scalekit_client               │    │ │   │
│  │  │     .validate_access_token(                │    │ │   │
│  │  │       token,                               │    │ │   │
│  │  │       options=ValidationOptions(           │    │ │   │
│  │  │         issuer=scalekit_url,               │    │ │   │
│  │  │         audience=["our-server"]            │    │ │   │
│  │  │       )                                     │    │ │   │
│  │  │     )                                       │    │ │   │
│  │  │                                            │    │ │   │
│  │  │   if not is_valid:                         │    │ │   │
│  │  │       return Response(                     │    │ │   │
│  │  │         status_code=401,                   │    │ │   │
│  │  │         headers={                          │    │ │   │
│  │  │           "WWW-Authenticate": "Bearer..."  │    │ │   │
│  │  │         }                                   │    │ │   │
│  │  │       ) ────────────────────────────────┐  │    │ │   │
│  │  │                                        │  │    │ │   │
│  │  │   # Token valid, continue              │  │    │ │   │
│  │  │   return await call_next(request) ───┐ │  │    │ │   │
│  │  └──────────────────────────────────────┼─┼──┼────┘ │   │
│  │                                          │ │  │      │   │
│  │  [2] RequestLoggingMiddleware           │ │  │      │   │
│  │  ┌──────────────────────────────────────┼─┼──┼───┐ │   │
│  │  │ • Generate request_id                │ │  │   │ │   │
│  │  │ • Log: [abc123] → tools/call         │ │  │   │ │   │
│  │  │ • Start timer                        │ │  │   │ │   │
│  │  │ • ctx.set_state("request_id", ...)   │ │  │   │ │   │
│  │  │ • return await call_next(ctx) ─────┐ │ │  │   │ │   │
│  │  └────────────────────────────────────┼─┼─┼──┼───┘ │   │
│  │                                        │ │ │  │     │   │
│  │  [3] UserContextMiddleware             │ │ │  │     │   │
│  │  ┌──────────────────────────────────────┼─┼─┼──┼─┐ │   │
│  │  │ • Decode JWT (no verification!)    │ │ │  │ │ │   │
│  │  │   claims = jwt.decode(token, ...)   │ │ │  │ │ │   │
│  │  │                                     │ │ │  │ │ │   │
│  │  │ • Extract user info:                │ │ │  │ │ │   │
│  │  │   user_id = claims["sub"]           │ │ │  │ │ │   │
│  │  │   user_email = claims["email"]      │ │ │  │ │ │   │
│  │  │   user_role = claims["role"]        │ │ │  │ │ │   │
│  │  │                                     │ │ │  │ │ │   │
│  │  │ • Store in FastMCP context:         │ │ │  │ │ │   │
│  │  │   ctx.set_state("user_id", ...)     │ │ │  │ │ │   │
│  │  │   ctx.set_state("user_role", ...)   │ │ │  │ │ │   │
│  │  │                                     │ │ │  │ │ │   │
│  │  │ • return await call_next(ctx) ────┐ │ │ │  │ │ │   │
│  │  └───────────────────────────────────┼─┼─┼─┼──┼─┘ │   │
│  │                                       │ │ │ │  │   │   │
│  │  [4] RBACEnforcementMiddleware        │ │ │ │  │   │   │
│  │  ┌───────────────────────────────────┼─┼─┼─┼──┼─┐ │   │
│  │  │ • Get tool name from request      │ │ │ │  │ │ │   │
│  │  │ • Check TOOL_PERMISSIONS:         │ │ │ │  │ │ │   │
│  │  │   if "get_stats" requires teacher │ │ │ │  │ │ │   │
│  │  │   and user_role == "student":     │ │ │ │  │ │ │   │
│  │  │       raise ToolError ──────────┐ │ │ │ │  │ │ │   │
│  │  │                                 │ │ │ │ │  │ │ │   │
│  │  │ • return await call_next(ctx) ─┼─┼─┼─┼─┼──┼─┘ │   │
│  │  └────────────────────────────────┼─┼─┼─┼─┼──┼───┘   │
│  │                                    │ │ │ │ │  │       │
│  │  [5] AuditLoggingMiddleware        │ │ │ │ │  │       │
│  │  ┌────────────────────────────────┼─┼─┼─┼─┼──┼───┐   │
│  │  │ • Log: [AUDIT] user=hash(id)   │ │ │ │ │  │   │   │
│  │  │   tool=search_content_student  │ │ │ │ │  │   │   │
│  │  │   role=student, result=success │ │ │ │ │  │   │   │
│  │  │                                │ │ │ │ │  │   │   │
│  │  │ • return await call_next(ctx) ─┼─┼─┼─┼─┼──┼─┐ │   │
│  │  └────────────────────────────────┼─┼─┼─┼─┼──┼─┘ │   │
│  └──────────────────────────────────┬┬─┬┬┬─┬┬┬──┬───┘   │
│                                      ││ │││ │││  │       │
│  All Middleware Passed! ✅          ││ │││ │││  │       │
└──────────────────────────────────────┼┼─┼┼┼─┼┼┼──┼───────┘
                                       ││ │││ │││  │
                                       ▼▼ ▼▼▼ ▼▼▼  ▼
┌─────────────────────────────────────────────────────────────────┐
│  MCP Tool Handler                                               │
│  (search_content_student)                                        │
│                                                                  │
│  @mcp.tool()                                                    │
│  async def search_content_student(                             │
│      query: str,                                               │
│      ctx: Context                                              │
│  ):                                                             │
│      """                                                        │
│      ✅ Auth bereits validiert!                                │
│      ✅ User-Info verfügbar via ctx.get_state()                │
│      ✅ RBAC bereits geprüft!                                  │
│      ✅ Request geloggt!                                       │
│      """                                                        │
│                                                                  │
│      # User-Info aus Context holen                             │
│      user_role = ctx.get_state("user_role")  # "student"       │
│      user_id = ctx.get_state("user_id")      # "user-123"      │
│                                                                  │
│      # Progress Reporting                                       │
│      await ctx.report_progress(0, 4, "Generiere Embedding...")  │
│                                                                  │
│      # Business Logic (NUR das!)                               │
│      embedding = embed_query(query)                            │
│      results = search_qdrant(                                  │
│          embedding,                                            │
│          filters={"access_level": "student"}                   │
│      )                                                          │
│                                                                  │
│      await ctx.report_progress(4, 4, "Fertig!")                 │
│                                                                  │
│      return format_results(results)                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
       │
       │ Response mit Ergebnissen
       │
       ▼
┌──────────────┐
│ Claude/User  │
│              │
│ Erhält:      │
│ Search       │
│ Results      │
└──────────────┘


401 Response Flow (wenn Token ungültig):
                           ┌───────────────────────────┐
                           │ ScalekitAuthMiddleware    │
                           │ erkennt ungültigen Token  │
                           └──────────┬────────────────┘
                                      │
                                      │ Sofort 401 Response
                                      │ (kein weiteres Middleware)
                                      │
                                      ▼
                           ┌───────────────────────────┐
                           │ Response:                 │
                           │ Status: 401 Unauthorized  │
                           │ Headers:                  │
                           │   WWW-Authenticate:       │
                           │     Bearer realm="OAuth"  │
                           │ Body:                     │
                           │   {"error": "invalid_..."}│
                           └──────────┬────────────────┘
                                      │
                                      ▼
                           ┌───────────────────────────┐
                           │ Claude/User               │
                           │ Muss neu authentifizieren │
                           └───────────────────────────┘
```

---

## Code-Beispiele im Vergleich

### Beispiel 1: Search Endpoint

#### ❌ Controller-Pattern (Java Spring Boot)

```java
@RestController
@RequestMapping("/api")
public class SearchController {
    
    @Autowired
    private AuthenticationService authService;
    
    @Autowired
    private SearchService searchService;
    
    @Autowired
    private RBACService rbacService;
    
    /**
     * Search endpoint with EXPLICIT auth checks
     */
    @GetMapping("/search")
    public ResponseEntity<SearchResponse> search(
        @RequestHeader("Authorization") String authHeader,
        @RequestParam String query,
        @RequestParam(defaultValue = "10") int limit
    ) {
        // ═══════════════════════════════════════════════════
        // STEP 1: Token Extraction (MANUAL)
        // ═══════════════════════════════════════════════════
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            return ResponseEntity
                .status(HttpStatus.UNAUTHORIZED)
                .header("WWW-Authenticate", "Bearer")
                .body(null);
        }
        
        String token = authHeader.substring(7);
        
        // ═══════════════════════════════════════════════════
        // STEP 2: Token Validation (MANUAL)
        // ═══════════════════════════════════════════════════
        User user;
        try {
            user = authService.validateToken(token);
        } catch (InvalidTokenException e) {
            logger.warn("Invalid token: {}", e.getMessage());
            return ResponseEntity
                .status(HttpStatus.UNAUTHORIZED)
                .header("WWW-Authenticate", "Bearer")
                .body(null);
        }
        
        if (user == null) {
            return ResponseEntity
                .status(HttpStatus.UNAUTHORIZED)
                .body(null);
        }
        
        // ═══════════════════════════════════════════════════
        // STEP 3: RBAC Check (MANUAL)
        // ═══════════════════════════════════════════════════
        if (!rbacService.hasPermission(user, "search:read")) {
            logger.warn("User {} lacks permission for search", user.getId());
            return ResponseEntity
                .status(HttpStatus.FORBIDDEN)
                .body(null);
        }
        
        // ═══════════════════════════════════════════════════
        // STEP 4: Audit Logging (MANUAL)
        // ═══════════════════════════════════════════════════
        auditLog.log(AuditEvent.builder()
            .user(user.getId())
            .action("SEARCH")
            .timestamp(Instant.now())
            .build()
        );
        
        // ═══════════════════════════════════════════════════
        // STEP 5: FINALLY - Business Logic
        // ═══════════════════════════════════════════════════
        try {
            SearchResponse response = searchService.search(
                query, 
                limit, 
                user.getRole()
            );
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Search failed", e);
            return ResponseEntity
                .status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(null);
        }
    }
}
```

**Lines of Code:** ~80 Zeilen (davon ~60 für Auth/RBAC/Logging!)

---

#### ✅ Middleware-Pattern (Python FastAPI + FastMCP)

```python
# ═══════════════════════════════════════════════════════════════
# FILE: src/tools/search_tools.py
# ═══════════════════════════════════════════════════════════════

@mcp.tool(
    name="search_content_student",
    description="Search with student access",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True
    )
)
async def search_content_student(
    query: str,
    limit: int = 10,
    ctx: Context = None
) -> dict:
    """
    Search educational content with student access.
    
    ✅ Auth: Already validated by ScalekitAuthMiddleware
    ✅ User Context: Already extracted by UserContextMiddleware
    ✅ RBAC: Already checked by RBACEnforcementMiddleware
    ✅ Logging: Already logged by AuditLoggingMiddleware
    
    This tool ONLY contains business logic!
    """
    from src.server.lifespan import AppContext
    
    # ═══════════════════════════════════════════════════════
    # Get injected dependencies (from lifespan)
    # ═══════════════════════════════════════════════════════
    app: AppContext = ctx.lifespan_context
    
    # ═══════════════════════════════════════════════════════
    # Get user info (set by UserContextMiddleware)
    # ═══════════════════════════════════════════════════════
    user_role = ctx.get_state("user_role") or "student"
    user_id = ctx.get_state("user_id") or "anonymous"
    
    # ═══════════════════════════════════════════════════════
    # Progress Reporting (UX enhancement)
    # ═══════════════════════════════════════════════════════
    await ctx.report_progress(0, 4, "Analysiere Suchanfrage...")
    
    # ═══════════════════════════════════════════════════════
    # Business Logic - THAT'S ALL!
    # ═══════════════════════════════════════════════════════
    
    # Generate embedding
    await ctx.report_progress(1, 4, "Generiere Embedding...")
    query_embedding = app.embedding_service.embed_query(query)
    
    # Build RBAC filter (student-level only)
    await ctx.report_progress(2, 4, "Wende Filter an...")
    from qdrant_client.models import Filter, FieldCondition, MatchAny
    access_filter = Filter(
        must=[
            FieldCondition(
                key="access_level",
                match=MatchAny(any=["student"])
            )
        ]
    )
    
    # Execute search
    await ctx.report_progress(3, 4, "Durchsuche Datenbank...")
    results = app.qdrant.search(
        query_vector=query_embedding,
        collection=app.config.default_collection,
        limit=limit,
        filters=access_filter
    )
    
    # Format and return
    await ctx.report_progress(4, 4, "Formatiere Ergebnisse...")
    formatted = _format_search_results(results, query)
    
    return {
        "content": [{
            "type": "text",
            "text": formatted
        }]
    }
```

**Lines of Code:** ~35 Zeilen (davon ~30 für Business Logic!)

---

### Beispiel 2: Admin Stats Endpoint

#### ❌ Controller-Pattern

```java
@GetMapping("/admin/stats")
public ResponseEntity<Stats> getStats(
    @RequestHeader("Authorization") String authHeader
) {
    // Auth validation (wieder)
    User user = authService.validateToken(extractToken(authHeader));
    if (user == null) {
        return ResponseEntity.status(401).build();
    }
    
    // RBAC check (wieder)
    if (!user.hasRole("ADMIN") && !user.hasRole("TEACHER")) {
        return ResponseEntity.status(403).build();
    }
    
    // Audit log (wieder)
    auditLog.log("STATS_ACCESS", user.getId());
    
    // Business logic
    Stats stats = statsService.getCollectionStats();
    return ResponseEntity.ok(stats);
}
```

**Problem:** Auth/RBAC/Audit-Code wieder kopiert!

---

#### ✅ Middleware-Pattern

```python
@mcp.tool(name="get_collection_stats")
async def get_collection_stats(ctx: Context) -> dict:
    """
    Get collection statistics.
    
    Access: Teacher/Admin only (enforced by RBACEnforcementMiddleware)
    """
    app: AppContext = ctx.lifespan_context
    
    # Just business logic!
    collection_info = app.qdrant.client.get_collection(
        app.config.default_collection
    )
    
    return {
        "total_documents": collection_info.points_count,
        "vector_dimensions": collection_info.config.params.vectors.size,
        # ...
    }
```

**RBAC wird automatisch geprüft von:**

```python
# src/middleware/mcp_middleware.py
class RBACEnforcementMiddleware:
    TOOL_PERMISSIONS = {
        "get_collection_stats": {"admin", "teacher"},  # ← Definition
    }
    
    async def on_call_tool(self, context, call_next):
        tool_name = context.message.name
        required_roles = self.TOOL_PERMISSIONS.get(tool_name, set())
        
        if required_roles:
            user_role = context.fastmcp_context.get_state("user_role")
            
            if user_role not in required_roles:
                raise ToolError(f"Access denied. Requires: {required_roles}")
        
        return await call_next(context)
```

**Vorteil:** RBAC-Rules an EINER Stelle definiert, automatisch enforced!

---

## Die 3 Schichten im Detail

### Schicht 1: OAuth Flow (Login/Callback)

**Zweck:** Initialer Login und Token-Erhalt

**Datei:** `src/auth/oauth_flow.py`

**Komponenten:**

```python
def create_oauth_router(
    scalekit_env_url: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str
) -> APIRouter:
    """
    Create OAuth router with 3 endpoints:
    1. /auth/login   - Initiate OAuth flow
    2. /callback     - OAuth callback from Scalekit
    3. /auth/logout  - End session
    """
```

#### Endpoint 1: `/auth/login`

```python
@router.get("/auth/login")
async def login(organization_id: Optional[str] = None):
    """
    User/Claude initiates login.
    
    Flow:
    1. Generate CSRF state token
    2. Generate PKCE code verifier
    3. Store in session (temporary, in-memory)
    4. Redirect to Scalekit authorization page
    """
    # CSRF protection
    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(32)
    
    sessions[state] = {
        "code_verifier": code_verifier,
        "created_at": datetime.now()
    }
    
    # Build authorization URL
    auth_url = (
        f"{scalekit_env_url}/oauth/authorize?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"state={state}&"
        f"response_type=code&"
        f"scope=openid profile email"
    )
    
    return RedirectResponse(url=auth_url, status_code=302)
```

#### Endpoint 2: `/callback`

```python
@router.get("/callback")
async def callback(code: str, state: str):
    """
    Scalekit redirects here after user authentication.
    
    Flow:
    1. Validate state (CSRF check)
    2. Exchange authorization code for access token
    3. Delete session (cleanup)
    4. Return token to client
    """
    # Validate CSRF state
    if state not in sessions:
        raise HTTPException(400, "Invalid state. CSRF attack?")
    
    session = sessions[state]
    
    # Exchange code for token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{scalekit_env_url}/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": client_id,
                "client_secret": client_secret
            }
        )
    
    token_data = response.json()
    
    # Cleanup
    del sessions[state]
    
    # Return token to client
    return {
        "access_token": token_data["access_token"],
        "token_type": "Bearer",
        "expires_in": token_data["expires_in"]
    }
```

**Wichtig:** Diese Endpoints sind **public** (kein Auth nötig)!

---

### Schicht 2: Token Validation Middleware

**Zweck:** Jeder Request wird automatisch auf gültigen Token geprüft

**Datei:** `src/middleware/scalekit_auth.py`

**Aufbau:**

```python
class ScalekitAuthMiddleware:
    """
    FastAPI Middleware für OAuth 2.1 Token Validation.
    
    Läuft AUTOMATISCH vor JEDEM Request.
    """
    
    def __init__(self, config: ServerConfig):
        # Scalekit SDK Client initialisieren
        self.scalekit_client = ScalekitClient(
            env_url=config.scalekit_env_url,
            client_id=config.scalekit_client_id,
            client_secret=config.scalekit_client_secret
        )
        
        # WWW-Authenticate header für 401 responses
        self.www_authenticate_header = {
            "WWW-Authenticate": (
                f'Bearer realm="OAuth", '
                f'resource_metadata="{base_url}/.well-known/oauth-protected-resource"'
            )
        }
    
    async def __call__(
        self, 
        request: Request, 
        call_next: Callable
    ) -> Response:
        """
        Main middleware logic - runs for EVERY request.
        """
        
        # ═══════════════════════════════════════════════════
        # STEP 1: Check if endpoint is public
        # ═══════════════════════════════════════════════════
        if self._is_public_endpoint(request.url.path):
            # Allow without auth
            return await call_next(request)
        
        # ═══════════════════════════════════════════════════
        # STEP 2: Extract Bearer token
        # ═══════════════════════════════════════════════════
        auth_header = request.headers.get("authorization", "")
        
        if not auth_header.startswith("Bearer "):
            return Response(
                content='{"error": "invalid_token"}',
                status_code=401,
                headers=self.www_authenticate_header
            )
        
        token = auth_header.split("Bearer ", 1)[1].strip()
        
        # ═══════════════════════════════════════════════════
        # STEP 3: Validate token with Scalekit SDK
        # ═══════════════════════════════════════════════════
        try:
            is_valid = self.scalekit_client.validate_access_token(
                token,
                options=TokenValidationOptions(
                    issuer=self.config.scalekit_env_url,
                    audience=[self.config.scalekit_expected_audience]
                )
            )
            
            if not is_valid:
                return Response(
                    content='{"error": "invalid_token"}',
                    status_code=401,
                    headers=self.www_authenticate_header
                )
        
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return Response(
                content='{"error": "invalid_token"}',
                status_code=401,
                headers=self.www_authenticate_header
            )
        
        # ═══════════════════════════════════════════════════
        # STEP 4: Token valid → proceed to next middleware/handler
        # ═══════════════════════════════════════════════════
        return await call_next(request)
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint doesn't require auth."""
        public_paths = [
            "/.well-known/oauth-protected-resource",
            "/health",
            "/docs",
            "/auth/login",
            "/callback",
            "/auth/logout"
        ]
        return any(path.startswith(p) for p in public_paths)
```

**Key Points:**

1. **Automatic:** Läuft bei JEDEM Request
2. **Centralized:** Token-Validation-Logic an EINER Stelle
3. **Scalekit SDK:** Nutzt offizielles SDK für Validation
4. **OAuth 2.1 Compliant:** Korrekte WWW-Authenticate Headers
5. **Public Endpoints:** Health/Login/Docs sind ausgenommen

---

### Schicht 3: FastMCP Middleware (User Context & RBAC)

**Zweck:** User-Info extrahieren und RBAC enforced

**Datei:** `src/middleware/mcp_middleware.py`

#### Middleware 1: RequestLoggingMiddleware

```python
class RequestLoggingMiddleware(Middleware):
    """
    Logs all requests with correlation IDs and timing.
    """
    
    async def on_request(self, context: MiddlewareContext, call_next):
        # Generate request ID for correlation
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # Store in context for tools
        context.fastmcp_context.set_state("request_id", request_id)
        
        logger.info(f"[{request_id}] → {context.method}")
        
        try:
            result = await call_next(context)
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"[{request_id}] ✓ completed in {duration_ms:.1f}ms")
            return result
        except Exception as e:
            logger.error(f"[{request_id}] ✗ failed: {e}")
            raise
```

#### Middleware 2: UserContextMiddleware

```python
class UserContextMiddleware(Middleware):
    """
    Extracts user info from JWT and stores in FastMCP context.
    
    Note: Token is already validated by ScalekitAuthMiddleware!
    We just extract claims here.
    """
    
    async def on_request(self, context: MiddlewareContext, call_next):
        # Get headers
        headers = get_http_headers() or {}
        auth_header = headers.get("authorization", "")
        
        # Default values
        user_id = None
        user_email = None
        user_role = "student"
        
        # Extract JWT claims if present
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                # Decode JWT (no signature verification needed - 
                # Scalekit already validated!)
                claims = jwt.decode(
                    token, 
                    options={"verify_signature": False}
                )
                
                user_id = claims.get("sub")
                user_email = claims.get("email")
                user_role = claims.get("role", "student")
                
            except Exception as e:
                logger.warning(f"Failed to extract JWT claims: {e}")
        
        # Store in FastMCP context (available in all tools!)
        context.fastmcp_context.set_state("user_id", user_id)
        context.fastmcp_context.set_state("user_email", user_email)
        context.fastmcp_context.set_state("user_role", user_role)
        
        return await call_next(context)
```

#### Middleware 3: RBACEnforcementMiddleware

```python
class RBACEnforcementMiddleware(Middleware):
    """
    Enforces role-based access control at tool level.
    
    Tools can be restricted to specific roles.
    """
    
    # Define which tools require which roles
    TOOL_PERMISSIONS = {
        # Admin-only
        "reindex_document": {"admin"},
        "delete_content": {"admin"},
        "manage_users": {"admin"},
        
        # Teacher+
        "get_collection_stats": {"admin", "teacher"},
        "content_get_document": {"teacher", "admin"},
    }
    
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """
        Check permissions before tool execution.
        """
        tool_name = context.message.name
        required_roles = self.TOOL_PERMISSIONS.get(tool_name, set())
        
        if required_roles:
            user_role = context.fastmcp_context.get_state("user_role") or "guest"
            
            if user_role not in required_roles:
                logger.warning(
                    f"Access denied: {user_role} tried to access "
                    f"{tool_name} (requires: {required_roles})"
                )
                raise ToolError(
                    f"Access denied. Tool '{tool_name}' requires one of: "
                    f"{', '.join(sorted(required_roles))}"
                )
        
        return await call_next(context)
```

#### Middleware 4: AuditLoggingMiddleware

```python
class AuditLoggingMiddleware(Middleware):
    """
    Audit logging for DSGVO compliance.
    """
    
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        tool_name = context.message.name
        user_id = context.fastmcp_context.get_state("user_id") or "anonymous"
        user_role = context.fastmcp_context.get_state("user_role") or "unknown"
        request_id = context.fastmcp_context.get_state("request_id") or "unknown"
        
        # Pseudonymize user ID (DSGVO)
        user_id_hash = hash(user_id) if user_id != "anonymous" else "anonymous"
        
        try:
            result = await call_next(context)
            
            logger.info(
                f"[AUDIT] Tool invocation successful - "
                f"request_id={request_id}, tool={tool_name}, "
                f"user={user_id_hash}, role={user_role}"
            )
            
            return result
        except Exception as e:
            logger.warning(
                f"[AUDIT] Tool invocation failed - "
                f"request_id={request_id}, tool={tool_name}, "
                f"user={user_id_hash}, role={user_role}, "
                f"error={type(e).__name__}"
            )
            raise
```

---

## Vorteile & Nachteile

### Controller-Pattern

#### ✅ Vorteile

1. **Explizit:** Auth-Logic ist sichtbar im Code
2. **Flexibel:** Jeder Controller kann eigene Auth-Regeln haben
3. **Vertraut:** Viele Entwickler kennen dieses Pattern

#### ❌ Nachteile

1. **Code-Duplikation:** Auth-Code in jedem Controller wiederholt
2. **Fehleranfällig:** Leicht zu vergessen, Auth-Check hinzuzufügen
3. **Schwer wartbar:** Änderung an Auth-Logic = alle Controller anpassen
4. **Inkonsistenz:** Unterschiedliche Implementierungen möglich
5. **Mixing Concerns:** Auth + Business Logic vermischt
6. **Schwer testbar:** Tests müssen Auth + Logic testen
7. **Performance:** Redundante Validierung (z.B. Token-Decode in jedem Controller)

---

### Middleware-Pattern

#### ✅ Vorteile

1. **DRY (Don't Repeat Yourself):** Auth-Code an EINER Stelle
2. **Sicherheit:** Unmöglich zu vergessen (automatisch für alle Endpoints)
3. **Wartbarkeit:** Änderungen an Auth = nur Middleware anpassen
4. **Konsistenz:** Gleiche Auth-Logic für alle Endpoints
5. **Separation of Concerns:** Auth getrennt von Business Logic
6. **Testability:** Middleware und Tools separat testbar
7. **Performance:** Token einmal validieren, Claims cachen
8. **Best Practice:** Industry Standard (Spring Security Filter, Express.js Middleware, etc.)

#### ❌ Nachteile

1. **Weniger explizit:** Auth-Logic nicht sichtbar im Tool-Code
2. **Debugging:** Bei Fehlern muss man Middleware-Chain verstehen
3. **Lernkurve:** Anfänger müssen Middleware-Konzept verstehen

---

## Best Practices

### 1. Public Endpoints klar definieren

```python
def _is_public_endpoint(self, path: str) -> bool:
    """
    Zentrale Liste aller öffentlichen Endpoints.
    
    Best Practice:
    - Liste klein halten
    - Dokumentieren WARUM public
    - Regelmäßig reviewen
    """
    public_paths = [
        "/.well-known/oauth-protected-resource",  # OAuth discovery
        "/health",                                 # Health check
        "/docs",                                   # API docs (optional)
        "/auth/login",                             # OAuth initiation
        "/callback",                               # OAuth callback
    ]
    return any(path.startswith(p) for p in public_paths)
```

### 2. Konsistente Error Responses

```python
# BAD: Verschiedene Error-Formate
return Response(status_code=401)
return {"error": "unauthorized"}
raise HTTPException(401, "Unauthorized")

# GOOD: OAuth 2.1 konformes Error-Format
return Response(
    content=json.dumps({
        "error": "invalid_token",
        "error_description": "Token validation failed"
    }),
    status_code=401,
    media_type="application/json",
    headers={
        "WWW-Authenticate": 'Bearer realm="OAuth", resource_metadata="..."'
    }
)
```

### 3. Logging für Security-Events

```python
# Auth Success
logger.info(f"Token validated successfully for {request.url.path}")

# Auth Failure
logger.warning(f"Invalid token for {request.url.path} from IP {request.client.host}")

# RBAC Denial
logger.warning(
    f"Access denied: user with role '{user_role}' tried to access "
    f"tool '{tool_name}' (requires: {', '.join(required_roles)})"
)

# Audit Trail
logger.info(
    f"[AUDIT] Tool invocation - "
    f"request_id={request_id}, tool={tool_name}, "
    f"user={hash(user_id)}, role={user_role}, result=success"
)
```

### 4. Token-Speicherung: NIEMALS!

```python
# ❌ NEVER DO THIS!
class BadAuthMiddleware:
    def __init__(self):
        self.tokens = {}  # ← DANGEROUS!
    
    async def __call__(self, request, call_next):
        token = extract_token(request)
        self.tokens[token] = True  # ← DON'T STORE TOKENS!
        # ...

# ✅ CORRECT: Stateless validation
class ScalekitAuthMiddleware:
    async def __call__(self, request, call_next):
        token = extract_token(request)
        
        # Validate with Scalekit SDK (stateless!)
        is_valid = self.scalekit_client.validate_access_token(token)
        
        # Token NOT stored - validated per request
        if not is_valid:
            return Response(status_code=401)
        
        return await call_next(request)
```

**Warum?**
- Tokens gehören dem Client (Claude Desktop)
- Server sollte stateless sein (horizontal scaling)
- Speicherung = Security Risk (Token-Leakage)
- DSGVO: Tokens enthalten personenbezogene Daten

### 5. Middleware-Reihenfolge ist wichtig!

```python
# ✅ CORRECT ORDER:

# 1. Auth FIRST (block unauthenticated requests early)
app.add_middleware(BaseHTTPMiddleware, dispatch=scalekit_auth_middleware)

# 2. Then FastMCP middleware
mcp.add_middleware(RequestLoggingMiddleware())      # Logging
mcp.add_middleware(UserContextMiddleware())          # Extract user info
mcp.add_middleware(RBACEnforcementMiddleware())      # Tool-level RBAC
mcp.add_middleware(AuditLoggingMiddleware())         # Audit trail

# 3. Finally: Tool handlers
@mcp.tool()
async def my_tool(...):
    # ...
```

**Warum diese Reihenfolge?**
1. **Auth first:** Keine unnötige Verarbeitung für ungültige Requests
2. **Logging early:** Alle Requests loggen (auch abgelehnte)
3. **User Context before RBAC:** RBAC braucht user_role
4. **Audit last:** Sollte auch Failures loggen

---

## Integration in diesem Projekt

### Datei-Übersicht

```
src/
├── auth/
│   └── oauth_flow.py              # OAuth Login/Callback/Logout
│
├── middleware/
│   ├── scalekit_auth.py           # Token Validation (Schicht 2)
│   └── mcp_middleware.py          # FastMCP Middleware (Schicht 3)
│       ├── RequestLoggingMiddleware
│       ├── UserContextMiddleware
│       ├── RBACEnforcementMiddleware
│       └── AuditLoggingMiddleware
│
├── tools/
│   └── search_tools.py            # MCP Tools (OHNE Auth-Code!)
│       ├── search_content_student
│       ├── search_content_teacher
│       └── get_collection_stats
│
└── server/
    └── lifespan.py                # Dependency Injection

main.py                            # Registration
```

### Registration in main.py

```python
# ═══════════════════════════════════════════════════════════════
# 1. FastAPI App erstellen
# ═══════════════════════════════════════════════════════════════
app = FastAPI(title="MCP Educational Server")

# ═══════════════════════════════════════════════════════════════
# 2. OAuth Router registrieren (Schicht 1: Login/Callback)
# ═══════════════════════════════════════════════════════════════
oauth_router = create_oauth_router(
    scalekit_env_url=config.scalekit_env_url,
    client_id=config.scalekit_client_id,
    client_secret=config.scalekit_client_secret,
    redirect_uri=config.oauth_redirect_uri
)
app.include_router(oauth_router)

# ═══════════════════════════════════════════════════════════════
# 3. Scalekit Auth Middleware registrieren (Schicht 2: Validation)
# ═══════════════════════════════════════════════════════════════
if config.enable_auth:
    scalekit_middleware = create_scalekit_middleware(config)
    app.add_middleware(
        BaseHTTPMiddleware, 
        dispatch=scalekit_middleware
    )
    logger.info("✓ Scalekit authentication middleware enabled")

# ═══════════════════════════════════════════════════════════════
# 4. FastMCP initialisieren mit Lifespan
# ═══════════════════════════════════════════════════════════════
from src.server.lifespan import app_lifespan

mcp = FastMCP(
    name="MCP Educational Server",
    lifespan=app_lifespan,
    stateless_http=True
)

# ═══════════════════════════════════════════════════════════════
# 5. FastMCP Middleware registrieren (Schicht 3: Context & RBAC)
# ═══════════════════════════════════════════════════════════════
from src.middleware.mcp_middleware import (
    RequestLoggingMiddleware,
    UserContextMiddleware,
    RBACEnforcementMiddleware,
    AuditLoggingMiddleware
)

mcp.add_middleware(RequestLoggingMiddleware())
mcp.add_middleware(UserContextMiddleware())
mcp.add_middleware(RBACEnforcementMiddleware())
mcp.add_middleware(AuditLoggingMiddleware())

logger.info("✓ Registered 4 FastMCP middleware components")

# ═══════════════════════════════════════════════════════════════
# 6. Tools registrieren (OHNE Auth-Code!)
# ═══════════════════════════════════════════════════════════════
from src.tools.search_tools import register_search_tools

register_search_tools(mcp)

logger.info("✓ Registered MCP tools")

# ═══════════════════════════════════════════════════════════════
# 7. MCP in FastAPI mounten
# ═══════════════════════════════════════════════════════════════
app.mount("", mcp.get_asgi_app())

logger.info("✓ MCP server mounted in FastAPI")
```

### Request Flow Beispiel

```
User sendet: POST /mcp mit Bearer Token

↓ FastAPI receives request

1️⃣ ScalekitAuthMiddleware (FastAPI Middleware)
   • Extract token from Authorization header
   • Validate with Scalekit SDK
   • If invalid → 401 Response (STOP)
   • If valid → Continue ↓

2️⃣ RequestLoggingMiddleware (FastMCP Middleware)
   • Generate request_id
   • Log request start
   • Store request_id in context
   • Continue ↓

3️⃣ UserContextMiddleware (FastMCP Middleware)
   • Decode JWT (no signature check - Scalekit already did!)
   • Extract: user_id, user_email, user_role
   • Store in FastMCP context via set_state()
   • Continue ↓

4️⃣ RBACEnforcementMiddleware (FastMCP Middleware)
   • Get tool name from request
   • Check TOOL_PERMISSIONS dict
   • Get user_role from context
   • If role not allowed → ToolError (STOP)
   • If allowed → Continue ↓

5️⃣ AuditLoggingMiddleware (FastMCP Middleware)
   • Log tool invocation (user, tool, result)
   • Pseudonymize user_id (DSGVO)
   • Continue ↓

6️⃣ Tool Handler (search_content_student)
   • Get user_role from ctx.get_state("user_role")
   • Execute business logic
   • Return results

↓ Response

7️⃣ AuditLoggingMiddleware (on way back)
   • Log success/failure
   
↓ Return to FastAPI

8️⃣ RequestLoggingMiddleware (on way back)
   • Log request completion + duration

↓ Send response to user
```

---

## Zusammenfassung

### Controller-Pattern (Alt)

```
Request → Router → Controller
                    ├─ Auth Check (manual)
                    ├─ RBAC Check (manual)
                    ├─ Audit Log (manual)
                    └─ Business Logic

Problem: Auth in JEDEM Controller wiederholt!
```

### Middleware-Pattern (Modern)

```
Request → Middleware Chain → Tool Handler
          ├─ Auth (automatic)
          ├─ Logging (automatic)
          ├─ User Context (automatic)
          ├─ RBAC (automatic)
          └─ Audit (automatic)

Tool: NUR Business Logic!
```

---

## Fazit

**Das Middleware-Pattern ist besser für Authentication, weil:**

1. ✅ **Sicherer** - Unmöglich zu vergessen
2. ✅ **Wartbarer** - DRY (Don't Repeat Yourself)
3. ✅ **Testbarer** - Middleware und Tools separat testbar
4. ✅ **Professioneller** - Industry Standard
5. ✅ **Skalierbarer** - Stateless, horizontal scaling möglich

**In diesem Projekt:**
- ✅ Scalekit OAuth 2.1 mit offiziellem SDK
- ✅ 5 Middleware-Komponenten (1 FastAPI + 4 FastMCP)
- ✅ Saubere Trennung: Auth ≠ Business Logic
- ✅ DSGVO-konform mit Audit-Logging
- ✅ Production-ready Architecture

---

**Erstellt:** 31. Januar 2026  
**Autor:** Imre (HTL Diploma Thesis)  
**Projekt:** LeoWiki MCP Educational Server  
**Version:** 2.0.0
