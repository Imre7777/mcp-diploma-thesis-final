# 🔧 VOLLSTÄNDIGE MCP-SERVER KONFIGURATION

## Environment Variables (`.env`)

```env
# ============================================
# SCALEKIT OAUTH CONFIGURATION
# ============================================

# Aus Screenshot 3 - API Credentials
SCALEKIT_ENVIRONMENT_URL=https://leowikimcp.scalekit.dev
SCALEKIT_CLIENT_ID=skc_107036659593249282
SCALEKIT_CLIENT_SECRET=<dein-client-secret-aus-scalekit>

# Aus Screenshot 2 - MCP Server Configuration
# WICHTIG: Muss EXAKT mit Server URL in Scalekit übereinstimmen!
SCALEKIT_RESOURCE_ID=https://leowiki-mcp.stream/

# Alternative: Wenn du die auto-generierte Resource ID verwendest
# SCALEKIT_RESOURCE_ID=res_107039365691081482

# ============================================
# MCP SERVER CONFIGURATION
# ============================================

# Dein MCP Server Endpoint (was Claude als URL bekommt)
MCP_SERVER_URL=https://leowiki-mcp.stream
MCP_ENDPOINT_PATH=/mcp

# ============================================
# LEOWIKI API (für eure bestehende Logik)
# ============================================
LEOWIKI_API_URL=<eure-leowiki-api-url>
LEOWIKI_API_KEY=<falls-benötigt>
```

---

### Pflicht-Endpoints die dein MCP Server bereitstellen MUSS

#### 1. OAuth Protected Resource Metadata (`/.well-known/oauth-protected-resource`)

```typescript
// PFLICHT-ENDPOINT für MCP Client Discovery
app.get('/.well-known/oauth-protected-resource', (req, res) => {
  res.json({
    // Authorization Server URL - Format: {SCALEKIT_ENV_URL}/resources/{RESOURCE_ID}
    "authorization_servers": [
      "https://leowikimcp.scalekit.dev/resources/res_107039365691081482"
    ],
    
    // Wie Tokens übermittelt werden
    "bearer_methods_supported": ["header"],
    
    // MUSS mit Server URL in Scalekit Dashboard übereinstimmen!
    "resource": "https://leowiki-mcp.stream/",
    
    // Optional: Dokumentation
    "resource_documentation": "https://leowiki-mcp.stream/docs",
    
    // Definierte Scopes (falls in Scalekit konfiguriert)
    "scopes_supported": ["wiki:read", "wiki:search"]
  });
});
```

#### 2. MCP Endpoint (`/mcp`)

```typescript
// Haupt-MCP-Endpoint - POST und GET müssen unterstützt werden
app.post('/mcp', authMiddleware, async (req, res) => {
  // MCP JSON-RPC Handling
});

app.get('/mcp', authMiddleware, async (req, res) => {
  // SSE Stream für Server-to-Client Nachrichten
});

// Optional: Session Termination
app.delete('/mcp', authMiddleware, async (req, res) => {
  // Session beenden
});
```

---

### Token Validation Middleware (KRITISCH!)

```typescript
import { Scalekit } from '@scalekit-sdk/node';

// Scalekit Client initialisieren
const scalekit = new Scalekit(
  process.env.SCALEKIT_ENVIRONMENT_URL,  // https://leowikimcp.scalekit.dev
  process.env.SCALEKIT_CLIENT_ID,         // skc_107036659593249282
  process.env.SCALEKIT_CLIENT_SECRET      // Dein Secret
);

// KRITISCH: Muss EXAKT mit Server URL in Scalekit übereinstimmen!
const RESOURCE_ID = process.env.SCALEKIT_RESOURCE_ID; // https://leowiki-mcp.stream/

// Metadata Endpoint URL für WWW-Authenticate Header
const METADATA_ENDPOINT = 'https://leowiki-mcp.stream/.well-known/oauth-protected-resource';

// WWW-Authenticate Header für 401 Responses
const WWW_AUTHENTICATE = {
  key: 'WWW-Authenticate',
  value: `Bearer realm="OAuth", resource_metadata="${METADATA_ENDPOINT}"`
};

// Auth Middleware
export async function authMiddleware(req, res, next) {
  try {
    // /.well-known Endpoints sind PUBLIC!
    if (req.path.includes('.well-known')) {
      return next();
    }

    // Bearer Token extrahieren
    const authHeader = req.headers['authorization'];
    const token = authHeader?.startsWith('Bearer ')
      ? authHeader.split('Bearer ')[1]?.trim()
      : null;

    if (!token) {
      return res
        .status(401)
        .set(WWW_AUTHENTICATE.key, WWW_AUTHENTICATE.value)
        .json({ error: 'unauthorized', error_description: 'Bearer token required' });
    }

    // Token validieren - KRITISCH: audience muss EXAKT matchen!
    await scalekit.validateToken(token, {
      issuer: process.env.SCALEKIT_ENVIRONMENT_URL,
      audience: [RESOURCE_ID]
    });

    next();
  } catch (err) {
    console.error('Token validation failed:', err);
    return res
      .status(401)
      .set(WWW_AUTHENTICATE.key, WWW_AUTHENTICATE.value)
      .json({ error: 'invalid_token', error_description: 'Token validation failed' });
  }
}
```

