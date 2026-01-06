# 🔐 Scalekit Final Setup - OAuth 2.1 Production

**Datum:** 06. Januar 2026  
**Status:** 🟡 **Konfiguration vorhanden, Test-User fehlen noch**

---

## 🎯 Übersicht

Scalekit ist unser **OAuth Authorization Server** für die Authentifizierung von Studenten und Lehrern.

### Was bereits konfiguriert ist

- ✅ Scalekit Account erstellt
- ✅ Environment erstellt
- ✅ Client ID & Secret in `.env` gespeichert
- ✅ OAuth Flow implementiert (`src/auth/oauth_flow.py`)
- ✅ JWT Validation implementiert (`src/auth/scalekit_client.py`)
- ✅ RBAC Middleware implementiert (`src/middleware/auth.py`)
- ✅ `ENABLE_AUTH=true` aktiviert

### Was noch fehlt

- ⚠️ **Test-User anlegen** (Student & Teacher)
- ⚠️ **End-to-End OAuth Flow testen**
- ⚠️ **Claude Desktop Integration testen**
- ⚠️ **Produktions-User vorbereiten**

---

## 📋 Scalekit Konfiguration

### Environment Variables

```bash
# In .env:
ENABLE_AUTH=true
SCALEKIT_ENV_URL=https://auth.scalekit.com/...
SCALEKIT_CLIENT_ID=skc_...
SCALEKIT_CLIENT_SECRET=sks_...
```

**Status:** ✅ Konfiguriert

### Redirect URIs

**Produktions-URL:**
```
https://leowiki-mcp.stream/auth/callback
```

**Wichtig:** Diese URL muss in Scalekit als "Allowed Redirect URI" eingetragen sein!

**Prüfen:**
1. Login zu Scalekit Dashboard: https://app.scalekit.com
2. Environment auswählen
3. OAuth Settings → Redirect URIs
4. Sicherstellen dass `https://leowiki-mcp.stream/auth/callback` eingetragen ist

---

## 👥 Test-User Anlegen

### Schritt 1: Scalekit Dashboard öffnen

```
https://app.scalekit.com
```

### Schritt 2: Users → Create User

**Test-Student:**
```
Email: student@test.local
Name: Test Student
Role: student
Password: [sicheres Passwort]
```

**Test-Teacher:**
```
Email: teacher@test.local
Name: Test Teacher
Role: teacher
Password: [sicheres Passwort]
```

**Optional - Test-Admin:**
```
Email: admin@test.local
Name: Test Admin
Role: admin
Password: [sicheres Passwort]
```

### Schritt 3: Rollen zuweisen

**Wichtig:** In Scalekit müssen die Rollen EXAKT so heißen:
- `student`
- `teacher`
- `admin`

**Prüfen:**
1. User auswählen
2. Roles → Add Role
3. Rolle zuweisen (student/teacher/admin)

---

## 🧪 Testing

### Test 1: OAuth Login Flow

**Von Windows-PC aus:**

```bash
# Browser öffnen:
https://leowiki-mcp.stream/auth/login
```

**Erwartetes Verhalten:**
1. Redirect zu Scalekit Login-Seite
2. Login mit `student@test.local` / Passwort
3. Redirect zurück zu `/auth/callback`
4. JWT Token wird zurückgegeben
5. Token enthält Rolle "student"

**Erfolg:** ✅ Token erhalten, Rolle "student" im Token

### Test 2: RBAC - Student sieht nur Student-Content

**Claude Desktop Config:**
```json
{
  "mcpServers": {
    "educational-content": {
      "url": "https://leowiki-mcp.stream",
      "transport": {
        "type": "http"
      },
      "auth": {
        "type": "oauth",
        "authorization_url": "https://leowiki-mcp.stream/auth/login",
        "token_url": "https://leowiki-mcp.stream/auth/token",
        "client_id": "claude-desktop"
      }
    }
  }
}
```

**Test:**
1. Claude Desktop öffnen
2. MCP Server verbinden
3. Login als `student@test.local`
4. Tool aufrufen: `search_content` mit Query "test"

**Erwartetes Ergebnis:**
- ✅ Nur Dokumente mit `access_level: student` werden zurückgegeben
- ❌ Dokumente mit `access_level: teacher` werden NICHT zurückgegeben

