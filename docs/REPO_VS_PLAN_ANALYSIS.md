# Repository vs. Plan - Detaillierte Analyse

## Repository: `mcp-diploma-thesis-final`

## Verglichen mit: `PHASE_1_WEB_CLIENT_AUTH.md`

> **Analysiert am: 19. Januar 2026**

---

## Executive Summary

Das bestehende Repository hat bereits **eine solide Grundlage** für OAuth 2.1 mit ScaleKit implementiert. Allerdings gibt es **kritische Lücken**, die behoben werden müssen, damit die Authentifizierung funktioniert.

### Status-Übersicht

| Komponente | Status | Bemerkung |
|-----------|--------|-----------|
| FastMCP Server | ✅ Vollständig | Gut implementiert |
| OAuth Metadata Endpoint | ✅ Vorhanden | `/.well-known/oauth-protected-resource` |
| ScaleKit SDK Integration | ✅ Vorhanden | Offizielle SDK verwendet |
| Auth Middleware | ✅ Vorhanden | Token-Validierung funktioniert |
| OAuth Callback Handler | ⚠️ **NICHT GEMOUNTET** | Code existiert, aber nicht aktiv! |
| OAuth Login Endpoint | ⚠️ **NICHT GEMOUNTET** | Code existiert, aber nicht aktiv! |
| Environment Config | ⚠️ **UNVOLLSTÄNDIG** | Wichtige Variablen fehlen |
| RBAC | ✅ Vollständig | Student/Teacher/Admin |
| Docker/Caddy Setup | ✅ Vollständig | Production-ready |

---

## 🔴 KRITISCHE PROBLEME

### Problem 1: OAuth Router NICHT registriert

**Datei: `src/auth/oauth_flow.py`** enthält einen vollständigen OAuth Router mit:
- `/auth/login` - Startet OAuth Flow
- `/auth/callback` - Verarbeitet ScaleKit Callback
- `/auth/logout` - Logout
- `/auth/user` - User Info

**ABER: In `main.py` wird dieser Router NIEMALS registriert!**

```python
# main.py - Der OAuth Router fehlt!

# Diese Imports existieren:
from src.auth.oauth_flow import create_oauth_router  # ❌ NICHT VORHANDEN!

# Dieser Code fehlt:
oauth_router = create_oauth_router(
    scalekit_env_url=config.scalekit_env_url,
    client_id=config.scalekit_client_id,
    client_secret=config.scalekit_client_secret,
    redirect_uri=f"https://leowiki-mcp.stream/auth/callback",
)
app.include_router(oauth_router)  # ❌ FEHLT!
```

**Auswirkung:**
- 🔴 `/auth/login` existiert nicht → Keine Web-Login Möglichkeit
- 🔴 `/auth/callback` existiert nicht → ScaleKit Callback schlägt fehl
- 🔴 Gesamte Web-Client-Authentifizierung funktioniert nicht!

---

### Problem 2: Environment-Variablen unvollständig

**env.example enthält:**
```env
ENABLE_AUTH=false  # ⚠️ Default ist false!
SCALEKIT_ENV_URL=https://mcpeduauth.scalekit.dev  # ⚠️ Falscher Wert!
SCALEKIT_CLIENT_ID=your-client-id-here
SCALEKIT_CLIENT_SECRET=your-client-secret-here
```

**Es FEHLEN:**
```env
# Fehlende Variablen:
SCALEKIT_MCP_SERVER_ID=res_107039365691081482
SCALEKIT_EXPECTED_AUDIENCE=https://leowiki-mcp.stream
SCALEKIT_PROTECTED_RESOURCE_METADATA={"resource":"res_107039365691081482",...}
```

**Auswirkung:**
- 🔴 Token-Validierung verwendet falschen Audience-Wert
- 🔴 OAuth Metadata-Endpoint generiert Fallback statt echte ScaleKit-Daten

---

### Problem 3: Callback-URL nicht konfigurierbar

In `oauth_flow.py` wird die Redirect-URI als Parameter übergeben, aber in `main.py` ist keine Möglichkeit, diese zu konfigurieren (da der Router nicht gemountet ist).

**Korrekte Callback-URL für ScaleKit:**
- Production: `https://leowiki-mcp.stream/auth/callback`
- Lokal: `http://localhost:8000/auth/callback`

