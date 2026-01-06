# 🧪 Claude Desktop Testing Guide - Scalekit OAuth & RBAC

## 📋 **Übersicht**

Dieser Guide testet die vollständige Integration:
1. ✅ Scalekit OAuth 2.1 Authentication
2. ✅ Role-Based Access Control (RBAC)
3. ✅ Claude Desktop MCP Integration

---

## 🎯 **Test-Architektur**

```
┌──────────────────┐         ┌─────────────────┐
│  Claude Desktop  │◄────────│  Scalekit Auth  │
│  (OAuth Client)  │  tokens │   Server        │
└────────┬─────────┘         └─────────────────┘
         │ Bearer Token
         ▼
┌──────────────────┐
│   MCP Server     │ https://leowiki-mcp.stream
│ (Protected Res)  │
├──────────────────┤
│ /.well-known/    │ ← OAuth discovery ✅
│   oauth-prote... │
│ /mcp             │ ← MCP protocol
│ /health          │ ← Health check ✅
└──────────────────┘
         │
         ▼
┌──────────────────┐
│     Qdrant       │ Vector Database
│  (3417 points)   │ RBAC filtering ✅
└──────────────────┘
```

---

## ✅ **PRE-FLIGHT CHECK**

### **1. Server Status**

```bash
curl https://leowiki-mcp.stream/health
```

**Erwartete Antwort:**
```json
{
    "status": "healthy",
    "server": "MCP Educational Server",
    "version": "1.0.0",
    "authentication": "enabled",
    "rbac": "enabled"
}
```

✅ **Status:** Verified

---

### **2. OAuth Discovery**

```bash
curl https://leowiki-mcp.stream/.well-known/oauth-protected-resource
```

**Erwartete Antwort:**
```json
{
    "resource": "mcp-edu-server",
    "authorization_servers": [
        "https://mcpeduauth.scalekit.dev"
    ],
    "bearer_methods_supported": ["header"],
    "resource_signing_alg_values_supported": ["RS256"],
    "scopes_supported": ["mcp:read", "mcp:write", "usr:read", "usr:write"]
}
```

✅ **Status:** Verified

---

### **3. Qdrant Collection**

```bash
curl http://localhost:6333/collections/educational_content
```

**Erwartete Daten:**
- ✅ **Points:** 3417 (exakt match mit JSONL)
- ✅ **Collections:** media (2385) + pages (1032)
- ✅ **Status:** green

---

## 📝 **SCHRITT 1: Scalekit Dashboard Konfiguration**

### **URL:** https://app.scalekit.com

### **Zu prüfen/konfigurieren:**

#### **1. MCP Server Settings**
- ✅ **Name:** MCP Educational Server
- ✅ **Resource ID:** `res_10661405199119278`
- ✅ **Environment URL:** `https://mcpeduauth.scalekit.dev`

#### **2. Redirect URIs (für Claude Desktop)**

Claude Desktop erfordert spezielle Redirect URIs:

```
claude-desktop://auth/callback
http://localhost:PORT/auth/callback
```

**Wichtig:** Prüfe in Scalekit Dashboard unter "MCP Server" → "Redirect URIs"

#### **3. Test-User mit Rollen**

Erstelle 3 Test-User in Scalekit:

| User | Email | Rolle | Access Level |
|------|-------|-------|--------------|
| Student | `student@test.local` | `student` | student content only |
| Teacher | `teacher@test.local` | `teacher` | student + teacher content |
| Admin | `admin@test.local` | `admin` | all content |

**Rollen-Konfiguration:**
- User → Edit → Roles → Assign Role
- Rollen müssen exakt `student`, `teacher`, oder `admin` heißen

---

## 🖥️ **SCHRITT 2: Claude Desktop Konfiguration**

### **Config File Location:**

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

---

### **Config Beispiel:**

