# 🔐 MCP Server OAuth 2.1 Integration Plan

## Für: LeoWiki MCP Server
## Stand: 08. Januar 2026

---

> ⚠️ **CRITICAL: CLAUDE DESKTOP COMPATIBILITY WARNING**
> 
> **This OAuth 2.1 integration plan does NOT work with Claude Desktop!**
> 
> **Why:** Claude Desktop runs MCP servers via STDIO (standard input/output)
> without a web browser. OAuth 2.1 requires HTTP redirects, login pages,
> and callback URLs - none of which are available in STDIO mode.
> 
> **This plan is for:**
> - ✅ Web-based MCP clients (MCP Inspector)
> - ✅ HTTP transport mode
> - ✅ Custom web applications
> - ✅ API integrations
> 
> **For Claude Desktop users:**
> - Use `ENABLE_AUTH=false` in `.env`
> - OR implement static token authentication
> - OR wait for MCP protocol OAuth support
> 
> **Full explanation:** See `CLAUDE_DESKTOP_AUTH_LIMITATION.md`

---

## 📋 Übersicht

Dieses Dokument beschreibt alle Schritte, die auf **MCP Server Seite** notwendig sind, um die OAuth 2.1 Authentifizierung mit ScaleKit vollständig zu implementieren.

### Was bereits konfiguriert ist (ScaleKit):
- ✅ MCP Server registriert
- ✅ OAuth 2.1 Client Credentials erstellt
- ✅ Rollen (admin, teacher, student) angelegt
- ✅ Benutzer angelegt und aktiviert
- ✅ Callback URLs konfiguriert

### Was noch zu tun ist (MCP Server):
- ⏳ OAuth 2.1 Authorization Code Flow implementieren
- ⏳ Token Exchange Endpoint
- ⏳ JWT Token Validierung
- ⏳ Session Management
- ⏳ Rollenbasierte Zugriffskontrolle

---

## 🏗️ Architektur

```
┌──────────────────────────────────────────────────────────────────────┐
│                         AUTHENTIFIZIERUNGS-FLOW                       │
└──────────────────────────────────────────────────────────────────────┘

┌─────────┐    1. Request    ┌─────────────┐    2. Redirect    ┌───────────┐
│  User   │ ───────────────▶ │ MCP Server  │ ────────────────▶ │ ScaleKit  │
│ Browser │                  │             │                   │   Auth    │
└─────────┘                  └─────────────┘                   └───────────┘
     │                              ▲                                │
     │                              │                                │
     │         5. Protected        │ 4. Token                       │
     │            Resource         │    Exchange                    │
     │◀─────────────────────────────                                │
     │                              │                                │
     │                              │                                │
     └──────────────────────────────┴────────────────────────────────┘
                           3. Callback mit Auth Code
```

---

## 🔑 ScaleKit Credentials

```env
# Diese Werte sind in SCALEKIT_MCP_CREDENTIALS.md dokumentiert

SCALEKIT_ENV_URL=https://leowikimcp.scalekit.dev
SCALEKIT_CLIENT_ID=skc_107036659593249282
SCALEKIT_CLIENT_SECRET=<aus_credentials_datei>

# MCP Server URLs
# ⚠️ WICHTIG: Bei FastMCP NUR die Base-URL verwenden (OHNE /mcp am Ende!)
MCP_SERVER_URL=https://leowiki-mcp.stream
MCP_CALLBACK_URL=https://leowiki-mcp.stream/callback

# Für lokale Entwicklung
MCP_CALLBACK_URL_LOCAL=http://localhost:3000/callback
```

> ⚠️ **FastMCP Hinweis**: Bei Verwendung von FastMCP muss in ScaleKit die **Base-URL** 
> (`https://leowiki-mcp.stream`) eingetragen werden, **NICHT** `https://leowiki-mcp.stream/mcp`.
> FastMCP fügt den `/mcp` Pfad automatisch hinzu!

---

## 📍 Endpoints die implementiert werden müssen