---

## ✅ WAS GUT IMPLEMENTIERT IST

### 1. ScaleKit SDK Integration (Besser als unser Plan!)

**Bestehende Implementation:**
```python
# src/middleware/scalekit_auth.py
from scalekit import ScalekitClient
from scalekit.common.scalekit import TokenValidationOptions

self.scalekit_client = ScalekitClient(
    env_url=config.scalekit_env_url,
    client_id=config.scalekit_client_id,
    client_secret=config.scalekit_client_secret
)

# Token-Validierung mit offiziellem SDK:
validation_options = TokenValidationOptions(
    issuer=self.config.scalekit_env_url,
    audience=[self.config.scalekit_expected_audience]
)
is_valid = self.scalekit_client.validate_access_token(token, options=validation_options)
```

**Unser Plan:**
```python
# Manuelle JWT-Validierung mit PyJWT
claims = jwt.decode(token, jwks, algorithms=["RS256"], ...)
```

**Bewertung:** ⭐ Die bestehende Implementation ist **BESSER** - sie verwendet das offizielle ScaleKit SDK, das:
- JWKS-Caching automatisch handhabt
- Key-Rotation unterstützt
- Von ScaleKit gepflegt wird

---

### 2. OAuth Metadata Endpoint

**Bestehende Implementation:**
```python
# src/server/oauth_metadata.py
async def get_oauth_protected_resource_metadata(config: ServerConfig):
    # Option 1: Verwende Metadata aus ScaleKit Dashboard
    if config.scalekit_protected_resource_metadata:
        metadata = json.loads(config.scalekit_protected_resource_metadata)
        return Response(content=json.dumps(metadata), ...)
    
    # Option 2: Generiere Default (Fallback)
    metadata = _generate_default_metadata(config)
    return Response(content=json.dumps(metadata), ...)
```

**Bewertung:** ⭐ Korrekte Implementation nach ScaleKit-Dokumentation!

---

### 3. RBAC (Role-Based Access Control)

**Bestehende Implementation:**
```python
# src/tools/search_tools.py
ROLE_ACCESS_LEVELS = {
    "student": ["student"],
    "teacher": ["student", "teacher"],
    "admin": ["student", "teacher", "admin"],
}

def get_access_filter(user_role: str) -> Filter:
    allowed_levels = ROLE_ACCESS_LEVELS.get(user_role, ["public"])
    return Filter(must=[FieldCondition(key="access_level", match=MatchAny(any=allowed_levels))])
```

**Bewertung:** ⭐ Perfekt implementiert!

---

### 4. Auth Middleware mit Public Endpoints

**Bestehende Implementation:**
```python
# src/middleware/scalekit_auth.py
def _is_public_endpoint(self, path: str) -> bool:
    public_paths = [
        "/.well-known/oauth-protected-resource",
        "/health",
        "/docs",
        "/openapi.json",
    ]
    return any(path.startswith(public_path) for public_path in public_paths)
```

**Bewertung:** ⭐ Korrekt - Discovery und Health sind public!

---

## 📋 ERFORDERLICHE ÄNDERUNGEN

### Fix 1: OAuth Router in `main.py` mounten

```python
# main.py - HINZUFÜGEN nach Zeile 49:

from src.auth.oauth_flow import create_oauth_router

# ... (nach app = FastAPI(...))

# ============================================================================
# OAuth Authentication Endpoints (Login, Callback, Logout)
# ============================================================================
if config.enable_auth:
    oauth_router = create_oauth_router(
        scalekit_env_url=config.scalekit_env_url,
        client_id=config.scalekit_client_id,
        client_secret=config.scalekit_client_secret,
        redirect_uri=f"https://leowiki-mcp.stream/auth/callback",
        frontend_callback_url=None,  # JSON response für API clients
    )
    app.include_router(oauth_router)
    logger.info("OAuth authentication endpoints registered: /auth/login, /auth/callback, /auth/logout")
```

---

### Fix 2: `env.example` vervollständigen

