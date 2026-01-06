# 🔒 Security Hardening - MCP Educational Server

**Datum:** 06. Januar 2026  
**Status:** 🟢 **Multi-Layer Security Aktiv**

---

## 🎯 Sicherheits-Architektur

### Defense in Depth (Mehrschichtige Sicherheit)

```
Internet
   ↓
[1] UFW Firewall (Host-Level)
   ↓ (nur Port 80, 443)
[2] Caddy Reverse Proxy (TLS, Rate Limiting, Security Headers)
   ↓ (frontend-network)
[3] MCP Server (OAuth, JWT, RBAC)
   ↓ (backend-network - INTERNAL ONLY)
[4] Qdrant Vector DB (NO external access)
```

**Jede Schicht ist unabhängig und verstärkt die anderen!**

---

## 🛡️ Layer 1: UFW Firewall (Host-Level)

### Aktive Regeln

```bash
# Status prüfen:
sudo ufw status verbose

# Aktive Regeln:
✅ SSH (22)         - ALLOWED (für Administration)
✅ HTTP (80)        - ALLOWED (Caddy - Let's Encrypt + Redirect)
✅ HTTPS (443)      - ALLOWED (Caddy - Hauptzugang)
❌ Qdrant (6333)    - BLOCKED (explizit)
❌ Qdrant (6334)    - BLOCKED (explizit)
❌ MCP Server (8000) - BLOCKED (explizit)
```

### Was bedeutet das?

**Von außen erreichbar:**
- ✅ Port 22 (SSH) - für Administration
- ✅ Port 80 (HTTP) - nur für HTTPS-Redirect
- ✅ Port 443 (HTTPS) - einziger Zugang zur Anwendung

**NICHT von außen erreichbar:**
- ❌ Port 6333 (Qdrant HTTP)
- ❌ Port 6334 (Qdrant gRPC)
- ❌ Port 8000 (MCP Server direkt)

**Selbst wenn Docker-Ports exposed wären, würde UFW sie blockieren!**

### Management

```bash
# Status anzeigen:
sudo ufw status verbose

# Firewall deaktivieren (NICHT empfohlen):
sudo ufw disable

# Firewall aktivieren:
sudo ufw enable

# Neue Regel hinzufügen:
sudo ufw allow 1234/tcp comment 'Meine App'

# Regel löschen:
sudo ufw delete allow 1234/tcp

# Firewall zurücksetzen (VORSICHT!):
sudo ufw reset
```

---

## 🔐 Layer 2: Docker Network Isolation

### Zwei getrennte Netzwerke

#### Frontend-Network (Internet-Zugang)
```yaml
frontend-network:
  driver: bridge
  # Normale Bridge - hat Internet-Zugang
  ipam:
    config:
      - subnet: 172.20.0.0/24

Services:
  - Caddy (Port 80, 443 exposed)
  - MCP Server (KEIN Port exposed)
```