```json
{
  "mcpServers": {
    "leowiki-mcp": {
      "command": "python",
      "args": [
        "/home/imreo/mcp-diploma-thesis-final/main.py"
      ],
      "env": {
        "PYTHONPATH": "/home/imreo/mcp-diploma-thesis-final",
        "OPENAI_API_KEY": "sk-proj-...",
        "VECTOR_DB_URL": "http://qdrant:6333",
        "DEFAULT_COLLECTION": "educational_content",
        "ENABLE_AUTH": "true",
        "ENABLE_RBAC": "true",
        "SCALEKIT_ENV_URL": "https://mcpeduauth.scalekit.dev",
        "SCALEKIT_CLIENT_ID": "skc_35934031996379566",
        "SCALEKIT_CLIENT_SECRET": "test_sk_JnDlRTWW5RnNdg2TLYCWnuPg2O2cKrDAJHkp8dhFxg5NEG-PaYiYv3OT1X1v_jgz",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Wichtige Felder:**
- ✅ `command`: Python-Interpreter (oder absoluter Pfad)
- ✅ `args`: Pfad zu `main.py` (OHNE `--http` Flag!)
- ✅ `ENABLE_AUTH=true`: OAuth aktiviert
- ✅ `ENABLE_RBAC=true`: Role-based filtering
- ✅ Scalekit credentials

---

## 🧪 **SCHRITT 3: Testing in Claude Desktop**

### **Test 1: Connection Establishment**

1. **Claude Desktop starten**
2. **Settings** → **Developer** → **MCP Servers**
3. **Prüfen:** Ist `leowiki-mcp` aufgelistet?
   - ✅ Status: Connected
   - ✅ Tools: `search_content`, `health_check`

**Erwartetes Verhalten:**
- Claude Desktop entdeckt Server via `.well-known/oauth-protected-resource`
- OAuth-Flow wird automatisch gestartet

---

### **Test 2: OAuth Login (Student)**

1. **Claude Desktop öffnet Browser** → Scalekit Login
2. **Login mit:** `student@test.local` / Passwort
3. **Grant permissions** (falls gefragt)
4. **Redirect zurück zu Claude Desktop**

**Erwartetes Ergebnis:**
- ✅ Token wird gespeichert
- ✅ MCP Server ist verbunden
- ✅ Student-Rolle ist aktiv

---

### **Test 3: RBAC - Student Query**

**In Claude Desktop eingeben:**

```
Suche nach "Matura 2021" in den Dokumenten
```

**Erwartetes Verhalten:**
1. Claude Desktop ruft `search_content` Tool auf
2. MCP Server:
   - Validiert Bearer Token
   - Extrahiert Rolle: `student`
   - Wendet RBAC-Filter an: `access_level = ["student"]`
3. Qdrant liefert nur Student-Content

**Erwartetes Ergebnis:**
- ✅ Nur Dokumente mit `access_level: student`
- ❌ Keine Dokumente mit `access_level: teacher` oder `admin`

**Beispiel-Output:**
```
Found 5 results for 'Matura 2021'

**Result 1** (score: 0.892)
Title: Ablauf und Durchführung der Matura 2020/21
Namespace: archive:exams
Content_Type: KNOWLEDGE
Access Level: student ✅

**Result 2** (score: 0.876)
Title: Matura Termine SoSe 2021
...
```

---

### **Test 4: RBAC - Teacher Query**

1. **Logout aus Claude Desktop**
2. **Login mit:** `teacher@test.local`
3. **Suche erneut:** "Matura 2021"

**Erwartetes Verhalten:**
- RBAC-Filter: `access_level = ["student", "teacher"]`
- Mehr Ergebnisse als Student

**Vergleich:**
| Rolle | Filter | Anzahl Ergebnisse | Content-Types |
|-------|--------|-------------------|---------------|
| Student | `["student"]` | z.B. 5 | Public info |
| Teacher | `["student", "teacher"]` | z.B. 8 | + Teacher materials |
| Admin | `["student", "teacher", "admin"]` | z.B. 10 | + Admin docs |

---

### **Test 5: Access Denied für geschützte Inhalte**

**Scenario:** Student versucht Teacher-Content zu sehen

1. **Login als:** `student@test.local`
2. **Suche:** "Lehrerkonferenz" (hypothetisch ein teacher-only Dokument)

**Erwartetes Ergebnis:**
- ❌ Keine Ergebnisse (oder nur student-level Infos)
- ✅ Teacher-only Content wird gefiltert

---

## 🔍 **SCHRITT 4: Debug & Troubleshooting**

### **Problem 1: OAuth Flow startet nicht**

**Check:**
```bash
# Prüfe OAuth Discovery
curl https://leowiki-mcp.stream/.well-known/oauth-protected-resource

