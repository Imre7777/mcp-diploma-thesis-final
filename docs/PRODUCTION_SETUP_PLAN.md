# 🚀 Production Setup Plan - Final Schritte

**Datum:** 06. Januar 2026  
**Server:** leowiki-mcp.stream (Raspberry Pi)  
**Status:** OAuth aktiviert ✅ - Jetzt: Sicherheit, Tailscale & Scalekit

---

## 📋 Übersicht der 3 Hauptaufgaben

| # | Aufgabe | Status | Priorität | Geschätzte Zeit |
|---|---------|--------|-----------|-----------------|
| 1 | **Serversicherheit verbessern** | 🟡 In Planung | Hoch | 1-2 Stunden |
| 2 | **Tailscale Setup** | 🟢 Bereit | **HÖCHSTE** | 30-45 Min |
| 3 | **Scalekit finales Setup** | 🟡 Geplant | Hoch | 1 Stunde |

---

## 🔐 Teil 1: Serversicherheit - Vergleich & Verbesserungen

### 📊 Status Quo vs. Altes Projekt

#### **Aktuelles Projekt (mcp-diploma-thesis-final):**

```yaml
# docker-compose.yml
networks:
  mcp-network:
    driver: bridge    # Ein einziges Netzwerk für alle Container

services:
  qdrant:      # Port 6334, 6333 → Exposed!
  mcp-server:  # Port 8000 → Exposed!
  caddy:       # Port 80, 443 → Exposed (OK)
```

**Alle Container im gleichen Netzwerk:**
```
┌─────────────────────────────────────────┐
│         mcp-network (bridge)            │
│                                         │
│  ┌──────┐  ┌───────────┐  ┌──────┐   │
│  │Qdrant│◄─┤MCP Server │◄─┤Caddy │   │
│  └──────┘  └───────────┘  └──────┘   │
│     ▲           ▲             ▲        │
│     │           │             │        │
│  6334,6333    8000        80,443      │
└─────────────────────────────────────────┘
         ▼           ▼             ▼
    ALLE PORTS EXPOSED ZUM HOST!
```

#### **Altes Projekt (mcp-vector-server-backup):**

Hatte wahrscheinlich:
```yaml
# Vermutung: Getrenntes internes Netzwerk
networks:
  frontend-network:   # Caddy ↔ MCP Server
  backend-network:    # MCP Server ↔ Qdrant (intern!)
```

**Vorteil:** Qdrant war NICHT von außen erreichbar!

```
┌─────────────────────────┐  ┌──────────────────┐
│  frontend-network       │  │ backend-network  │
│                         │  │  (intern only)   │
│  ┌──────┐  ┌────────┐  │  │  ┌──────┐        │
│  │Caddy │◄─┤MCP Srv │◄─┼──┼─►│Qdrant│        │
│  └──────┘  └────────┘  │  │  └──────┘        │
│     ▲                   │  │                  │
│  80,443                 │  │  (no ports!)     │
└─────────────────────────┘  └──────────────────┘
```

### 🔒 Sicherheitsverbesserungen

#### **Option 1: Ports von Host entfernen (EMPFOHLEN)**

```yaml
# docker-compose.yml - VERBESSERT
services:
  qdrant:
    # ports:  # ← ENTFERNEN! Nur intern erreichbar
    #   - "6334:6334"
    #   - "6333:6333"
    expose:  # ← Stattdessen: nur innerhalb Docker-Netzwerk
      - "6334"
      - "6333"
    networks:
      - backend-network  # Separates Netzwerk
  
  mcp-server:
    # ports:  # ← ENTFERNEN!
    #   - "8000:8000"
    expose:
      - "8000"
    networks:
      - frontend-network
      - backend-network
  
  caddy:
    ports:  # NUR Caddy exponiert!
      - "80:80"
      - "443:443"
    networks:
      - frontend-network

networks:
  frontend-network:
    driver: bridge
  backend-network:
    driver: bridge
    internal: true  # ← WICHTIG: Kein Internet-Zugang!
```