### Test 3: RBAC - Teacher sieht Student + Teacher Content

**Test:**
1. Claude Desktop neu starten (oder Logout)
2. Login als `teacher@test.local`
3. Tool aufrufen: `search_content` mit Query "test"

**Erwartetes Ergebnis:**
- ✅ Dokumente mit `access_level: student` werden zurückgegeben
- ✅ Dokumente mit `access_level: teacher` werden zurückgegeben
- ❌ Dokumente mit `access_level: admin` werden NICHT zurückgegeben

### Test 4: Token Expiration

**Test:**
1. Login als Student
2. Token erhalten
3. Warten (Token läuft nach 1 Stunde ab)
4. Erneuter API-Aufruf

**Erwartetes Ergebnis:**
- ❌ HTTP 401 Unauthorized
- ✅ Claude Desktop fordert automatisch neuen Login an

### Test 5: Invalid Token

**Test:**
```bash
# Manueller API-Aufruf mit ungültigem Token:
curl -H "Authorization: Bearer invalid_token_xyz" \
     https://leowiki-mcp.stream/api/search?q=test
```

**Erwartetes Ergebnis:**
- ❌ HTTP 401 Unauthorized
- ✅ Error Message: "Invalid token"

---

## 🔍 Debugging

### Logs anzeigen

```bash
# MCP Server Logs (OAuth & RBAC):
docker compose logs -f mcp-server | grep -E "(auth|oauth|token|role)"

# Alle Logs:
docker compose logs -f mcp-server
```

### Häufige Probleme

#### Problem 1: "Redirect URI mismatch"

**Ursache:** Redirect URI in Scalekit stimmt nicht mit der in der Anwendung überein.

**Lösung:**
1. Scalekit Dashboard → OAuth Settings
2. Redirect URIs prüfen
3. Sicherstellen: `https://leowiki-mcp.stream/auth/callback`

#### Problem 2: "Invalid client credentials"

**Ursache:** Client ID oder Secret falsch.

**Lösung:**
```bash
# .env prüfen:
cat /home/imreo/mcp-diploma-thesis-final/.env | grep SCALEKIT

# Sollte zeigen:
# SCALEKIT_CLIENT_ID=skc_...
# SCALEKIT_CLIENT_SECRET=sks_...

# Falls falsch, korrigieren und neu starten:
docker compose restart mcp-server
```

#### Problem 3: "User has no role"

**Ursache:** User in Scalekit hat keine Rolle zugewiesen.

**Lösung:**
1. Scalekit Dashboard → Users
2. User auswählen
3. Roles → Add Role
4. `student`, `teacher` oder `admin` zuweisen

#### Problem 4: "Token validation failed"

**Ursache:** JWT Signatur ungültig oder Token abgelaufen.

**Lösung:**
```bash
# Logs prüfen:
docker compose logs mcp-server | grep "token"

# Mögliche Ursachen:
# - Token abgelaufen (normal, neu anmelden)
# - JWKS nicht erreichbar (Netzwerk-Problem)
# - Token manipuliert (Security-Issue!)
```

---

## 🔐 Sicherheits-Checks

### Check 1: JWT Signatur wird validiert

**Test:**
```bash
# Manipulierten Token senden:
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c" \
     https://leowiki-mcp.stream/api/search?q=test
```

**Erwartetes Ergebnis:**
- ❌ HTTP 401 Unauthorized
- ✅ "Invalid token signature"

### Check 2: Expired Token wird abgelehnt

**Test:**
```bash
# Token mit exp in der Vergangenheit:
# (wird automatisch von Scalekit Client geprüft)
```

**Erwartetes Ergebnis:**
- ❌ HTTP 401 Unauthorized
- ✅ "Token expired"

### Check 3: RBAC wird erzwungen

**Test:**
```bash
# Student-Token verwenden, aber nach Teacher-Content fragen:
# (wird durch Qdrant Filter verhindert)
```

**Erwartetes Ergebnis:**
- ✅ HTTP 200 OK
- ✅ Aber: Nur Student-Content in Ergebnissen
- ❌ Teacher-Content wird NICHT zurückgegeben

---

## 📊 RBAC Flow (Nochmal zur Erinnerung)