# Erwartete Keys:
# - resource
# - authorization_servers
# - bearer_methods_supported
```

**Lösung:**
- Prüfe `ENABLE_AUTH=true` in `.env`
- Prüfe Scalekit credentials
- Restart Docker Container: `docker compose restart mcp-server`

---

### **Problem 2: Authentication Failed**

**Claude Desktop Fehlermeldung:**
```
Failed to authenticate with MCP server
```

**Check:**
1. **Scalekit Dashboard** → **Redirect URIs:**
   - Enthält `claude-desktop://auth/callback`?
   
2. **Token Validation:**
   ```bash
   # Check server logs
   docker logs mcp-server | grep -i "auth\|token\|scalekit"
   ```

3. **Scalekit Client Secret:**
   - Korrekt in `.env`?
   - Keine Leerzeichen oder Zeilenumbrüche?

---

### **Problem 3: RBAC funktioniert nicht (alle User sehen alles)**

**Check:**
```bash
# Prüfe ENABLE_RBAC
docker exec mcp-server env | grep RBAC

# Erwartete Ausgabe: ENABLE_RBAC=true
```

**Check Qdrant Dokumente:**
```bash
curl -X POST http://localhost:6333/collections/educational_content/points/scroll \
  -H "Content-Type: application/json" \
  -d '{"limit": 5, "with_payload": {"include": ["access_level"]}, "with_vector": false}' | \
  python3 -m json.tool
```

**Erwartete Struktur:**
```json
{
  "payload": {
    "access_level": "student"  // oder "teacher" oder "admin"
  }
}
```

**Lösung:**
- Prüfe, ob alle Dokumente `access_level` haben
- Wenn nicht: Re-ingest JSONL mit korrekter Struktur

---

### **Problem 4: Keine Rolle im Token**

**Check Server Logs:**
```bash
docker logs mcp-server | grep "No recognized role"
```

**Erwartete Log-Zeile:**
```
WARNING - No recognized role in token, defaulting to student. Roles: [...]
```

**Lösung:**
1. **Scalekit Dashboard** → **User** → **Roles**
   - Prüfe, ob Rolle zugewiesen ist
   - Rollen müssen exakt `student`, `teacher`, oder `admin` heißen

2. **Token Claims prüfen:**
   ```bash
   # Decode JWT Token (https://jwt.io)
   # Erwartete Claims:
   {
     "sub": "user_123",
     "email": "student@test.local",
     "roles": ["student"],  // WICHTIG!
     "org_id": "org_123"
   }
   ```

---

## 📊 **ERWARTETE TEST-ERGEBNISSE**

### **Zusammenfassung:**

| Test | Student | Teacher | Admin | Status |
|------|---------|---------|-------|--------|
| OAuth Login | ✅ | ✅ | ✅ | Pass |
| Token Validation | ✅ | ✅ | ✅ | Pass |
| search_content Tool | ✅ | ✅ | ✅ | Pass |
| RBAC Filtering | student only | student+teacher | all | Pass |
| Access Denied | teacher/admin hidden | admin hidden | - | Pass |

---

## 🎉 **SUCCESS CRITERIA**

✅ **OAuth Flow:**
- Claude Desktop startet Login automatisch
- Redirect zu Scalekit funktioniert
- Token wird gespeichert

✅ **RBAC:**
- Student sieht nur `access_level: student`
- Teacher sieht `student + teacher`
- Admin sieht alle Content-Levels

✅ **MCP Integration:**
- Tools sind verfügbar in Claude Desktop
- Queries liefern korrekte, gefilterte Ergebnisse
- Keine Fehler in Server Logs

---

## 📝 **NEXT STEPS NACH ERFOLGREICHEN TESTS**

1. **Production Users erstellen** in Scalekit
2. **OAuth Redirect URIs** für Production updaten
3. **Monitoring** einrichten (Server Logs, Qdrant Status)
4. **Dokumentation** für End-User erstellen
5. **Backup-Strategie** für Qdrant Collection

---

## 📚 **Referenzen**

- [Scalekit MCP Quickstart](https://docs.scalekit.com/authenticate/mcp/quickstart/)
- [MCP Specification](https://modelcontextprotocol.io/)
- [FastMCP Library](https://github.com/jlowin/fastmcp)
- [OAuth 2.1 Protected Resource](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1)

---

**Status:** Ready for Testing 🚀  
**Last Updated:** 2026-01-06  
**Version:** 1.0