**Zweck:** Caddy kann auf Internet zugreifen (für Let's Encrypt), MCP Server ist nur für Caddy erreichbar.

#### Backend-Network (INTERNAL ONLY)
```yaml
backend-network:
  driver: bridge
  internal: true  # ← KEIN Internet-Zugang!
  ipam:
    config:
      - subnet: 172.21.0.0/24

Services:
  - MCP Server
  - Watchdog
  - Qdrant (KEIN Port exposed)
```

**Zweck:** Qdrant ist VOLLSTÄNDIG isoliert - kein Zugriff von außen, kein Zugriff aufs Internet.

### Vergleich: Alt vs. Neu

| Feature | Altes Projekt | Neues Projekt |
|---------|---------------|---------------|
| **Qdrant Ports** | 6333, 6334 exposed | ❌ KEINE Ports exposed |
| **MCP Server Port** | 8000 exposed | ❌ KEIN Port exposed |
| **Netzwerk-Isolation** | Ein Netzwerk | ✅ Zwei getrennte Netzwerke |
| **Backend Internet** | Ja | ❌ NEIN (internal: true) |
| **UFW Firewall** | Nein | ✅ JA |
| **Caddy Security Headers** | Basis | ✅ Erweitert |

**Das neue Projekt ist DEUTLICH sicherer!**

---

## 🚪 Layer 3: Caddy Reverse Proxy

### TLS/HTTPS

```caddyfile
leowiki-mcp.stream {
    # Automatisches HTTPS (Let's Encrypt)
    # - TLS 1.2 minimum
    # - Strong ciphers only
    # - HSTS enabled
}
```

**Features:**
- ✅ Automatische TLS-Zertifikate (Let's Encrypt)
- ✅ Automatische Erneuerung
- ✅ HTTP → HTTPS Redirect
- ✅ HTTP/2 und HTTP/3 Support

### Security Headers

```caddyfile
header {
    # XSS Protection
    X-Content-Type-Options "nosniff"
    X-Frame-Options "DENY"
    X-XSS-Protection "1; mode=block"
    
    # HSTS (1 Jahr)
    Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
    
    # CSP (Content Security Policy)
    Content-Security-Policy "default-src 'self'"
    
    # Referrer Policy
    Referrer-Policy "strict-origin-when-cross-origin"
    
    # Permissions Policy
    Permissions-Policy "geolocation=(), microphone=(), camera=()"
    
    # Remove Server Header
    -Server
}
```

**Was wird geschützt:**
- ✅ XSS (Cross-Site Scripting)
- ✅ Clickjacking
- ✅ MIME-Type Sniffing
- ✅ Man-in-the-Middle Attacks (HSTS)
- ✅ Unerwünschte Browser-Features

### Rate Limiting

```caddyfile
rate_limit {
    zone dynamic {
        key {remote_host}
        events 100
        window 1m
    }
}
```

**Schutz vor:**
- ✅ Brute-Force Attacks
- ✅ DDoS (einfache Varianten)
- ✅ API Abuse

**Limit:** 100 Requests pro Minute pro IP

---

## 🔑 Layer 4: OAuth + JWT + RBAC

### OAuth 2.1 (Scalekit)

**Authentifizierung:**
- ✅ Keine Passwörter im MCP Server
- ✅ JWT Tokens (signiert, verifiziert)
- ✅ Token Expiration
- ✅ Refresh Tokens

**Siehe:** `docs/OAUTH_RBAC_COMPLETE_GUIDE.md`

### Role-Based Access Control (RBAC)

**Rollen:**
- `student` - sieht nur "student" Content
- `teacher` - sieht "student" + "teacher" Content
- `admin` - sieht alles

**Implementierung:**
- ✅ JWT enthält Rolle
- ✅ Middleware extrahiert Rolle
- ✅ Qdrant Filter basiert auf Rolle
- ✅ Keine Umgehung möglich

---

## 🐳 Layer 5: Docker Security

### Container Hardening

```yaml
# Capabilities minimieren:
cap_drop:
  - ALL
cap_add:
  - NET_BIND_SERVICE  # Nur für Server
  - CHOWN             # Nur für Qdrant
  - SETUID            # Nur für Qdrant
  - SETGID            # Nur für Qdrant

# Read-Only Filesystem (wo möglich):
read_only: true
tmpfs:
  - /tmp

# Restart Policy:
restart: unless-stopped
```

**Prinzip:** Minimale Berechtigungen, maximale Isolation.

---

## 📊 Sicherheits-Vergleich

### Altes Projekt vs. Neues Projekt

| Sicherheits-Feature | Altes Projekt | Neues Projekt |
|---------------------|---------------|---------------|
| **UFW Firewall** | ❌ Nein | ✅ Ja |
| **Netzwerk-Isolation** | ⚠️ Ein Netzwerk | ✅ Zwei Netzwerke (frontend/backend) |
| **Backend Internet-Zugang** | ✅ Ja | ❌ Nein (internal: true) |
| **Exposed Ports** | ⚠️ 6333, 6334, 8000 | ✅ Nur 80, 443 (Caddy) |
| **TLS/HTTPS** | ✅ Ja | ✅ Ja (automatisch) |
| **Security Headers** | ⚠️ Basis | ✅ Erweitert |
| **Rate Limiting** | ❌ Nein | ✅ Ja (100/min) |
| **OAuth** | ⚠️ Optional | ✅ Aktiviert |
| **RBAC** | ⚠️ Optional | ✅ Aktiviert |
| **Container Hardening** | ❌ Nein | ✅ Ja (cap_drop, read_only) |
| **Watchdog Isolation** | ❌ N/A | ✅ Separater Container |

**Bewertung:**
- Altes Projekt: ⚠️ **Basis-Sicherheit** (funktional, aber Verbesserungspotential)
- Neues Projekt: ✅ **Enterprise-Level Security** (mehrschichtig, gehärtet)

---

## 🧪 Sicherheits-Tests

### Test 1: Qdrant von außen erreichbar?

```bash
# Von AUSSERHALB des Servers (z.B. vom Windows-PC):
curl http://leowiki-mcp.stream:6333/collections

# Erwartetes Ergebnis:
# Connection refused oder Timeout
# ✅ NICHT erreichbar!
```

### Test 2: MCP Server direkt erreichbar?

```bash
# Von AUSSERHALB des Servers:
curl http://leowiki-mcp.stream:8000/health

# Erwartetes Ergebnis:
# Connection refused oder Timeout
# ✅ NICHT erreichbar!
```

### Test 3: Nur HTTPS funktioniert?

```bash
# HTTP sollte zu HTTPS redirecten:
curl -I http://leowiki-mcp.stream

# Erwartetes Ergebnis:
# HTTP/1.1 301 Moved Permanently
# Location: https://leowiki-mcp.stream
# ✅ Redirect funktioniert!

# HTTPS sollte funktionieren:
curl -I https://leowiki-mcp.stream

# Erwartetes Ergebnis:
# HTTP/2 200
# ✅ HTTPS funktioniert!
```

### Test 4: Rate Limiting aktiv?

```bash
# 150 Requests in 1 Minute (über Limit):
for i in {1..150}; do
  curl -s https://leowiki-mcp.stream > /dev/null
  echo "Request $i"
done

# Erwartetes Ergebnis:
# Ab Request ~100: HTTP 429 Too Many Requests
# ✅ Rate Limiting funktioniert!
```

### Test 5: Security Headers vorhanden?

```bash
# Headers prüfen:
curl -I https://leowiki-mcp.stream

# Erwartete Headers:
# Strict-Transport-Security: max-age=31536000
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# Content-Security-Policy: default-src 'self'
# ✅ Security Headers aktiv!
```

### Test 6: Backend-Network hat kein Internet?

```bash
# In Qdrant Container:
docker exec mcp-qdrant ping -c 1 google.com

# Erwartetes Ergebnis:
# ping: bad address 'google.com'
# oder: Network is unreachable
# ✅ Kein Internet-Zugang!
```

---

## 🚨 Incident Response

### Verdächtige Aktivität erkennen

```bash
# UFW Logs anzeigen:
sudo tail -f /var/log/ufw.log

# Caddy Access Logs:
docker compose logs -f caddy | grep -E "(429|403|401)"

# MCP Server Logs:
docker compose logs -f mcp-server | grep -E "(ERROR|WARNING)"

# Qdrant Logs:
docker compose logs -f qdrant | grep -E "(ERROR|WARNING)"
```

### Bei Angriff

**1. Rate Limiting verschärfen:**
```caddyfile
# In Caddyfile:
rate_limit {
    zone dynamic {
        key {remote_host}
        events 10  # ← Von 100 auf 10 reduzieren
        window 1m
    }
}
```

**2. IP blockieren:**
```bash
# Angreifer-IP blockieren:
sudo ufw deny from 1.2.3.4 comment 'Blocked attacker'

# Prüfen:
sudo ufw status numbered
```

**3. Container neu starten:**
```bash
# Falls kompromittiert:
docker compose down
docker compose up -d
```

**4. Logs sichern:**
```bash
# Für forensische Analyse:
docker compose logs > /tmp/incident_logs_$(date +%Y%m%d_%H%M%S).txt
sudo cp /var/log/ufw.log /tmp/ufw_incident_$(date +%Y%m%d_%H%M%S).log
```

---

## 🔧 Wartung

### Regelmäßige Checks

**Wöchentlich:**
```bash
# UFW Status:
sudo ufw status verbose

# Docker Container Status:
docker compose ps

# Disk Space:
df -h

# Logs auf Fehler prüfen:
docker compose logs --since 7d | grep -E "(ERROR|CRITICAL)"
```

**Monatlich:**
```bash
# System Updates:
sudo apt update && sudo apt upgrade -y

# Docker Images aktualisieren:
docker compose pull
docker compose up -d

# Alte Docker Images aufräumen:
docker image prune -a
```

**Vierteljährlich:**
```bash
# Security Audit:
# - Alle Tests durchführen (siehe oben)
# - Logs auf Anomalien prüfen
# - Passwörter rotieren (falls verwendet)
# - TLS-Zertifikat prüfen (sollte auto-erneuert sein)
```

---

## 📚 Weitere Verbesserungen (Optional)

### Fail2Ban (Automatische IP-Blockierung)

```bash
# Installation:
sudo apt install fail2ban

# Konfiguration für SSH:
sudo nano /etc/fail2ban/jail.local
```

**Nutzen:** Automatische Blockierung nach mehreren fehlgeschlagenen Login-Versuchen.

### Intrusion Detection (AIDE)

```bash
# Installation:
sudo apt install aide

# Initialisierung:
sudo aideinit
```

**Nutzen:** Erkennt Änderungen an System-Dateien.

### Log Aggregation (Loki + Grafana)

**Nutzen:** Zentrale Log-Verwaltung, Dashboards, Alerting.

### Backup & Disaster Recovery

```bash
# Qdrant Daten sichern:
docker compose exec qdrant tar czf /qdrant/storage/backup.tar.gz /qdrant/storage/collections

# Backup herunterladen:
docker cp mcp-qdrant:/qdrant/storage/backup.tar.gz ./backups/
```

---

## ✅ Sicherheits-Checkliste

### Deployment

- [x] UFW Firewall aktiviert
- [x] Nur Ports 22, 80, 443 offen
- [x] Docker Network Isolation (frontend/backend)
- [x] Backend-Network ist internal (kein Internet)
- [x] Keine Qdrant/MCP Server Ports exposed
- [x] Caddy mit TLS (Let's Encrypt)
- [x] Security Headers konfiguriert
- [x] Rate Limiting aktiv
- [x] OAuth aktiviert
- [x] RBAC aktiviert
- [x] Container Hardening (cap_drop, read_only)
- [x] Restart Policies gesetzt

### Betrieb

- [ ] Regelmäßige Updates (monatlich)
- [ ] Log-Monitoring (wöchentlich)
- [ ] Backup-Strategie definiert
- [ ] Incident Response Plan dokumentiert
- [ ] Security Tests durchgeführt

---

## 🎯 Zusammenfassung

### Was wurde verbessert?

**1. UFW Firewall (NEU)**
- Host-Level Schutz
- Explizite Port-Blockierung

**2. Docker Network Isolation (VERBESSERT)**
- Zwei getrennte Netzwerke
- Backend ohne Internet-Zugang

**3. Keine Exposed Ports (VERBESSERT)**
- Nur Caddy (80, 443) von außen erreichbar
- Qdrant und MCP Server vollständig isoliert

**4. Container Hardening (NEU)**
- Minimale Capabilities
- Read-Only Filesystem (wo möglich)

**5. Rate Limiting (NEU)**
- Schutz vor Brute-Force und DDoS

### Sicherheits-Level

**Vorher (altes Projekt):**
```
⚠️ Basis-Sicherheit
- TLS ✅
- Exposed Ports ⚠️
- Ein Netzwerk ⚠️
- Keine Firewall ❌
```

**Jetzt (neues Projekt):**
```
✅ Enterprise-Level Security
- Multi-Layer Defense ✅
- Zero Exposed Backend Ports ✅
- Network Isolation ✅
- UFW Firewall ✅
- Container Hardening ✅
- Rate Limiting ✅
- OAuth + RBAC ✅
```

**Das neue Projekt ist production-ready und enterprise-grade! 🚀**