**Vorteile:**
- ✅ Qdrant ist NICHT von außen erreichbar (auch nicht von localhost!)
- ✅ MCP Server ist NICHT direkt erreichbar (nur via Caddy)
- ✅ Nur Caddy (Port 80/443) ist exponiert
- ✅ Bessere Isolation zwischen Services

#### **Option 2: Firewall-Regeln (zusätzlich)**

```bash
# UFW Firewall auf Raspberry Pi
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 22/tcp    # SSH (für Management)
sudo ufw enable

# Qdrant Port 6333/6334 ist NICHT erlaubt → blockiert!
```

#### **Option 3: Docker Network Policies (erweitert)**

```yaml
# docker-compose.yml
services:
  qdrant:
    networks:
      backend-network:
        ipv4_address: 172.25.0.10
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETUID
      - SETGID

networks:
  backend-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.25.0.0/24
    driver_opts:
      com.docker.network.bridge.enable_ip_masquerade: "false"
```

### 📊 Sicherheits-Checkliste

| Maßnahme | Aktuell | Empfohlen | Status |
|----------|---------|-----------|--------|
| **Qdrant Port exposed** | ❌ 6334, 6333 | ✅ Nur intern | 🔴 TODO |
| **MCP Server Port exposed** | ❌ 8000 | ✅ Nur intern | 🔴 TODO |
| **Separate Netzwerke** | ❌ Ein Netzwerk | ✅ Frontend/Backend | 🔴 TODO |
| **Firewall aktiv** | ❓ Unbekannt | ✅ UFW enabled | 🔴 TODO |
| **HTTPS (Caddy)** | ✅ Let's Encrypt | ✅ | ✅ DONE |
| **OAuth Authentication** | ✅ Scalekit | ✅ | ✅ DONE |
| **Container Capabilities** | ⚠️ Default | ✅ Minimal | 🔴 TODO |
| **Read-only Filesystem** | ❌ | ✅ Für Caddy/Qdrant | 🟡 Optional |

### 🎯 Implementierungsplan Sicherheit

**Schritt 1:** Netzwerk-Isolation (15 Min)
```bash
# Neue docker-compose.yml mit getrennten Netzwerken erstellen
# Ports von Qdrant & MCP Server entfernen
# Nur Caddy exponiert Ports 80/443
```

**Schritt 2:** Firewall Setup (10 Min)
```bash
# UFW aktivieren und konfigurieren
# Nur notwendige Ports öffnen
```

**Schritt 3:** Testing (15 Min)
```bash
# Überprüfen, dass Qdrant von außen NICHT erreichbar ist
# Überprüfen, dass MCP Server nur via Caddy erreichbar ist
# Überprüfen, dass HTTPS funktioniert
```

---

## 🌐 Teil 2: Tailscale Setup (HÖCHSTE PRIORITÄT)

### 📊 Ist-Situation

✅ **Kollege hat bereits:**
- Tailscale Account erstellt
- Credentials vorhanden
- Dashboard-Zugriff
- Seinen PC sieht er im Dashboard

❌ **Raspberry Pi:**
- Tailscale NOCH NICHT installiert
- NICHT im Tailscale-Netzwerk
- Kollege kann Pi NICHT sehen

### 🎯 Ziel

```
Kollege's PC (Tailscale: 100.x.x.1)
        ↓ (encrypted VPN tunnel)
Raspberry Pi (Tailscale: 100.x.x.2)
        ↓ (SCP Upload)
/home/imreo/mcp-diploma-thesis-final/data/incoming/
        ↓ (Automatic Ingestion)
Qdrant Vector Database
```

### 🚀 Implementierungsplan Tailscale

#### **Schritt 1: Tailscale auf Raspberry Pi installieren** (5 Min)

```bash
# SSH zum Pi
ssh imreo@leowiki-mcp.stream

# Tailscale installieren
curl -fsSL https://tailscale.com/install.sh | sh

# Tailscale starten
sudo tailscale up

# WICHTIG: Browser-Link wird angezeigt!
# https://login.tailscale.com/a/XXXXXX
# → Link öffnen und mit GLEICHEM Account wie Kollege anmelden!
```

**Output:**
```
To authenticate, visit:
  https://login.tailscale.com/a/abc123def456

Success! You are now authenticated.
```