```env
# =============================================================================
# REQUIRED: OpenAI API Key
# =============================================================================
OPENAI_API_KEY=sk-proj-your-openai-api-key-here

# =============================================================================
# ScaleKit OAuth 2.1 Configuration (REQUIRED for production)
# =============================================================================
ENABLE_AUTH=true

# ScaleKit Environment (von ScaleKit Dashboard)
SCALEKIT_ENV_URL=https://leowikimcp.scalekit.dev
SCALEKIT_CLIENT_ID=skc_107036659593249282
SCALEKIT_CLIENT_SECRET=<DEIN_SECRET_HIER>

# MCP Server Identity (von ScaleKit MCP Server Dashboard)
SCALEKIT_MCP_SERVER_ID=res_107039365691081482
SCALEKIT_EXPECTED_AUDIENCE=https://leowiki-mcp.stream

# OAuth Protected Resource Metadata (JSON von ScaleKit Dashboard - EINZEILIG!)
# Kopiere den JSON-String aus dem ScaleKit Dashboard und füge ihn hier ein
SCALEKIT_PROTECTED_RESOURCE_METADATA={"resource":"res_107039365691081482","authorization_servers":["https://leowikimcp.scalekit.dev"],"bearer_methods_supported":["header"],"scopes_supported":["openid","profile","email"]}

# =============================================================================
# Other settings (configured in docker-compose.yml)
# =============================================================================
# VECTOR_DB_URL=http://qdrant:6334
# DEFAULT_COLLECTION=educational_content
```

---

### Fix 3: Public Endpoints erweitern

```python
# src/middleware/scalekit_auth.py - _is_public_endpoint erweitern:

def _is_public_endpoint(self, path: str) -> bool:
    public_paths = [
        "/.well-known/oauth-protected-resource",
        "/health",
        "/docs",
        "/openapi.json",
        "/auth/login",      # ← HINZUFÜGEN
        "/auth/callback",   # ← HINZUFÜGEN
        "/auth/logout",     # ← HINZUFÜGEN
    ]
    return any(path.startswith(public_path) for public_path in public_paths)
```

---

### Fix 4: Callback-URL in ScaleKit Dashboard

Stelle sicher, dass in ScaleKit diese Callback-URLs konfiguriert sind:
- `https://leowiki-mcp.stream/auth/callback`
- `http://localhost:8000/auth/callback` (für lokale Entwicklung)

---

## 📊 Vergleichstabelle: Repository vs. Plan

| Feature | Repository | Plan | Bewertung |
|---------|-----------|------|-----------|
| **OAuth Discovery** | ✅ `/.well-known/oauth-protected-resource` | ✅ Gleich | ✅ |
| **Token Validation** | ✅ ScaleKit SDK | ⚠️ Manuell mit PyJWT | Repository besser! |
| **Auth Middleware** | ✅ Vollständig | ✅ Vollständig | ✅ |
| **OAuth Login** | ⚠️ Code existiert, nicht gemountet | ✅ Vollständig | Fix nötig! |
| **OAuth Callback** | ⚠️ Code existiert, nicht gemountet | ✅ Vollständig | Fix nötig! |
| **RBAC** | ✅ Student/Teacher/Admin | ✅ Gleich | ✅ |
| **Health Endpoint** | ✅ `/health` | ✅ Gleich | ✅ |
| **Docker Setup** | ✅ Production-ready | ✅ Konzept | ✅ |
| **Environment Config** | ⚠️ Unvollständig | ✅ Vollständig | Fix nötig! |
| **Tests** | ✅ JWT Tests vorhanden | ⚠️ Konzept | ✅ |

---

## 🎯 Action Items (Priorität)

**P1** - KRITISCH (Authentifizierung funktioniert nicht ohne diese Fixes)

1. **OAuth Router mounten** in `main.py`
   - Importiere `create_oauth_router`
   - Registriere Router mit `app.include_router()`
   - ~10 Zeilen Code

2. **Environment-Variablen updaten**
   - Kopiere korrekte ScaleKit-Credentials
   - Füge `SCALEKIT_EXPECTED_AUDIENCE` hinzu
   - Füge `SCALEKIT_PROTECTED_RESOURCE_METADATA` hinzu

3. **Public Endpoints erweitern**
   - `/auth/*` als public markieren in `scalekit_auth.py`

**P2** - EMPFOHLEN

4. **ScaleKit Dashboard prüfen**
   - Callback-URL korrekt konfiguriert?
   - MCP Server korrekt registriert?