---

### Komplette Checkliste

#### Scalekit Dashboard ✅

| Setting        | Wert                                       | Status |
| -------------- | ------------------------------------------ | ------ |
| Redirect URL 1 | `https://claude.ai/api/mcp/auth_callback`  | ✅      |
| Redirect URL 2 | `https://claude.com/api/mcp/auth_callback` | ✅      |
| Server URL     | `https://leowiki-mcp.stream/`              | ✅      |
| DCR aktiviert  | Ja                                         | ✅      |
| CIMD aktiviert | Ja                                         | ✅      |

#### MCP Server Code 🔧

| Komponente        | Pfad/Wert                                   | Pflicht   |
| ----------------- | ------------------------------------------- | --------- |
| Metadata Endpoint | `GET /.well-known/oauth-protected-resource` | ✅ PFLICHT |
| MCP Endpoint POST | `POST /mcp`                                 | ✅ PFLICHT |
| MCP Endpoint GET  | `GET /mcp`                                  | ✅ PFLICHT |
| Auth Middleware   | Auf allen `/mcp` Routen                     | ✅ PFLICHT |
| CORS Headers      | Für Claude-Domains                          | ✅ PFLICHT |

#### Environment Variables 🔧

| Variable                   | Wert                              | Pflicht   |
| -------------------------- | --------------------------------- | --------- |
| `SCALEKIT_ENVIRONMENT_URL` | `https://leowikimcp.scalekit.dev` | ✅ PFLICHT |
| `SCALEKIT_CLIENT_ID`       | `skc_107036659593249282`          | ✅ PFLICHT |
| `SCALEKIT_CLIENT_SECRET`   | `<aus Dashboard>`                 | ✅ PFLICHT |
| `SCALEKIT_RESOURCE_ID`     | `https://leowiki-mcp.stream/`     | ✅ PFLICHT |

#### Claude.ai Connector Einstellung 🔧

| Setting        | Wert                             |
| -------------- | -------------------------------- |
| MCP Server URL | `https://leowiki-mcp.stream/mcp` |

---

### CORS Konfiguration (KRITISCH!)

```typescript
import cors from 'cors';

app.use(cors({
  origin: [
    'https://claude.ai',
    'https://claude.com',
    'http://localhost:3000'  // Für lokales Testing
  ],
  methods: ['GET', 'POST', 'DELETE', 'OPTIONS'],
  allowedHeaders: [
    'Content-Type',
    'Accept',
    'Authorization',
    'Mcp-Session-Id',
    'Last-Event-ID'
  ],
  exposedHeaders: [
    'Content-Type',
    'Authorization',
    'Mcp-Session-Id'
  ],
  credentials: true
}));
```

---

### Zusammenfassung der URLs

| Zweck                                   | URL                                                                |
| --------------------------------------- | ------------------------------------------------------------------ |
| **In Claude Connector eingeben**        | `https://leowiki-mcp.stream/mcp`                                   |
| **Server URL in Scalekit**              | `https://leowiki-mcp.stream/`                                      |
| **Scalekit Environment**                | `https://leowikimcp.scalekit.dev`                                  |
| **Authorization Server (für Metadata)** | `https://leowikimcp.scalekit.dev/resources/res_107039365691081482` |
| **Token Audience (RESOURCE_ID)**        | `https://leowiki-mcp.stream/`                                      |

Deine Scalekit-Konfiguration sieht gut aus! 🎉 Der nächste Schritt ist sicherzustellen, dass dein MCP-Server-Code alle oben genannten Endpoints und die Token-Validierung korrekt implementiert.