#### **Schritt 2: Tailscale IP ermitteln** (1 Min)

```bash
# Tailscale IPv4-Adresse
tailscale ip -4

# Beispiel Output: 100.101.102.103
```

#### **Schritt 3: Hostname setzen (Optional aber empfohlen)** (2 Min)

```bash
# Im Tailscale Dashboard:
# Devices → Raspberry Pi → Settings → Device name: "mcp-pi"

# Dann kann Kollege verwenden:
scp file.jsonl imreo@mcp-pi:/home/imreo/mcp-diploma-thesis-final/data/incoming/
# Statt:
scp file.jsonl imreo@100.101.102.103:/home/imreo/...
```

#### **Schritt 4: SSH-Zugriff testen** (5 Min)

```bash
# Vom Kollegen's PC (muss auch Tailscale laufen haben):
ssh imreo@100.101.102.103
# Oder:
ssh imreo@mcp-pi

# Wenn funktioniert: ✅ Verbindung steht!
```

#### **Schritt 5: Verzeichnis-Berechtigungen prüfen** (2 Min)

```bash
# Auf dem Pi:
ls -ld /home/imreo/mcp-diploma-thesis-final/data/incoming/

# Sollte sein:
drwxrwxr-x imreo imreo ... data/incoming/

# Falls nicht:
chmod 775 /home/imreo/mcp-diploma-thesis-final/data/incoming/
```

#### **Schritt 6: SSH-Key Setup für Kollegen (Optional aber empfohlen)** (10 Min)

```bash
# Kollege generiert SSH-Key (falls noch nicht vorhanden):
ssh-keygen -t ed25519 -C "colleague@email.com"

# Kollege sendet public key (id_ed25519.pub) an dich
# Du fügst ihn zum Pi hinzu:
ssh imreo@leowiki-mcp.stream
nano ~/.ssh/authorized_keys
# → Public key einfügen und speichern

# Jetzt kann Kollege OHNE Passwort uploaden!
```

#### **Schritt 7: Test-Upload durchführen** (5 Min)

```bash
# Kollege erstellt Test-Datei:
echo '{"id": "test_001", "title": "Test", "content": "Test content", "metadata": {"frontmatter": {"access_level": "student"}}}' > test.jsonl

# Upload via Tailscale:
scp test.jsonl imreo@mcp-pi:/home/imreo/mcp-diploma-thesis-final/data/incoming/

# Auf Pi überprüfen:
ls -lh /home/imreo/mcp-diploma-thesis-final/data/incoming/
# → test.jsonl sollte da sein!
```

#### **Schritt 8: Automatische Ingestion sicherstellen** (Variable Zeit)

**Option A: Manuell** (aktuell)
```bash
# Nach Upload manuell ausführen:
cd /home/imreo/mcp-diploma-thesis-final
python scripts/ingest_full_data.py
```

**Option B: Watchdog Service (empfohlen für Kollegen!)** 
```yaml
# Zu docker-compose.yml hinzufügen:
  data-watcher:
    build: .
    container_name: mcp-data-watcher
    restart: unless-stopped
    command: python -m src.pipeline.watchdog
    volumes:
      - ./data/incoming:/app/data/incoming
      - ./data/processed:/app/data/processed
      - ./data/failed:/app/data/failed
    environment:
      - VECTOR_DB_URL=http://qdrant:6334
      - DEFAULT_COLLECTION=educational_content
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - qdrant
    networks:
      - mcp-network
```

**Vorteil:** Datei wird automatisch verarbeitet sobald sie in `incoming/` landet!

#### **Schritt 9: Kollegen-Dokumentation erstellen** (10 Min)

Erstelle: `docs/COLLEAGUE_TAILSCALE_GUIDE.md` mit:
- Tailscale Download-Link
- Pi's Tailscale-IP
- SCP Upload-Befehl
- JSONL Format-Beispiel
- Troubleshooting

### 📋 Tailscale Checkliste