5. **Tests erweitern**
   - End-to-End OAuth Flow testen
   - Integration mit echten ScaleKit Tokens

**P3** - NICE-TO-HAVE

6. **Dokumentation aktualisieren**
   - README mit OAuth-Setup-Anleitung
   - Deployment-Guide für Auth

---

## 📝 Konkrete Code-Änderungen

### Datei: `main.py`

**Nach Zeile 49 hinzufügen:**

```python
# ============================================================================
# OAuth Authentication Router (Login, Callback, Logout)
# ============================================================================
if config.enable_auth:
    from src.auth.oauth_flow import create_oauth_router
    
    # Bestimme Callback-URL basierend auf Environment
    callback_url = os.getenv(
        "OAUTH_CALLBACK_URL",
        f"http://localhost:{config.server_port}/auth/callback"
    )
    
    oauth_router = create_oauth_router(
        scalekit_env_url=config.scalekit_env_url,
        client_id=config.scalekit_client_id,
        client_secret=config.scalekit_client_secret,
        redirect_uri=callback_url,
        frontend_callback_url=None,
    )
    app.include_router(oauth_router)
    logger.info(f"OAuth endpoints registered with callback: {callback_url}")
```

---

### Datei: `src/middleware/scalekit_auth.py`

**`_is_public_endpoint` Methode aktualisieren (Zeile 167-184):**

```python
def _is_public_endpoint(self, path: str) -> bool:
    """
    Check if an endpoint is public (does not require authentication).
    """
    public_paths = [
        "/.well-known/oauth-protected-resource",
        "/health",
        "/docs",
        "/openapi.json",
        "/auth/login",       # OAuth login initiation
        "/auth/callback",    # OAuth callback from ScaleKit
        "/auth/logout",      # Logout endpoint
    ]
    
    return any(path.startswith(public_path) for public_path in public_paths)
```

---

### Datei: `.env` (Production)

```env
# ScaleKit OAuth 2.1 - LeoWiki MCP Server
ENABLE_AUTH=true
SCALEKIT_ENV_URL=https://leowikimcp.scalekit.dev
SCALEKIT_CLIENT_ID=skc_107036659593249282
SCALEKIT_CLIENT_SECRET=<DEIN_SECRET>
SCALEKIT_MCP_SERVER_ID=res_107039365691081482
SCALEKIT_EXPECTED_AUDIENCE=https://leowiki-mcp.stream
SCALEKIT_PROTECTED_RESOURCE_METADATA={"resource":"res_107039365691081482","authorization_servers":["https://leowikimcp.scalekit.dev"],"bearer_methods_supported":["header"],"scopes_supported":["openid","profile","email"]}
OAUTH_CALLBACK_URL=https://leowiki-mcp.stream/auth/callback

# OpenAI
OPENAI_API_KEY=<DEIN_OPENAI_KEY>
```

---

## ✅ Fazit

**Das Repository hat eine gute Grundlage, aber es fehlen kritische Verbindungen:**

1. Der OAuth-Code existiert, ist aber nicht aktiviert
2. Die Environment-Konfiguration ist unvollständig
3. Nach den 3 Fixes sollte Phase 1 (Web Client Auth) funktionieren

**Empfehlung:**  
- ✅ Behalte die ScaleKit SDK Integration (besser als unser Plan)
- ✅ Behalte die RBAC-Implementation
- 🔧 Führe die 3 kritischen Fixes durch
- 🧪 Teste den kompletten OAuth-Flow

---

---

## ✅ Update: Pläne angepasst

Die Pläne wurden aktualisiert, um die bessere ScaleKit SDK Variante zu verwenden:

- **`PHASE_1_WEB_CLIENT_AUTH.md`**: Jetzt mit ScaleKit SDK statt manueller JWT-Validierung
- **`PHASE_2_PROXY_BRIDGE_AUTH.md`**: Kongruent mit Phase 1

Beide Pläne sind jetzt vollständig kompatibel mit dem bestehenden Repository.

---

*Analyse erstellt: 19. Januar 2026*
*Pläne aktualisiert: 19. Januar 2026*
*Repository: <https://github.com/Imre7777/mcp-diploma-thesis-final>*
