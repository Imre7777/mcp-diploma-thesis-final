# 🔐 OAuth 2.1 & RBAC Complete Guide - MCP Educational Server

**Vollständiger Leitfaden zur Authentifizierung und Rollenverwaltung**

**Datum:** 06. Januar 2026  
**Server:** https://leowiki-mcp.stream  
**OAuth Provider:** Scalekit (https://mcpeduauth.scalekit.dev)

---

## 📋 Inhaltsverzeichnis

1. [Überblick](#überblick)
2. [Die OAuth 2.1 Architektur](#die-oauth-21-architektur)
3. [Rollenbasierte Zugriffskontrolle (RBAC)](#rollenbasierte-zugriffskontrolle-rbac)
4. [Der komplette Authentifizierungs-Flow](#der-komplette-authentifizierungs-flow)
5. [JWT Token mit Rollen](#jwt-token-mit-rollen)
6. [Token-Speicherung und Management](#token-speicherung-und-management)
7. [Token-Verwendung bei MCP-Requests](#token-verwendung-bei-mcp-requests)
8. [Unterscheidung: Student vs. Teacher](#unterscheidung-student-vs-teacher)
9. [Claude Desktop Konfiguration](#claude-desktop-konfiguration)
10. [User-Verwaltung in Scalekit](#user-verwaltung-in-scalekit)
11. [Praktisches Beispiel: HTL Leonding](#praktisches-beispiel-htl-leonding)
12. [Testing und Troubleshooting](#testing-und-troubleshooting)

---

## 🎯 Überblick

Das MCP Educational Server System verwendet **OAuth 2.1** mit **Scalekit** als Authorization Server und implementiert **Role-Based Access Control (RBAC)** für die Unterscheidung zwischen Students, Teachers und Admins.

### Kernprinzip

**Die Rolle wird NICHT in der Claude Desktop Config gespeichert!**  
Die Rolle kommt vom **User-Account** in Scalekit, der beim **Login** automatisch identifiziert wird.

### Key Components

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  Claude Desktop (MCP Client)                            │
│  ├─ config.json: Server URL + OAuth Discovery          │
│  └─ Token Storage: Verschlüsselte JWT Tokens           │
│                                                          │
└────────────────┬─────────────────────────────────────────┘
                 │
                 │ OAuth 2.1 Flow
                 ▼
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  Scalekit Authorization Server                          │
│  ├─ User Database: Email, Password, Roles               │
│  ├─ Login Page: Authentifizierung                       │
│  └─ JWT Token Generation: Mit Role Claims               │
│                                                          │
└────────────────┬─────────────────────────────────────────┘
                 │
                 │ JWT Token mit Rolle
                 ▼
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  MCP Educational Server (Raspberry Pi)                   │
│  ├─ Token Validation: Scalekit SDK                      │
│  ├─ Role Extraction: Aus JWT Claims                     │
│  └─ RBAC Filtering: Basierend auf Rolle                 │
│                                                          │
└────────────────┬─────────────────────────────────────────┘
                 │
                 │ Filtered Results
                 ▼
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  Qdrant Vector Database                                  │
│  ├─ Dokumente mit access_level: student/teacher/admin   │
│  └─ Filter-Query basierend auf User-Rolle               │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 🔐 Die OAuth 2.1 Architektur

### Protected Resource Pattern

Ihr MCP Server implementiert das **OAuth 2.1 Protected Resource Pattern**:

```
┌──────────────────┐
│  Claude Desktop  │ ← OAuth Client
│  (MCP Client)    │
└────────┬─────────┘
         │
         │ (1) Verbindung zu MCP Server
         ▼
┌─────────────────────────────────────────┐
│  MCP Server (Raspberry Pi)              │
│  https://leowiki-mcp.stream             │
│                                         │
│  /.well-known/oauth-protected-resource │ ← (2) OAuth Discovery
└────────┬────────────────────────────────┘
         │
         │ (3) Redirect zur Anmeldung
         ▼
┌─────────────────────────────────────────┐
│  Scalekit Authorization Server          │
│  https://mcpeduauth.scalekit.dev        │
│                                         │
│  Login-Seite für Student/Teacher        │
└────────┬────────────────────────────────┘
         │
         │ (4) JWT Token mit Rolle
         ▼
┌──────────────────┐
│  Claude Desktop  │ ← Token wird sicher gespeichert
└──────────────────┘
```

### Warum OAuth 2.1?

- ✅ **Standard-konform:** RFC 9068 (JSON Web Token Profile)
- ✅ **Sicher:** Tokens werden signiert und validiert
- ✅ **Automatisch:** Token Refresh ohne User-Interaktion
- ✅ **Plattform-übergreifend:** Windows, macOS, Linux
- ✅ **User-freundlich:** Einmal anmelden, dann "it just works"

---

## 👥 Rollenbasierte Zugriffskontrolle (RBAC)

### Die drei Rollen

| **Rolle** | **Access Level** | **Kann sehen** | **Verwendung** |
|-----------|-----------------|----------------|----------------|
| **student** | 1 | Nur `access_level: "student"` Dokumente | Alle Schüler/Studenten |
| **teacher** | 2 | `access_level: "student"` UND `"teacher"` | Lehrer, Professoren |
| **admin** | 3 | Alle: `"student"`, `"teacher"`, `"admin"` | Administratoren, System |

### Role Hierarchy (Privilege-basiert)

```
┌─────────────────────────────────────────────┐
│              AUTHENTICATED                   │
│  ┌─────────────────────────────────────┐   │
│  │           ADMIN                      │   │
│  │  Sees: student + teacher + admin     │   │
│  │  ┌──────────────────────────────┐   │   │
│  │  │       TEACHER                │   │   │
│  │  │  Sees: student + teacher     │   │   │
│  │  │  ┌────────────────────────┐  │   │   │
│  │  │  │     STUDENT             │  │   │   │
│  │  │  │  Sees: student only     │  │   │   │
│  │  │  └────────────────────────┘  │   │   │
│  │  └──────────────────────────────┘   │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### RBAC Access Mapping (Code)

```python
# src/tools/search_tools.py
ROLE_ACCESS_LEVELS = {
    "student": ["student"],                    # Nur student-Inhalte
    "teacher": ["student", "teacher"],         # Student + Teacher
    "admin": ["student", "teacher", "admin"],  # Alles
}
```

### Content Access Levels

Jedes Dokument in Qdrant hat ein `access_level` Feld:

```json
// Beispiel-Dokumente

{
  "id": "doc_001",
  "text": "Python ist eine Programmiersprache...",
  "title": "Python Einführung",
  "access_level": "student",     // ← Für Studenten sichtbar
  "namespace": "Informatik/Grundlagen"
}

{
  "id": "doc_002",
  "text": "Lösung zu Übung 3: a = 5, b = 10...",
  "title": "Übung 3 - Musterlösung",
  "access_level": "teacher",     // ← NUR für Lehrer sichtbar!
  "namespace": "Informatik/Lösungen"
}

{
  "id": "doc_003",
  "text": "Administratorhandbuch: Serverkonfiguration...",
  "title": "Server Setup Guide",
  "access_level": "admin",       // ← NUR für Admins
  "namespace": "System/Admin"
}
```

---

## 🔄 Der komplette Authentifizierungs-Flow

### Schritt 1: Initialisierung (beim ersten Start)

```
Student/Teacher öffnet Claude Desktop
    ↓
Claude liest claude_desktop_config.json:
{
  "mcpServers": {
    "mcp-educational-server": {
      "url": "https://leowiki-mcp.stream/",
      "oauth": {
        "enabled": true,
        "discoveryUrl": "https://leowiki-mcp.stream/.well-known/oauth-protected-resource"
      }
    }
  }
}
    ↓
Claude ruft Discovery Endpoint auf
    ↓
Server antwortet mit Scalekit Authorization Server URL
```

### Schritt 2: OAuth Login (erste Anmeldung)

```
1. Claude Desktop erkennt: "Auth erforderlich"
   
2. Claude öffnet Browser-Fenster:
   → https://mcpeduauth.scalekit.dev/authorize?
     client_id=skc_XXX&
     redirect_uri=http://localhost:PORT/callback&
     response_type=code&
     state=RANDOM_STRING&
     scope=openid+profile+email

3. Student/Teacher sieht Scalekit Login-Seite:
   ┌─────────────────────────────────┐
   │  MCP Educational Server Login   │
   │                                 │
   │  Email: ________________        │
   │  Password: ____________         │
   │                                 │
   │  [ Login as Student/Teacher ]   │
   └─────────────────────────────────┘

4. User gibt Credentials ein

5. Scalekit prüft:
   - Credentials korrekt?
   - Welche Rolle? → student / teacher / admin

6. Scalekit erstellt JWT Token:
   {
     "sub": "user_123",
     "email": "max@htl-leonding.at",
     "role": "student",  ← WICHTIG!
     "iss": "https://mcpeduauth.scalekit.dev",
     "aud": "https://leowiki-mcp.stream",
     "exp": 1704567890,
     "iat": 1704564290
   }

7. Redirect zurück zu Claude mit Authorization Code

8. Claude tauscht Code gegen Access Token:
   POST https://mcpeduauth.scalekit.dev/token
   → Erhält JWT Access Token

9. Claude speichert Token verschlüsselt
```

### Schritt 3: Token Lifecycle

```
Token läuft ab (nach 1 Stunde)
    ↓
Student macht nächste Anfrage
    ↓
MCP Server: Token expired → 401 Unauthorized
    ↓
Claude Desktop erkennt 401
    ↓
Claude Desktop verwendet Refresh Token:
    POST https://mcpeduauth.scalekit.dev/token
    grant_type=refresh_token
    refresh_token=...
    ↓
Neuer Access Token
    ↓
Request automatisch wiederholen
    ↓
Student merkt nichts! ✓
```

---

## 🎫 JWT Token mit Rollen

### Student Token (Beispiel)

```json
{
  "iss": "https://mcpeduauth.scalekit.dev",
  "sub": "user_123",
  "aud": "https://leowiki-mcp.stream",
  "exp": 1704567890,
  "iat": 1704564290,
  "email": "max.mustermann@htl-leonding.at",
  "name": "Max Mustermann",
  "roles": ["student"],                    // ← HIER IST DIE ROLLE!
  "org_id": "org_htl_leonding"
}
```

### Teacher Token (Beispiel)

```json
{
  "iss": "https://mcpeduauth.scalekit.dev",
  "sub": "user_456",
  "aud": "https://leowiki-mcp.stream",
  "exp": 1704567890,
  "iat": 1704564290,
  "email": "prof.mueller@htl-leonding.at",
  "name": "Prof. Müller",
  "roles": ["teacher"],                    // ← TEACHER ROLLE!
  "org_id": "org_htl_leonding"
}
```

### Admin Token (mehrere Rollen)

```json
{
  "iss": "https://mcpeduauth.scalekit.dev",
  "sub": "user_789",
  "aud": "https://leowiki-mcp.stream",
  "exp": 1704567890,
  "iat": 1704564290,
  "email": "admin@htl-leonding.at",
  "name": "Administrator",
  "roles": ["admin", "teacher"],           // ← MEHRERE ROLLEN!
  "org_id": "org_htl_leonding"
}
```

### Rolle extrahieren (Server-Side)

```python
# src/middleware/auth.py

def _extract_role(self, claims: dict) -> str:
    """
    Extract user role from Scalekit token claims.
    """
    roles = claims.get("roles", [])
    
    # If multiple roles, use highest privilege
    if "admin" in roles:
        return "admin"
    elif "teacher" in roles:
        return "teacher"
    elif "student" in roles:
        return "student"
    
    # Default to student for authenticated users
    return "student"
```

**Hierarchie** (bei mehreren Rollen):
```
admin > teacher > student
```

---

## 💾 Token-Speicherung und Management

### WO wird der Token gespeichert?

**Claude Desktop** (der MCP Client) speichert den Token **SICHER im eigenen Speicher**:

**Windows:**
```
%LOCALAPPDATA%\Claude\
  ├── User Data\
  │   └── Default\
  │       └── Storage\      ← OAuth Tokens hier (verschlüsselt)
```

**macOS:**
```
~/Library/Application Support/Claude/
  └── oauth_tokens.json     ← Verschlüsselt mit Keychain
```

**Linux:**
```
~/.config/Claude/
  └── oauth_storage         ← Keyring/Secret Service
```

### **WICHTIG: Was NICHT verwendet wird**

- ❌ **NICHT** im Browser Cookie Store!
- ❌ **NICHT** im Windows Credential Manager!
- ❌ **NICHT** in der `claude_desktop_config.json`!
- ✅ **Stattdessen:** Claude Desktop hat einen **eigenen sicheren Token Store**

### Token Management (Internes Verhalten von Claude Desktop)

```python
# Claude Desktop macht intern (vereinfacht):

class MCPClientOAuthManager:
    def __init__(self):
        self.token_store = SecureTokenStorage()  # Verschlüsselter Storage
    
    async def get_token(self, server_id: str) -> str:
        """Hole Token aus sicherem Speicher"""
        token = self.token_store.get(server_id)
        
        if token.is_expired():
            # Automatisch refreshen!
            token = await self.refresh_token(token.refresh_token)
            self.token_store.save(server_id, token)
        
        return token.access_token
    
    async def make_mcp_request(self, server_url: str, method: str, params: dict):
        """Jeder MCP Request bekommt automatisch den Token"""
        token = await self.get_token("mcp-educational-server")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        return await httpx.post(server_url, json=params, headers=headers)
```

---

## 🔍 Token-Verwendung bei MCP-Requests

### Wenn Student eine Suche macht

```
Student in Claude: "Suche nach Python Grundlagen"
    ↓
Claude Desktop:
    1. Erkennt: MCP Tool "search_content" soll verwendet werden
    2. Holt Token aus internem Speicher
    3. Macht HTTP Request:
    
    POST https://leowiki-mcp.stream/mcp
    Headers:
        Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
        Content-Type: application/json
    Body:
        {
          "jsonrpc": "2.0",
          "method": "tools/call",
          "params": {
            "name": "search_content",
            "arguments": {
              "query": "Python Grundlagen",
              "limit": 10
            }
          }
        }
    ↓
MCP Server (Raspberry Pi):
    1. AuthenticationMiddleware extrahiert Token
    2. ScalekitClient validiert Token:
       - Signatur prüfen (mit JWKS von Scalekit)
       - Expiration prüfen
       - Audience prüfen
       - Issuer prüfen
    3. Rolle extrahieren: "student"
    4. Request State setzen: request.state.user = {"role": "student"}
    ↓
search_content Tool:
    1. Rolle aus request.state.user holen
    2. Qdrant Query mit Filter:
       filter={
         "must": [
           {
             "key": "access_level",
             "match": {"any": ["student"]}
           }
         ]
       }
    3. Nur Student-sichtbare Ergebnisse zurückgeben
```

### Server-Side Validation (Code)

```python
# src/middleware/auth.py

async def _validate_token(self, token: str) -> Optional[dict]:
    """Token bei jedem Request validieren"""
    try:
        # Scalekit SDK macht die komplette Validierung
        claims = self.scalekit_client.validate_token_and_get_claims(
            token=token,
            audience="https://leowiki-mcp.stream"
        )
        
        # User-Info extrahieren
        user_info = {
            "sub": claims.get("sub"),
            "email": claims.get("email"),
            "role": self._extract_role(claims),  # student/teacher/admin
            "name": claims.get("name"),
        }
        
        return user_info
        
    except jwt.ExpiredSignatureError:
        # Token abgelaufen → 401 Error
        # Claude Desktop wird automatisch refreshen
        return None
```

---

## 🎯 Unterscheidung: Student vs. Teacher

### Szenario: Beide suchen nach "Python Übung 3"

**Datenbank enthält:**
```json
[
  {
    "id": "1",
    "title": "Python Übung 3 - Aufgabenstellung",
    "text": "Schreibe ein Programm, das...",
    "access_level": "student",  // ← BEIDE sehen das
    "score": 0.95
  },
  {
    "id": "2", 
    "title": "Python Übung 3 - Musterlösung",
    "text": "Lösung: def calculate(a, b): return a + b...",
    "access_level": "teacher",  // ← NUR LEHRER sieht das!
    "score": 0.89
  },
  {
    "id": "3",
    "title": "Python Übung 3 - Hinweise",
    "text": "Tipp: Verwende eine Schleife...",
    "access_level": "student",  // ← BEIDE sehen das
    "score": 0.82
  }
]
```

### Student macht Suche

```
Student: "Suche nach Python Übung 3"
    ↓
Claude Desktop sendet Request mit Student-Token
    ↓
MCP Server extrahiert Rolle: "student"
    ↓
Qdrant Filter: access_level IN ["student"]
    ↓
Ergebnisse:
✅ Doc 1: Aufgabenstellung (access_level: student, score: 0.95)
✅ Doc 3: Hinweise (access_level: student, score: 0.82)
❌ Doc 2: Musterlösung wird NICHT angezeigt!
```

### Teacher macht Suche

```
Teacher: "Suche nach Python Übung 3"
    ↓
Claude Desktop sendet Request mit Teacher-Token
    ↓
MCP Server extrahiert Rolle: "teacher"
    ↓
Qdrant Filter: access_level IN ["student", "teacher"]
    ↓
Ergebnisse:
✅ Doc 1: Aufgabenstellung (access_level: student, score: 0.95)
✅ Doc 2: Musterlösung (access_level: teacher, score: 0.89) ← SICHTBAR!
✅ Doc 3: Hinweise (access_level: student, score: 0.82)
```

### Visuelle Darstellung

```
┌─────────────────────────────────────────────────────────────┐
│                    QDRANT DATABASE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🟢 Doc A (access_level: "student")   ←── Student sieht   │
│  🟡 Doc B (access_level: "teacher")   ←── Nur Teacher!    │
│  🟢 Doc C (access_level: "student")   ←── Student sieht   │
│  🔴 Doc D (access_level: "admin")     ←── Nur Admin!      │
│  🟢 Doc E (access_level: "student")   ←── Student sieht   │
│  🟡 Doc F (access_level: "teacher")   ←── Nur Teacher!    │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Student sucht "Python":         Teacher sucht "Python":
   ↓                               ↓
Filter: ["student"]              Filter: ["student", "teacher"]
   ↓                               ↓
Ergebnis:                        Ergebnis:
✅ Doc A                          ✅ Doc A
❌ Doc B (gefiltert!)            ✅ Doc B  ← SICHTBAR!
✅ Doc C                          ✅ Doc C
❌ Doc D (gefiltert!)            ❌ Doc D (gefiltert!)
✅ Doc E                          ✅ Doc E
❌ Doc F (gefiltert!)            ✅ Doc F  ← SICHTBAR!
```

---

## 💻 Claude Desktop Konfiguration

### Die Config ist für ALLE gleich!

**WICHTIG:** Die `claude_desktop_config.json` ist **identisch** für Students, Teachers und Admins!

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mcp-educational-server": {
      "url": "https://leowiki-mcp.stream/",
      "oauth": {
        "enabled": true,
        "discoveryUrl": "https://leowiki-mcp.stream/.well-known/oauth-protected-resource"
      }
    }
  }
}
```

### Was NICHT in der Config steht

- ❌ **Keine User Credentials** (Email, Password)
- ❌ **Keine Rolle** (student/teacher/admin)
- ❌ **Keine Tokens** (JWT Access Token)
- ❌ **Keine User-spezifischen Daten**

### Warum ist die Config generisch?

**Weil die Unterscheidung beim Login passiert!**

```
Computer 1 - Max (Student):
  → claude_desktop_config.json (GLEICH!)
  → Max loggt sich mit max@htl.at ein
  → Scalekit gibt Token mit Rolle "student"
  → Max sieht nur Student-Content

Computer 2 - Prof. Müller (Teacher):
  → claude_desktop_config.json (GENAU GLEICH!)
  → Prof. Müller loggt sich mit prof@htl.at ein
  → Scalekit gibt Token mit Rolle "teacher"
  → Prof. Müller sieht Student + Teacher Content
```

**DIE CONFIG IST IDENTISCH!** 🎯  
**Die Rolle kommt vom LOGIN!** 🔑

---

## 👥 User-Verwaltung in Scalekit

### Rollen-Speicherung in Scalekit

In **Scalekit** (dem OAuth Server) werden Benutzer mit ihren Rollen gespeichert:

```
┌──────────────────────────────────────────────────────┐
│              Scalekit User Database                  │
├──────────────────────────────────────────────────────┤
│                                                      │
│  User 1:                                            │
│  📧 Email: max.mustermann@htl-leonding.at          │
│  🔑 Password: (gehasht mit bcrypt)                 │
│  👤 Roles: ["student"]           ← HIER DEFINIERT! │
│  🏢 Organization: HTL Leonding                      │
│                                                      │
├──────────────────────────────────────────────────────┤
│                                                      │
│  User 2:                                            │
│  📧 Email: prof.mueller@htl-leonding.at            │
│  🔑 Password: (gehasht mit bcrypt)                 │
│  👤 Roles: ["teacher"]           ← HIER DEFINIERT! │
│  🏢 Organization: HTL Leonding                      │
│                                                      │
├──────────────────────────────────────────────────────┤
│                                                      │
│  User 3:                                            │
│  📧 Email: admin@htl-leonding.at                   │
│  🔑 Password: (gehasht mit bcrypt)                 │
│  👤 Roles: ["admin", "teacher"]  ← MEHRERE ROLLEN! │
│  🏢 Organization: HTL Leonding                      │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Option 1: Über Scalekit Dashboard

```
1. Login auf https://mcpeduauth.scalekit.dev
   ↓
2. Navigiere zu "Users" oder "Organizations"
   ↓
3. Click "Add User"
   ↓
4. Eingaben:
   ┌────────────────────────────────────┐
   │  Email: student@htl.at             │
   │  Name: Student Name                │
   │  Password: (generiert oder selbst) │
   │  Roles: [x] student                │ ← ROLLE WÄHLEN!
   │         [ ] teacher                │
   │         [ ] admin                  │
   │  Organization: HTL Leonding        │
   └────────────────────────────────────┘
   ↓
5. "Create User"
   ↓
6. User ist angelegt! ✓
```

### Option 2: Via Scalekit API (programmatisch)

```python
# scripts/create_scalekit_user.py
from scalekit import ScalekitClient

client = ScalekitClient(
    env_url="https://mcpeduauth.scalekit.dev",
    client_id="skc_35934031996379566",
    client_secret="your-secret"
)

# Student anlegen
student = client.users.create({
    "email": "max.mustermann@htl-leonding.at",
    "name": "Max Mustermann",
    "password": "SecurePassword123!",
    "roles": ["student"],         # ← ROLLE HIER!
    "organization_id": "org_htl"
})

# Teacher anlegen
teacher = client.users.create({
    "email": "prof.mueller@htl-leonding.at",
    "name": "Prof. Müller",
    "password": "SecurePassword456!",
    "roles": ["teacher"],         # ← ROLLE HIER!
    "organization_id": "org_htl"
})

print("✅ Users created!")
```

### Option 3: CSV Import (für viele User)

Erstelle eine CSV-Datei:

```csv
email,name,role,organization
max.mustermann@htl-leonding.at,Max Mustermann,student,HTL Leonding
anna.schmidt@htl-leonding.at,Anna Schmidt,student,HTL Leonding
peter.mayer@htl-leonding.at,Peter Mayer,student,HTL Leonding
prof.mueller@htl-leonding.at,Prof. Müller,teacher,HTL Leonding
prof.wagner@htl-leonding.at,Prof. Wagner,teacher,HTL Leonding
admin@htl-leonding.at,Admin User,admin,HTL Leonding
```

Dann über Scalekit Dashboard importieren.

### Rolle ändern

```
1. Scalekit Dashboard öffnen
   ↓
2. "Users" → User auswählen
   ↓
3. "Edit User"
   ↓
4. Roles ändern:
   Von: [x] student
   Zu:  [x] teacher
   ↓
5. "Save"
   ↓
6. User muss sich NEU anmelden
   ↓
7. Neuer Token mit neuer Rolle wird erstellt
   ↓
8. User hat jetzt Teacher-Rechte! ✓
```

---

## 🏫 Praktisches Beispiel: HTL Leonding

### Setup-Szenario

**HTL Leonding hat:**
- 300 Schüler
- 20 Lehrer
- 2 Administratoren

### Schritt 1: Scalekit Users anlegen

```bash
# Via Scalekit Dashboard oder API

# Alle Schüler (Beispiele):
max.mustermann@htl-leonding.at   → Role: student
anna.schmidt@htl-leonding.at     → Role: student
peter.mayer@htl-leonding.at      → Role: student
lisa.huber@htl-leonding.at       → Role: student
... (296 weitere Schüler)

# Alle Lehrer:
prof.mueller@htl-leonding.at     → Role: teacher
prof.wagner@htl-leonding.at      → Role: teacher
prof.huber@htl-leonding.at       → Role: teacher
prof.schmidt@htl-leonding.at     → Role: teacher
... (16 weitere Lehrer)

# Admins:
admin@htl-leonding.at            → Role: admin
direktion@htl-leonding.at        → Role: admin
```

### Schritt 2: Claude Desktop Config verteilen

**EINE Config für ALLE!**

Email an alle Schüler, Lehrer und Admins:

```
Betreff: MCP Educational Server - Zugang

Liebe Kollegen und Schüler,

Ab sofort könnt ihr den MCP Educational Server mit Claude Desktop nutzen.

1. Claude Desktop installieren: https://claude.ai/download

2. Config-Datei anpassen:
   Windows: %APPDATA%\Claude\claude_desktop_config.json
   macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
   Linux: ~/.config/Claude/claude_desktop_config.json

3. Folgenden Code einfügen:

{
  "mcpServers": {
    "mcp-educational-server": {
      "url": "https://leowiki-mcp.stream/",
      "oauth": {
        "enabled": true,
        "discoveryUrl": "https://leowiki-mcp.stream/.well-known/oauth-protected-resource"
      }
    }
  }
}

4. Claude Desktop neu starten

5. Beim ersten Zugriff werdet ihr aufgefordert, euch anzumelden.
   Verwendet eure HTL-Email-Adresse und das erhaltene Passwort.

Eure Zugriffsrechte werden automatisch basierend auf eurer Rolle bestimmt.

Viel Erfolg!
```

### Schritt 3: Login-Phase

**Schüler Max:**
```
1. Öffnet Claude Desktop
2. Browser öffnet sich mit Scalekit Login
3. Gibt ein: max.mustermann@htl-leonding.at + Passwort
4. Scalekit erkennt: Rolle = "student"
5. Token mit Rolle "student" wird erstellt
6. Max sieht nur Student-Inhalte ✓
```

**Lehrer Prof. Müller:**
```
1. Öffnet Claude Desktop
2. Browser öffnet sich mit Scalekit Login
3. Gibt ein: prof.mueller@htl-leonding.at + Passwort
4. Scalekit erkennt: Rolle = "teacher"
5. Token mit Rolle "teacher" wird erstellt
6. Prof. Müller sieht Student + Teacher Inhalte ✓
```

**Admin:**
```
1. Öffnet Claude Desktop
2. Browser öffnet sich mit Scalekit Login
3. Gibt ein: admin@htl-leonding.at + Passwort
4. Scalekit erkennt: Rolle = "admin"
5. Token mit Rolle "admin" wird erstellt
6. Admin sieht alle Inhalte ✓
```

### Ergebnis

- ✅ **322 Personen** mit der **GLEICHEN Config**
- ✅ **Automatische Rollenzuweisung** beim Login
- ✅ **Keine manuelle Konfiguration** pro User
- ✅ **Zentrale Verwaltung** in Scalekit
- ✅ **Sicher** durch OAuth 2.1

---

## 🧪 Testing und Troubleshooting

### Test 1: Health Check (ohne Auth)

```bash
curl https://leowiki-mcp.stream/health
```

**Erwartete Antwort:**
```json
{
  "status": "healthy",
  "server": "mcp-educational-server",
  "version": "1.0.0",
  "authentication": "enabled",
  "rbac": "enabled"
}
```

### Test 2: OAuth Discovery (ohne Auth)

```bash
curl https://leowiki-mcp.stream/.well-known/oauth-protected-resource
```

**Erwartete Antwort:**
```json
{
  "resource": "https://leowiki-mcp.stream",
  "authorization_servers": [
    "https://mcpeduauth.scalekit.dev/resources/res_10661405199119278"
  ],
  "bearer_methods_supported": ["header"],
  "resource_documentation": "https://leowiki-mcp.stream/docs"
}
```

### Test 3: Protected Endpoint (sollte fehlschlagen)

```bash
curl https://leowiki-mcp.stream/mcp
```

**Erwartete Antwort:**
```json
{
  "error": "invalid_token",
  "error_description": "Missing Bearer token"
}
```

### Test 4: Mit gültigem Token

```bash
curl -X POST https://leowiki-mcp.stream/mcp \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "search_content",
      "arguments": {
        "query": "Python",
        "limit": 5
      }
    },
    "id": 1
  }'
```

### Troubleshooting: Häufige Probleme

#### Problem: "No authentication token"

**Ursache:** Token fehlt oder ist falsch formatiert

**Lösung:**
1. Claude Desktop komplett neu starten
2. Token sollte automatisch refreshed werden
3. Falls nicht: Neu anmelden

#### Problem: "Invalid or expired token"

**Ursache:** Token abgelaufen

**Lösung:**
- Claude Desktop refreshed automatisch
- Falls nicht: Neu anmelden

#### Problem: "User sieht keine Ergebnisse"

**Ursache:** RBAC filtert alle Dokumente raus

**Lösung:**
1. Überprüfe User-Rolle: Ist er als "student" eingeloggt?
2. Überprüfe Dokumente: Gibt es "student"-level Dokumente?
3. Versuche als "teacher" anzumelden

#### Problem: "Rolle ist falsch"

**Ursache:** User hat falsche Rolle in Scalekit

**Lösung:**
1. Scalekit Dashboard öffnen
2. User-Rolle korrigieren
3. User muss sich NEU anmelden (altes Token ist noch gültig!)

---

## 📊 Zusammenfassung: Die komplette Kette

```
1. Scalekit User Database
   └── User hat Rolle: "student" oder "teacher"
       
2. JWT Token (nach Login)
   └── Token enthält: "roles": ["student"]
       
3. Claude Desktop
   └── Speichert Token verschlüsselt
       
4. MCP Request
   └── Sendet Token im Authorization Header
       
5. MCP Server Middleware (auth.py)
   └── Validiert Token
   └── Extrahiert Rolle aus JWT
   └── Speichert in request.state.user["role"]
       
6. MCP Tool (search_content)
   └── Liest Rolle: access_level = request.state.user["role"]
   └── Erstellt Qdrant Filter basierend auf Rolle
       
7. Qdrant Suche
   └── Filter wird angewendet
   └── NUR Dokumente mit erlaubtem access_level zurück
       
8. Ergebnis
   └── Student sieht nur "student"-Dokumente
   └── Teacher sieht "student" + "teacher"-Dokumente
```

---

## 🎯 Key Takeaways

| **Frage** | **Antwort** |
|-----------|-------------|
| Wo wird die Rolle gespeichert? | In Scalekit User Database |
| Wo wird die Rolle NICHT gespeichert? | NICHT in claude_desktop_config.json |
| Wann wird die Rolle bestimmt? | Beim Login (automatisch) |
| Wo steht die Rolle im Token? | Im JWT unter "roles" Claim |
| Wie wird zwischen Student/Teacher unterschieden? | Automatisch durch Rolle im Token |
| Ist die Config für alle gleich? | Ja! Identisch für Student, Teacher, Admin |
| Wo werden Tokens gespeichert? | Claude Desktop (verschlüsselt) |
| Kann ein User mehrere Rollen haben? | Ja, höchste Rolle zählt |

---

## 🚀 Fazit

**Das ist die Eleganz von OAuth 2.1!** 🚀

**Die Config ist generisch, die Rolle kommt vom User-Account!**