- [ ] Tailscale auf Pi installiert
- [ ] Tailscale gestartet und authenticated
- [ ] Tailscale IP ermittelt: `_____________________`
- [ ] Hostname "mcp-pi" gesetzt (optional)
- [ ] Kollege kann Pi via Tailscale erreichen (SSH-Test)
- [ ] Verzeichnis-Berechtigungen korrekt
- [ ] SSH-Key für Kollegen eingerichtet (optional)
- [ ] Test-Upload durchgeführt und erfolgreich
- [ ] Automatic Ingestion funktioniert (watchdog oder manuell)
- [ ] Kollegen-Dokumentation erstellt

### 🔐 Tailscale Sicherheits-Features

**ACL (Access Control List) - Optional:**

Im Tailscale Dashboard → Settings → Access Controls:

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["colleague@email.com"],
      "dst": ["mcp-pi:22"]
    }
  ]
}
```

**Bedeutung:** Kollege darf NUR SSH (Port 22) zum Pi, sonst nichts!

---

## 👥 Teil 3: Scalekit Finales Setup

### 📊 Status Quo

✅ **Bereits konfiguriert:**
- Scalekit Environment URL: `https://mcpeduauth.scalekit.dev`
- Client ID: `skc_35934031996379566`
- Client Secret: (in .env)
- OAuth Flow implementiert (in `src/auth/oauth_flow.py`)
- Middleware aktiviert
- Server läuft mit `ENABLE_AUTH=true`

❌ **Noch zu erledigen:**
- Test-Users anlegen (Student, Teacher, Admin)
- OAuth Flow End-to-End testen
- Claude Desktop Config testen
- Redirect URIs finalisieren
- Production Users anlegen

### 🎯 Implementierungsplan Scalekit

#### **Schritt 1: Scalekit Dashboard konfigurieren** (15 Min)

**1.1 Login zu Scalekit**
```
URL: https://app.scalekit.com
Oder direkt: https://mcpeduauth.scalekit.dev
```

**1.2 Redirect URIs konfigurieren**
```
Navigate to: Applications → MCP Educational Server → OAuth Settings

Add Redirect URIs:
✅ https://leowiki-mcp.stream/auth/callback
✅ http://localhost:8000/auth/callback  (für lokales Testing)
```

**1.3 Allowed Origins**
```
Add CORS Origins:
✅ https://leowiki-mcp.stream
✅ http://localhost:8000
```

#### **Schritt 2: Test-Users anlegen** (15 Min)

**Im Scalekit Dashboard → Users → Create User**

**User 1: Student**
```
Email: student@test.htl-leonding.at
Name: Max Mustermann
Password: TestStudent123!
Roles: ["student"]
Organization: HTL Leonding Test
```

**User 2: Teacher**
```
Email: teacher@test.htl-leonding.at
Name: Prof. Müller
Password: TestTeacher123!
Roles: ["teacher"]
Organization: HTL Leonding Test
```

**User 3: Admin**
```
Email: admin@test.htl-leonding.at
Name: Admin User
Password: TestAdmin123!
Roles: ["admin"]
Organization: HTL Leonding Test
```

#### **Schritt 3: OAuth Flow testen** (20 Min)

**3.1 Browser-Test**

```bash
# Öffne im Browser:
https://leowiki-mcp.stream/auth/login

# Erwartung:
1. Redirect zu Scalekit Login-Seite
2. Login mit student@test.htl-leonding.at
3. Redirect zurück zu /auth/callback
4. JWT Token wird angezeigt
```

**3.2 Token validieren**

```bash
# Mit erhaltenem Token testen:
curl -X POST https://leowiki-mcp.stream/mcp \
  -H "Authorization: Bearer DEIN_TOKEN_HIER" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "search_content",
      "arguments": {
        "query": "test",
        "limit": 5
      }
    },
    "id": 1
  }'

# Erwartung: Suchergebnisse (mit Student-Filter)
```

**3.3 Role-Based Access testen**

```bash
# Als Student einloggen → Token erhalten
# Suche mit Student-Token → Nur student-level Dokumente

# Als Teacher einloggen → Token erhalten
# Suche mit Teacher-Token → student + teacher Dokumente
```

#### **Schritt 4: Claude Desktop Integration testen** (20 Min)

**4.1 Claude Desktop Config**