> ⚠️ **FastMCP URL-Schema**: Bei FastMCP ist die Base-URL `https://leowiki-mcp.stream`.
> Der `/mcp` Endpoint wird von FastMCP automatisch bereitgestellt.

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/auth/login` | GET | Startet OAuth Flow, redirect zu ScaleKit |
| `/callback` | GET | Empfängt Auth Code, tauscht gegen Token |
| `/auth/logout` | GET/POST | Beendet Session |
| `/auth/me` | GET | Gibt aktuellen User zurück |
| `/mcp` | * | FastMCP Endpoint (automatisch) |
| `/*` | * | Alle geschützten Ressourcen |

---

## 🔄 Phase 1: OAuth 2.1 Authorization Code Flow mit PKCE

### 1.1 Login Endpoint implementieren

**Endpoint:** `GET /auth/login`

**Aufgabe:** Generiert PKCE Challenge und leitet zu ScaleKit weiter.

```javascript
// Node.js/Express Beispiel (FastMCP kompatibel)
const crypto = require('crypto');

// PKCE Helper Funktionen
function generateCodeVerifier() {
  return crypto.randomBytes(32).toString('base64url');
}

function generateCodeChallenge(verifier) {
  return crypto
    .createHash('sha256')
    .update(verifier)
    .digest('base64url');
}

// Login Route - OHNE /mcp Prefix (FastMCP)
app.get('/auth/login', (req, res) => {
  // 1. PKCE Code Verifier generieren
  const codeVerifier = generateCodeVerifier();
  const codeChallenge = generateCodeChallenge(codeVerifier);
  
  // 2. State für CSRF-Schutz generieren
  const state = crypto.randomBytes(16).toString('hex');
  
  // 3. In Session speichern (für Callback)
  req.session.oauth = {
    codeVerifier,
    state,
    returnTo: req.query.returnTo || '/'
  };
  
  // 4. Authorization URL bauen
  const authUrl = new URL('https://leowikimcp.scalekit.dev/oauth/authorize');
  authUrl.searchParams.set('client_id', process.env.SCALEKIT_CLIENT_ID);
  authUrl.searchParams.set('redirect_uri', process.env.MCP_CALLBACK_URL); // https://leowiki-mcp.stream/callback
  authUrl.searchParams.set('response_type', 'code');
  authUrl.searchParams.set('scope', 'openid profile email');
  authUrl.searchParams.set('state', state);
  authUrl.searchParams.set('code_challenge', codeChallenge);
  authUrl.searchParams.set('code_challenge_method', 'S256');
  
  // 5. Redirect zu ScaleKit
  res.redirect(authUrl.toString());
});
```

```python
# Python/FastAPI Beispiel (FastMCP kompatibel)
import secrets
import hashlib
import base64
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

app = FastAPI()

def generate_code_verifier():
    return secrets.token_urlsafe(32)

def generate_code_challenge(verifier: str):
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode()

# Login Route - OHNE /mcp Prefix (FastMCP)
@app.get("/auth/login")
async def login(request: Request, return_to: str = "/"):
    # 1. PKCE generieren
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    
    # 2. State generieren
    state = secrets.token_hex(16)
    
    # 3. In Session speichern
    request.session["oauth"] = {
        "code_verifier": code_verifier,
        "state": state,
        "return_to": return_to
    }
    
    # 4. Authorization URL
    # Callback URL: https://leowiki-mcp.stream/callback (OHNE /mcp!)
    params = {
        "client_id": SCALEKIT_CLIENT_ID,
        "redirect_uri": MCP_CALLBACK_URL,
        "response_type": "code",
        "scope": "openid profile email",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    
    auth_url = f"https://leowikimcp.scalekit.dev/oauth/authorize?{urlencode(params)}"
    return RedirectResponse(auth_url)
```

---

### 1.2 Callback Endpoint implementieren

**Endpoint:** `GET /callback`

**Aufgabe:** Empfängt Authorization Code und tauscht ihn gegen Tokens.

```javascript
// Node.js/Express Beispiel (FastMCP kompatibel)
// Callback URL: https://leowiki-mcp.stream/callback (OHNE /mcp!)
app.get('/callback', async (req, res) => {
  try {
    const { code, state, error } = req.query;
    
    // 1. Error Check
    if (error) {
      console.error('OAuth Error:', error);
      return res.redirect('/auth/error?message=' + error);
    }
    
    // 2. State validieren (CSRF-Schutz)
    if (!req.session.oauth || state !== req.session.oauth.state) {
      return res.status(400).send('Invalid state parameter');
    }
    
    const { codeVerifier, returnTo } = req.session.oauth;
    
    // 3. Token Exchange
    const tokenResponse = await fetch('https://leowikimcp.scalekit.dev/oauth/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        client_id: process.env.SCALEKIT_CLIENT_ID,
        client_secret: process.env.SCALEKIT_CLIENT_SECRET,
        code: code,
        redirect_uri: process.env.MCP_CALLBACK_URL, // https://leowiki-mcp.stream/callback
        code_verifier: codeVerifier,
      }),
    });
    
    if (!tokenResponse.ok) {
      const errorData = await tokenResponse.text();
      console.error('Token Exchange Error:', errorData);
      return res.redirect('/auth/error?message=token_exchange_failed');
    }
    
    const tokens = await tokenResponse.json();
    
    // 4. Tokens in Session speichern
    req.session.tokens = {
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      idToken: tokens.id_token,
      expiresAt: Date.now() + (tokens.expires_in * 1000)
    };
    
    // 5. User Info aus ID Token extrahieren (oder /userinfo aufrufen)
    const userInfo = decodeIdToken(tokens.id_token);
    req.session.user = {
      id: userInfo.sub,
      email: userInfo.email,
      name: userInfo.name,
      role: userInfo.role || 'member',
      orgId: userInfo.org_id
    };
    
    // 6. OAuth Session Daten löschen
    delete req.session.oauth;
    
    // 7. Redirect zur ursprünglichen Seite
    res.redirect(returnTo || '/');
    
  } catch (error) {
    console.error('Callback Error:', error);
    res.redirect('/auth/error?message=callback_failed');
  }
});

// Helper: ID Token dekodieren (ohne Validierung - nur für Demo)
function decodeIdToken(idToken) {
  const payload = idToken.split('.')[1];
  return JSON.parse(Buffer.from(payload, 'base64url').toString());
}
```

```python
# Python/FastAPI Beispiel (FastMCP kompatibel)
import httpx
import jwt

# Callback URL: https://leowiki-mcp.stream/callback (OHNE /mcp!)
@app.get("/callback")
async def callback(request: Request, code: str = None, state: str = None, error: str = None):
    # 1. Error Check
    if error:
        return RedirectResponse(f"/auth/error?message={error}")
    
    # 2. State validieren
    oauth_data = request.session.get("oauth")
    if not oauth_data or state != oauth_data["state"]:
        raise HTTPException(400, "Invalid state")
    
    code_verifier = oauth_data["code_verifier"]
    return_to = oauth_data["return_to"]
    
    # 3. Token Exchange
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://leowikimcp.scalekit.dev/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": SCALEKIT_CLIENT_ID,
                "client_secret": SCALEKIT_CLIENT_SECRET,
                "code": code,
                "redirect_uri": MCP_CALLBACK_URL,  # https://leowiki-mcp.stream/callback
                "code_verifier": code_verifier,
            }
        )
    
    if token_response.status_code != 200:
        return RedirectResponse("/auth/error?message=token_exchange_failed")
    
    tokens = token_response.json()
    
    # 4. Session speichern
    request.session["tokens"] = {
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token"),
        "id_token": tokens["id_token"],
        "expires_at": time.time() + tokens["expires_in"]
    }
    
    # 5. User Info extrahieren
    id_token_payload = jwt.decode(tokens["id_token"], options={"verify_signature": False})
    request.session["user"] = {
        "id": id_token_payload["sub"],
        "email": id_token_payload.get("email"),
        "name": id_token_payload.get("name"),
        "role": id_token_payload.get("role", "member")
    }
    
    # 6. Cleanup & Redirect
    del request.session["oauth"]
    return RedirectResponse(return_to)
```

---

## 🔒 Phase 2: JWT Token Validierung

### 2.1 JWKS (JSON Web Key Set) laden

ScaleKit stellt öffentliche Schlüssel bereit unter:
```
https://leowikimcp.scalekit.dev/.well-known/jwks.json
```

```javascript
// Node.js mit jose Library
const jose = require('jose');

let jwks = null;
let jwksLastFetch = 0;
const JWKS_CACHE_TTL = 3600000; // 1 Stunde

async function getJWKS() {
  const now = Date.now();
  if (!jwks || (now - jwksLastFetch) > JWKS_CACHE_TTL) {
    jwks = jose.createRemoteJWKSet(
      new URL('https://leowikimcp.scalekit.dev/.well-known/jwks.json')
    );
    jwksLastFetch = now;
  }
  return jwks;
}

async function verifyToken(token) {
  try {
    const JWKS = await getJWKS();
    const { payload } = await jose.jwtVerify(token, JWKS, {
      issuer: 'https://leowikimcp.scalekit.dev',
      audience: process.env.SCALEKIT_CLIENT_ID,
    });
    return payload;
  } catch (error) {
    console.error('Token Verification Error:', error.message);
    return null;
  }
}
```

```python
# Python mit PyJWT und jwcrypto
import jwt
from jwt import PyJWKClient

jwks_client = PyJWKClient("https://leowikimcp.scalekit.dev/.well-known/jwks.json")

def verify_token(token: str):
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=SCALEKIT_CLIENT_ID,
            issuer="https://leowikimcp.scalekit.dev"
        )
        return payload
    except jwt.exceptions.InvalidTokenError as e:
        print(f"Token verification error: {e}")
        return None
```

---

## 🛡️ Phase 3: Auth Middleware

### 3.1 Authentication Middleware

```javascript
// Node.js/Express Middleware (FastMCP kompatibel)
function requireAuth(req, res, next) {
  // 1. Session Check
  if (!req.session.user || !req.session.tokens) {
    // Für API: 401 zurückgeben
    if (req.path.startsWith('/api/')) {
      return res.status(401).json({ error: 'Unauthorized' });
    }
    // Für Browser: Redirect zu Login
    return res.redirect(`/auth/login?returnTo=${encodeURIComponent(req.originalUrl)}`);
  }
  
  // 2. Token Expiry Check
  if (Date.now() >= req.session.tokens.expiresAt) {
    // TODO: Token Refresh implementieren
    delete req.session.user;
    delete req.session.tokens;
    return res.redirect(`/auth/login?returnTo=${encodeURIComponent(req.originalUrl)}`);
  }
  
  // 3. User an Request anhängen
  req.user = req.session.user;
  next();
}

// Verwendung - FastMCP stellt /mcp automatisch bereit
// Schütze andere Routen:
app.use('/api', requireAuth);
// ODER für spezifische Routen:
app.get('/protected-resource', requireAuth, (req, res) => {
  res.json({ user: req.user });
});
```

```python
# Python/FastAPI Dependency (FastMCP kompatibel)
from fastapi import Depends, HTTPException, Request

async def get_current_user(request: Request):
    user = request.session.get("user")
    tokens = request.session.get("tokens")
    
    if not user or not tokens:
        raise HTTPException(401, "Not authenticated")
    
    # Token Expiry Check
    if time.time() >= tokens["expires_at"]:
        raise HTTPException(401, "Token expired")
    
    return user

# Verwendung - FastMCP stellt /mcp automatisch bereit
@app.get("/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    return {"user": user}
```

---

## 👥 Phase 4: Rollenbasierte Zugriffskontrolle (RBAC)

### 4.1 Rollen-Middleware

```javascript
// Node.js Role Check Middleware
function requireRole(...allowedRoles) {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({ error: 'Unauthorized' });
    }
    
    const userRole = req.user.role;
    
    if (!allowedRoles.includes(userRole)) {
      return res.status(403).json({ 
        error: 'Forbidden',
        message: `Role '${userRole}' is not allowed. Required: ${allowedRoles.join(' or ')}`
      });
    }
    
    next();
  };
}

// Verwendung (FastMCP kompatibel - ohne /mcp Prefix)
// Nur Admins
app.delete('/api/users/:id', requireAuth, requireRole('admin'), deleteUser);

// Admins und Teachers
app.post('/api/content', requireAuth, requireRole('admin', 'teacher'), createContent);

// Alle authentifizierten User
app.get('/api/content', requireAuth, getContent);
```

```python
# Python/FastAPI Role Check
def require_role(*allowed_roles):
    async def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(
                403, 
                f"Role '{user['role']}' not allowed. Required: {' or '.join(allowed_roles)}"
            )
        return user
    return role_checker

# Verwendung (FastMCP kompatibel - ohne /mcp Prefix)
@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str, user: dict = Depends(require_role("admin"))):
    pass

@app.post("/api/content")
async def create_content(user: dict = Depends(require_role("admin", "teacher"))):
    pass
```

### 4.2 Berechtigungsmatrix

| Aktion | admin | teacher | student |
|--------|-------|---------|---------|
| Wiki lesen | ✅ | ✅ | ✅ |
| Wiki bearbeiten | ✅ | ✅ | ❌ |
| Wiki erstellen | ✅ | ✅ | ❌ |
| Wiki löschen | ✅ | ❌ | ❌ |
| User verwalten | ✅ | ❌ | ❌ |
| Einstellungen | ✅ | ❌ | ❌ |
| Eigene Beiträge | ✅ | ✅ | ✅ |

---

## 🔄 Phase 5: Token Refresh (Optional aber empfohlen)

```javascript
// Token Refresh Endpoint (FastMCP kompatibel)
app.post('/auth/refresh', async (req, res) => {
  if (!req.session.tokens?.refreshToken) {
    return res.status(401).json({ error: 'No refresh token' });
  }
  
  try {
    const response = await fetch('https://leowikimcp.scalekit.dev/oauth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'refresh_token',
        client_id: process.env.SCALEKIT_CLIENT_ID,
        client_secret: process.env.SCALEKIT_CLIENT_SECRET,
        refresh_token: req.session.tokens.refreshToken,
      }),
    });
    
    if (!response.ok) {
      // Refresh Token invalid - User muss neu einloggen
      delete req.session.tokens;
      delete req.session.user;
      return res.status(401).json({ error: 'Refresh failed' });
    }
    
    const tokens = await response.json();
    req.session.tokens = {
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token || req.session.tokens.refreshToken,
      idToken: tokens.id_token,
      expiresAt: Date.now() + (tokens.expires_in * 1000)
    };
    
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: 'Refresh error' });
  }
});
```

---

## 🚪 Phase 6: Logout

```javascript
// Logout Endpoint (FastMCP kompatibel)
app.get('/auth/logout', (req, res) => {
  // 1. Session löschen
  req.session.destroy((err) => {
    if (err) {
      console.error('Session destroy error:', err);
    }
    
    // 2. Optional: ScaleKit Logout (Single Sign-Out)
    // const logoutUrl = `https://leowikimcp.scalekit.dev/oauth/logout?client_id=${process.env.SCALEKIT_CLIENT_ID}&post_logout_redirect_uri=${encodeURIComponent('https://leowiki-mcp.stream')}`;
    // res.redirect(logoutUrl);
    
    // 3. Oder einfach zur Startseite
    res.redirect('/');
  });
});
```

---

## 📁 Projekt-Struktur (Empfehlung für FastMCP)

```
mcp-server/
├── src/
│   ├── auth/
│   │   ├── oauth.js          # OAuth Flow (Login, Callback)
│   │   ├── middleware.js     # Auth & Role Middleware
│   │   ├── token.js          # JWT Validation
│   │   └── session.js        # Session Management
│   ├── routes/
│   │   ├── auth.routes.js    # /auth/* (Login, Logout, Callback)
│   │   └── api.routes.js     # /api/* (geschützte API Routen)
│   ├── mcp/
│   │   └── server.js         # FastMCP Server Setup (/mcp automatisch)
│   ├── config/
│   │   └── scalekit.js       # ScaleKit Config
│   └── app.js
├── .env
├── .env.example
└── package.json
```

> ⚠️ **FastMCP Hinweis**: Der `/mcp` Endpoint wird von FastMCP automatisch bereitgestellt.
> Du musst ihn NICHT manuell implementieren!

---

## ✅ Checkliste zur Implementierung

### Setup
- [ ] Environment Variables konfigurieren
- [ ] Session Store einrichten (Redis empfohlen für Production)
- [ ] HTTPS konfigurieren
- [ ] FastMCP installieren und konfigurieren

### OAuth Flow (FastMCP - OHNE /mcp Prefix!)
- [ ] `/auth/login` - Redirect zu ScaleKit
- [ ] `/callback` - Token Exchange
- [ ] PKCE implementiert
- [ ] State Parameter für CSRF-Schutz

### Token Handling
- [ ] JWT Validierung mit JWKS
- [ ] Token Expiry Check
- [ ] Token Refresh (optional)

### Authorization
- [ ] Auth Middleware für geschützte Routen
- [ ] Role-based Access Control
- [ ] Error Handling (401, 403)

### User Experience
- [ ] Login Redirect nach Auth
- [ ] Logout Endpoint `/auth/logout`
- [ ] User Info Endpoint `/auth/me`

### FastMCP Spezifisch
- [ ] Server URL in ScaleKit: `https://leowiki-mcp.stream` (OHNE /mcp!)
- [ ] Callback URL in ScaleKit: `https://leowiki-mcp.stream/callback`
- [ ] `/mcp` Endpoint wird automatisch bereitgestellt

---

## 🧪 Test-Szenarios

### 1. Login Flow testen
```bash
# Browser öffnen (FastMCP - OHNE /mcp!)
open https://leowiki-mcp.stream/auth/login

# Erwartung:
# 1. Redirect zu ScaleKit Login
# 2. Login mit Test-User (z.B. leowikidev@gmail.com / student!01pass)
# 3. Redirect zurück zu /callback (NICHT /mcp/callback!)
# 4. Session erstellt, User eingeloggt
```

### 2. Protected Route testen
```bash
# Ohne Auth (FastMCP - OHNE /mcp!)
curl https://leowiki-mcp.stream/api/protected
# Erwartung: 401 Unauthorized

# Mit Auth (Session Cookie)
curl -b "session=..." https://leowiki-mcp.stream/api/protected
# Erwartung: 200 OK mit User Daten
```

### 3. FastMCP Endpoint testen
```bash
# MCP Endpoint (automatisch von FastMCP bereitgestellt)
curl https://leowiki-mcp.stream/mcp
# Erwartung: FastMCP Response
```

### 4. Role Check testen
```bash
# Als Student auf Admin-Route
# Erwartung: 403 Forbidden

# Als Admin auf Admin-Route
# Erwartung: 200 OK
```

---

## 🆘 Troubleshooting

| Problem | Lösung |
|---------|--------|
| "Invalid state" Error | Session wird nicht korrekt gespeichert. Prüfe Session-Config |
| "Token exchange failed" | Client Secret prüfen, Callback URL muss exakt matchen |
| "Invalid signature" | JWKS URL prüfen, Token könnte abgelaufen sein |
| CORS Fehler | CORS für ScaleKit Domain erlauben |
| Cookie nicht gesetzt | `secure: true` nur mit HTTPS, `sameSite` prüfen |

---

## 📞 Support & Ressourcen

- **ScaleKit Dashboard**: https://app.scalekit.com/ws/environments/env_107036658938937858
- **ScaleKit Docs**: https://docs.scalekit.com
- **Credentials**: `SCALEKIT_MCP_CREDENTIALS.md` (lokal)

---

## 🏁 Quick Start (Copy & Paste)

### Minimale .env Datei:
```env
# ScaleKit
SCALEKIT_ENV_URL=https://leowikimcp.scalekit.dev
SCALEKIT_CLIENT_ID=skc_107036659593249282
SCALEKIT_CLIENT_SECRET=<SECRET_AUS_CREDENTIALS_DATEI>

# Server (FastMCP - OHNE /mcp in URLs!)
MCP_SERVER_URL=https://leowiki-mcp.stream
MCP_CALLBACK_URL=https://leowiki-mcp.stream/callback
SESSION_SECRET=<ZUFÄLLIGER_STRING_GENERIEREN>

# Für lokale Entwicklung
# MCP_CALLBACK_URL=http://localhost:3000/callback
```

> ⚠️ **WICHTIG für FastMCP**: Die Callback-URL ist `/callback`, NICHT `/mcp/callback`!

### Minimale Dependencies (Node.js):
```json
{
  "dependencies": {
    "express": "^4.18.0",
    "express-session": "^1.17.0",
    "jose": "^5.0.0",
    "dotenv": "^16.0.0"
  }
}
```

### Minimale Dependencies (Python):
```txt
fastapi>=0.100.0
uvicorn>=0.23.0
httpx>=0.24.0
PyJWT>=2.8.0
python-jose>=3.3.0
itsdangerous>=2.1.0
```

---

*Dokument erstellt: 08. Januar 2026*
*Autor: AI Assistant*
*Version: 1.0*