```
1. User Login (Scalekit)
   ↓
2. JWT Token mit Rolle (student/teacher/admin)
   ↓
3. Claude Desktop speichert Token
   ↓
4. API-Aufruf mit Token im Header
   ↓
5. AuthenticationMiddleware validiert Token
   ↓
6. Rolle wird extrahiert (z.B. "student")
   ↓
7. get_access_filter() erstellt Qdrant Filter
   ↓
8. Qdrant Search mit Filter
   ↓
9. Nur erlaubte Dokumente werden zurückgegeben
```

**Wichtig:** Die Rolle kommt IMMER vom JWT Token, NIEMALS vom Client!

---

## 🚀 Produktions-User

### Vorbereitung

**Für Studenten:**
1. Email-Adressen sammeln
2. In Scalekit anlegen (einzeln oder Bulk-Import)
3. Rolle `student` zuweisen
4. Initiales Passwort setzen (User muss beim ersten Login ändern)

**Für Lehrer:**
1. Email-Adressen sammeln
2. In Scalekit anlegen
3. Rolle `teacher` zuweisen
4. Initiales Passwort setzen

**Für Admins:**
1. Nur vertrauenswürdige Personen
2. Rolle `admin` zuweisen
3. Starkes Passwort erzwingen

### Bulk-Import (falls viele User)

**Scalekit Dashboard:**
1. Users → Import
2. CSV hochladen:
   ```csv
   email,name,role
   student1@school.com,Student One,student
   student2@school.com,Student Two,student
   teacher1@school.com,Teacher One,teacher
   ```
3. Import starten

---

## 📝 Nächste Schritte

### 1. Test-User anlegen ⚠️

**Jetzt:**
1. Scalekit Dashboard öffnen
2. 2-3 Test-User anlegen (student, teacher)
3. Rollen zuweisen

### 2. End-to-End Test ⚠️

**Jetzt:**
1. Browser-Test: `https://leowiki-mcp.stream/auth/login`
2. Token erhalten und prüfen
3. Claude Desktop Integration testen

### 3. RBAC Test ⚠️

**Jetzt:**
1. Als Student einloggen → nur Student-Content sehen
2. Als Teacher einloggen → Student + Teacher Content sehen
3. Logs prüfen

### 4. Produktions-User vorbereiten ⏳

**Später:**
1. User-Liste von Schule erhalten
2. Bulk-Import in Scalekit
3. Initiale Passwörter versenden

---

## ✅ Checkliste

### Konfiguration
- [x] Scalekit Account erstellt
- [x] Environment konfiguriert
- [x] Client ID & Secret in `.env`
- [x] Redirect URI konfiguriert
- [x] OAuth Flow implementiert
- [x] JWT Validation implementiert
- [x] RBAC Middleware implementiert
- [x] `ENABLE_AUTH=true` aktiviert

### Testing
- [ ] Test-User angelegt (student, teacher)
- [ ] Browser OAuth Flow getestet
- [ ] Claude Desktop Integration getestet
- [ ] RBAC Student-Filter getestet
- [ ] RBAC Teacher-Filter getestet
- [ ] Token Expiration getestet
- [ ] Invalid Token getestet

### Produktion
- [ ] Produktions-User angelegt
- [ ] Initiale Passwörter versendet
- [ ] User-Dokumentation erstellt
- [ ] Support-Prozess definiert

---

## 📚 Weitere Dokumentation

- **OAuth Flow:** `docs/OAUTH_RBAC_COMPLETE_GUIDE.md`
- **Sicherheit:** `docs/SECURITY_HARDENING.md`
- **Code:** `src/auth/oauth_flow.py`, `src/auth/scalekit_client.py`

---

## 🎯 Zusammenfassung

**Status:** 🟡 **Konfiguration komplett, Testing ausstehend**

**Was funktioniert:**
- ✅ OAuth Flow implementiert
- ✅ JWT Validation implementiert
- ✅ RBAC implementiert
- ✅ Sicherheit gehärtet

**Was noch zu tun ist:**
- ⚠️ Test-User anlegen
- ⚠️ End-to-End Tests durchführen
- ⚠️ Claude Desktop Integration testen

**Nächster Schritt:** Test-User in Scalekit Dashboard anlegen und OAuth Flow testen!