Erstelle/Update: `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

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

**4.2 Claude Desktop testen**

```
1. Claude Desktop neu starten
2. Browser sollte sich öffnen mit Scalekit Login
3. Mit student@test.htl-leonding.at anmelden
4. Claude Desktop sollte verbunden sein
5. Test-Abfrage: "Suche nach Python"
```

#### **Schritt 5: Production Users anlegen** (Variable Zeit)

**Option A: Manuell im Dashboard**
- Pro User im Scalekit Dashboard erstellen
- Email, Name, Rolle zuweisen

**Option B: CSV Import**
```csv
email,name,role,organization
schueler1@htl-leonding.at,Max M.,student,HTL Leonding
schueler2@htl-leonding.at,Anna S.,student,HTL Leonding
lehrer1@htl-leonding.at,Prof. M.,teacher,HTL Leonding
...
```

**Option C: Via API** (für viele User)
```python
# Script erstellen: scripts/create_scalekit_users.py
from scalekit import ScalekitClient

client = ScalekitClient(...)

users = [
    {"email": "...", "name": "...", "role": "student"},
    # ...
]

for user_data in users:
    client.users.create(user_data)
```

#### **Schritt 6: Email-Vorlagen vorbereiten** (10 Min)

**Email-Template für User:**

```
Betreff: MCP Educational Server - Zugang

Hallo [Name],

Sie haben Zugang zum MCP Educational Server erhalten.

1. Installation:
   - Claude Desktop: https://claude.ai/download

2. Konfiguration:
   - Config-Datei: %APPDATA%\Claude\claude_desktop_config.json
   - Code: [siehe Anhang]

3. Login:
   - Email: [user@htl-leonding.at]
   - Passwort: [initial_password]
   - Bitte nach erstem Login ändern!

4. Erste Schritte:
   - Claude Desktop öffnen
   - Browser-Login wird automatisch geöffnet
   - Credentials eingeben
   - Fertig!

Bei Fragen: imre.obermueller@gmail.com

Viel Erfolg!
```

### 📋 Scalekit Setup Checkliste

- [ ] Scalekit Dashboard Login erfolgreich
- [ ] Redirect URIs konfiguriert (production + localhost)
- [ ] CORS Origins konfiguriert
- [ ] Test-User Student angelegt
- [ ] Test-User Teacher angelegt
- [ ] Test-User Admin angelegt
- [ ] OAuth Flow Browser-Test erfolgreich
- [ ] Token Validierung funktioniert
- [ ] RBAC funktioniert (Student sieht nur student-level)
- [ ] Claude Desktop Config erstellt
- [ ] Claude Desktop OAuth Flow erfolgreich
- [ ] Production Users angelegt
- [ ] Email-Templates vorbereitet
- [ ] User-Dokumentation erstellt

---

## 📊 Gesamter Zeitplan

| Phase | Aufgaben | Geschätzte Zeit | Abhängigkeiten |
|-------|----------|----------------|----------------|
| **Phase 1: Tailscale** | Setup, Testing, Dokumentation | 30-45 Min | Keine |
| **Phase 2: Sicherheit** | Netzwerk-Isolation, Firewall | 1-2 Std | Nach Tailscale |
| **Phase 3: Scalekit** | User-Anlage, Testing | 1 Std | Unabhängig |

**Empfohlene Reihenfolge:**
1. **Tailscale zuerst** (höchste Priorität, Kollege wartet!)
2. **Scalekit parallel** (kann während Tailscale-Tests gemacht werden)
3. **Sicherheit zuletzt** (erfordert System-Neustart)

---

## 🚦 Nächste Schritte

### **JETZT: Tailscale Setup beginnen**

```bash
# 1. SSH zum Pi
ssh imreo@leowiki-mcp.stream

# 2. Tailscale installieren
curl -fsSL https://tailscale.com/install.sh | sh

# 3. Starten und authentifizieren
sudo tailscale up
```

**Dann melden wir uns zurück mit:**
- ✅ Tailscale IP-Adresse
- ✅ Test-Upload erfolgreich
- ✅ Kollegen-Dokumentation

**Bereit? Let's go! 🚀**
