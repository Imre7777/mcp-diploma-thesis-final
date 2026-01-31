# ⚡ QUICK REFERENCE - MCP Diploma Thesis

**Schnellzugriff für tägliche Operationen**

---

## 🚀 SYSTEM STARTEN/STOPPEN

```bash
cd /home/imreo/mcp-diploma-thesis-final

# Starten
docker compose up -d

# Stoppen
docker compose stop

# Neu starten
docker compose restart

# Komplett herunterfahren
docker compose down

# Status
docker compose ps
```

---

## 🔍 LOGS ANZEIGEN

```bash
# Alle Logs (live)
docker compose logs -f

# Nur MCP Server
docker compose logs -f mcp-server

# Letzte 50 Zeilen
docker compose logs --tail=50

# Fehler suchen
docker compose logs | grep -i error
```

---

## 🧪 HEALTH CHECKS

```bash
# MCP Server
curl http://localhost:8000/health

# Qdrant
curl http://localhost:6333/healthz

# Production (HTTPS)
curl https://leowiki-mcp.stream/health

# Alle auf einmal
curl http://localhost:8000/health && \
curl http://localhost:6333/healthz && \
echo "✅ All healthy"
```

---

## 🔍 SEARCH TESTEN

```bash
# Einfache Suche
curl -X POST http://localhost:8000/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"search_content","arguments":{"query":"HTL","limit":3,"user_role":"student"}}'

# Collection Stats
curl -X POST http://localhost:8000/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"get_collection_stats","arguments":{}}'
```

---

## 📊 MONITORING

```bash
# Resource Usage (live)
docker stats

# Disk Usage
docker system df

# Container Details
docker inspect mcp-server
```

---

## 📁 DATA INGESTION

```bash
# Datei hochladen (ins incoming/)
cp your_data.jsonl data/incoming/

# Manuell verarbeiten
docker compose exec mcp-server python scripts/ingest_full_data.py data/incoming/your_data.jsonl

# Überprüfen
ls -lh data/processed/
ls -lh data/failed/
```

---

## 🔧 CONFIGURATION

```bash
# Environment anzeigen
docker compose exec mcp-server env | grep -E "(OPENAI|ENABLE|QDRANT)"

# .env editieren
nano .env

# Nach Änderung neu starten
docker compose restart mcp-server
```

---

## 🔐 OAUTH AN/AUS

```bash
# OAuth aktivieren
nano .env
# Ändere: ENABLE_AUTH=true
docker compose restart mcp-server

# OAuth deaktivieren
nano .env
# Ändere: ENABLE_AUTH=false
docker compose restart mcp-server

# Status überprüfen
docker compose logs mcp-server | grep -i auth
```

---

## 🌐 URLS

| Service | URL |
|---------|-----|
| **API Docs** | http://localhost:8000/docs |
| **Health** | http://localhost:8000/health |
| **Qdrant Dashboard** | http://localhost:6333/dashboard |
| **Production** | https://leowiki-mcp.stream |
| **OAuth Metadata** | http://localhost:8000/.well-known/oauth-protected-resource |

---

## 🆘 QUICK FIXES

### Container läuft nicht
```bash
docker compose restart <service-name>
# oder
docker compose down && docker compose up -d
```

### Logs voll
```bash
docker system prune -f
```

### Port belegt
```bash
sudo netstat -tlnp | grep 8000
docker compose down
docker compose up -d
```

### Rebuild nötig
```bash
docker compose down
docker compose build --no-cache mcp-server
docker compose up -d
```

---

## 📞 WICHTIGE BEFEHLE

```bash
# Shell in Container
docker compose exec mcp-server bash

# Python REPL
docker compose exec mcp-server python

# Qdrant Collection löschen (VORSICHT!)
curl -X DELETE http://localhost:6333/collections/educational_content

# Qdrant Collection neu erstellen
docker compose exec mcp-server python -c "from src.backends import create_vector_backend; create_vector_backend().create_collection()"
```

---

## ✅ DAILY CHECKLIST

```bash
# Morgens:
docker compose ps                    # Alles läuft?
curl http://localhost:8000/health    # Healthy?
docker compose logs --tail=20        # Errors?

# Abends:
docker compose logs --tail=50        # Was ist passiert?
docker stats --no-stream             # Resources OK?
```

---

## 🎯 TESTING SHORTCUTS

```bash
# Schnelltest
curl http://localhost:8000/health && echo " ✅"

# MCP Inspector
npx @modelcontextprotocol/inspector http://localhost:8000/mcp

# Performance Test
time curl -s http://localhost:8000/health > /dev/null
```

---

**💡 TIP:** Speichere diese Datei als Lesezeichen!

```bash
cat /home/imreo/mcp-diploma-thesis-final/QUICK_REFERENCE.md
```
