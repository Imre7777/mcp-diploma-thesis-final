# Testing & Deployment Guide - LeoWiki MCP Server

**Branch:** `feature/professional-mcp-enhancements`  
**Date:** 31. Januar 2026  
**Status:** Testing in Progress

---

## 🧪 Test-Status

### ✅ Abgeschlossen

1. **Syntax Check** - Alle Python-Dateien kompilieren erfolgreich
   - `src/server/lifespan.py` ✓
   - `src/middleware/mcp_middleware.py` ✓
   - `src/resources/*.py` ✓
   - `src/prompts/*.py` ✓
   - `src/tools/search_tools.py` ✓

### ⏳ In Bearbeitung

2. **Dependencies Installation** - Erforderlich vor weiteren Tests

### ⏹️ Ausstehend

3. Import Tests
4. Server Start Test
5. Grundfunktionalität Tests
6. Git Commit & Merge
7. Deployment

---

## 📦 Dependencies Installation

### Problem

Das System hat Python 3.11.2, aber `pip3` ist nicht direkt verfügbar.

### Lösung 1: pip3 installieren (Empfohlen)

```bash
# Als root oder mit sudo
sudo apt update
sudo apt install python3-pip

# Verifizieren
pip3 --version
```

### Lösung 2: Python -m pip verwenden

```bash
# Falls pip3 nicht funktioniert
python3 -m ensurepip --upgrade
python3 -m pip --version
```

### Dependencies installieren

```bash
cd /home/imreo/mcp-diploma-thesis-final

# Methode 1: Mit pip3
pip3 install -r requirements.txt

# Methode 2: Mit python3 -m pip
python3 -m pip install -r requirements.txt

# Oder: System-Packages (schneller auf Raspberry Pi)
sudo apt install \
    python3-fastapi \
    python3-pydantic \
    python3-httpx \
    python3-jwt \
    python3-cryptography

# Dann nur die spezifischen Packages mit pip
pip3 install --user fastmcp scalekit-sdk-python qdrant-client openai
```

---

## 🔍 Test-Prozedur (nach Dependencies)

### 1. Import Tests

```bash
cd /home/imreo/mcp-diploma-thesis-final

python3 << 'EOF'
import sys

# Test alle neuen Module
modules = [
    "src.server.lifespan",
    "src.middleware.mcp_middleware",
    "src.resources.metadata",
    "src.resources.content",
    "src.prompts.educational",
    "src.tools.search_tools",
]

for module in modules:
    try:
        __import__(module)
        print(f"✓ {module}")
    except Exception as e:
        print(f"✗ {module}: {e}")
        sys.exit(1)

print("\n✓ Alle Imports erfolgreich!")
EOF
```

### 2. Configuration Test

```bash
# Environment-Variablen prüfen
cd /home/imreo/mcp-diploma-thesis-final

# .env Datei muss existieren
if [ ! -f .env ]; then
    echo "⚠️  .env Datei fehlt - erstelle aus env.example"
    cp env.example .env
    echo "BITTE .env bearbeiten und Credentials eintragen!"
    exit 1
fi

# Prüfe kritische Variablen
python3 << 'EOF'
from src.config.server_config import ServerConfig

try:
    config = ServerConfig()
    print(f"✓ Server Name: {config.server_name}")
    print(f"✓ Port: {config.server_port}")
    print(f"✓ Qdrant URL: {config.vector_db_url}")
    print(f"✓ Auth Enabled: {config.enable_auth}")
    
    if config.enable_auth:
        print(f"✓ Scalekit URL: {config.scalekit_env_url}")
        print(f"✓ Client ID: {config.scalekit_client_id[:8]}...")
    
    print("\n✓ Configuration valid!")
except Exception as e:
    print(f"✗ Configuration error: {e}")
    exit(1)
EOF
```

### 3. Qdrant Connection Test

```bash
# Prüfe ob Qdrant läuft
docker ps | grep qdrant

# Wenn nicht, starte Qdrant
if [ $? -ne 0 ]; then
    echo "Starte Qdrant..."
    docker run -d --name qdrant-mcp-edu -p 6333:6333 -p 6334:6334 qdrant/qdrant
    sleep 5
fi

# Test Connection
python3 << 'EOF'
from qdrant_client import QdrantClient

try:
    client = QdrantClient(url="http://localhost:6333")
    collections = client.get_collections()
    print(f"✓ Qdrant verbunden")
    print(f"✓ Collections: {len(collections.collections)}")
    
    # Check for our collection
    our_collection = "educational_content"
    try:
        info = client.get_collection(our_collection)
        print(f"✓ Collection '{our_collection}' gefunden: {info.points_count} Dokumente")
    except:
        print(f"⚠️  Collection '{our_collection}' nicht gefunden - muss ingested werden")
    
except Exception as e:
    print(f"✗ Qdrant connection failed: {e}")
    print("Bitte sicherstellen dass Qdrant läuft: docker ps | grep qdrant")
    exit(1)
EOF
```

### 4. Server Dry-Run Test

```bash
# Test ob Server starten würde (ohne tatsächlich zu starten)
cd /home/imreo/mcp-diploma-thesis-final

python3 << 'EOF'
import sys
import logging

logging.basicConfig(level=logging.INFO)

try:
    # Import main components
    from main import mcp, app, config
    
    print(f"✓ Server-Name: {config.server_name}")
    print(f"✓ FastMCP initialisiert")
    print(f"✓ FastAPI initialisiert")
    
    # Check tools registered
    tools = list(mcp._tool_manager._tools.keys())
    print(f"✓ Tools registriert: {len(tools)}")
    for tool in tools:
        print(f"  - {tool}")
    
    print("\n✓ Server würde erfolgreich starten!")
    
except Exception as e:
    print(f"✗ Server initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF
```

### 5. Server Start Test (kurz)

```bash
# Starte Server für 10 Sekunden
cd /home/imreo/mcp-diploma-thesis-final

echo "Starte Server für 10 Sekunden..."
timeout 10 python3 main.py --http 2>&1 | tee server-test.log &

sleep 5

# Test Health Endpoint
curl -s http://localhost:8000/health | jq . || echo "Health check failed"

# Test OAuth Discovery
curl -s http://localhost:8000/.well-known/oauth-protected-resource | jq . || echo "OAuth discovery failed"

# Warte auf timeout
wait

echo "\n✓ Server Start Test complete - siehe server-test.log"
```

---

## 🚀 Deployment-Prozess

### Voraussetzungen

- ✅ Alle Tests bestanden
- ✅ Dependencies installiert
- ✅ Qdrant läuft
- ✅ .env konfiguriert

### Schritt 1: Git Commit

```bash
cd /home/imreo/mcp-diploma-thesis-final

# Status prüfen
git status

# Alle Änderungen stagen
git add .

# Commit mit aussagekräftiger Message
git commit -m "feat: professional MCP refactoring complete

- Implemented two-tool RBAC architecture (security by design)
- Added 6 MCP Resources (3 static, 3 dynamic)
- Added 5 Educational Prompts for LLM interactions
- Implemented 4 FastMCP Middleware components
- Added Lifespan pattern for dependency injection
- Enhanced with Tool Annotations and Progress Reporting
- Complete API documentation (docs/API.md)
- Authentication architecture documentation

Changes:
- New: src/server/lifespan.py
- New: src/middleware/mcp_middleware.py
- New: src/resources/ (metadata.py, content.py)
- New: src/prompts/educational.py
- Refactored: src/tools/search_tools.py (two separate tools)
- Enhanced: main.py (instructions, middleware, resources, prompts)
- Updated: README.md with MCP Capabilities section
- New: docs/API.md (835 lines comprehensive API docs)
- New: docs/AUTHENTICATION_ARCHITECTURE.md

Version: 2.0.0
Status: Ready for production
"

# Push zum remote (wenn gewünscht)
git push origin feature/professional-mcp-enhancements
```

### Schritt 2: Merge zu Main

```bash
# Prüfe aktuellen Branch
git branch

# Wechsle zu main
git checkout main

# Merge feature branch
git merge feature/professional-mcp-enhancements

# Bei Konflikten: manuell lösen, dann:
# git add <resolved-files>
# git commit

# Push to origin
git push origin main
```

### Schritt 3: Tag für Release

```bash
git tag -a v2.0.0 -m "Release 2.0.0: Professional MCP Refactoring

Major features:
- Two-tool RBAC architecture
- 6 MCP Resources + 5 Prompts
- 4 FastMCP Middleware components
- Complete documentation
"

git push origin v2.0.0
```

---

## 🐳 Docker Deployment (Optional)

### Lokaler Test mit Docker

```bash
cd /home/imreo/mcp-diploma-thesis-final

# Build Image
docker build -t mcp-educational-server:2.0.0 .

# Run Container
docker run -d \
  --name mcp-server \
  -p 8000:8000 \
  --env-file .env \
  mcp-educational-server:2.0.0

# Logs prüfen
docker logs -f mcp-server

# Test
curl http://localhost:8000/health
```

### Mit Docker Compose

```bash
# Start all services (Qdrant + MCP Server)
docker-compose up -d

# Logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## ✅ Post-Deployment Checks

### 1. Health Check

```bash
curl http://localhost:8000/health
# Erwartet: {"status": "healthy", ...}
```

### 2. OAuth Discovery

```bash
curl http://localhost:8000/.well-known/oauth-protected-resource
# Erwartet: {"resource": ..., "authorization_servers": ...}
```

### 3. MCP Tools Test (mit Auth Token)

```bash
# Erfordert gültigen Bearer Token
TOKEN="your-access-token-here"

curl -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
  }'

# Sollte Liste mit 3 Tools zurückgeben:
# - search_content_student
# - search_content_teacher
# - get_collection_stats
```

### 4. Resource Test

```bash
# Mit Token
curl -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "resources/list",
    "id": 1
  }'

# Sollte 6 Resources zurückgeben
```

### 5. Prompt Test

```bash
# Mit Token
curl -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "prompts/list",
    "id": 1
  }'

# Sollte 5 Prompts zurückgeben
```

---

## 🔧 Troubleshooting

### Problem: Dependencies fehlen

```bash
# Lösung: Installiere mit pip3 oder system packages
pip3 install -r requirements.txt --user
```

### Problem: Qdrant nicht erreichbar

```bash
# Lösung: Starte Qdrant Container
docker run -d --name qdrant-mcp-edu -p 6333:6333 qdrant/qdrant

# Oder prüfe ob er läuft
docker ps | grep qdrant
docker logs qdrant-mcp-edu
```

### Problem: Port 8000 bereits belegt

```bash
# Lösung: Finde Prozess und beende ihn
sudo lsof -i :8000
sudo kill <PID>

# Oder nutze anderen Port in .env
HTTP_PORT=8001
```

### Problem: Import Errors

```bash
# Lösung: Python Path setzen
export PYTHONPATH=/home/imreo/mcp-diploma-thesis-final:$PYTHONPATH
python3 main.py
```

### Problem: Auth Fehler

```bash
# Prüfe .env Datei
cat .env | grep SCALEKIT

# Prüfe ob Credentials korrekt sind
# Teste OAuth Flow manuell: http://localhost:8000/auth/login
```

---

## 📊 Monitoring

### Logs prüfen

```bash
# Wenn als systemd service
sudo journalctl -u mcp-server -f

# Wenn direkt gestartet
tail -f logs/server.log

# Wenn mit Docker
docker logs -f mcp-server
```

### Performance überwachen

```bash
# Memory
free -h

# CPU
top -p $(pgrep -f "python3 main.py")

# Disk
df -h

# Qdrant
curl http://localhost:6333/metrics
```

---

## 📝 Checkliste

### Pre-Deployment

- [ ] Syntax Check bestanden
- [ ] Import Tests bestanden
- [ ] Dependencies installiert
- [ ] Qdrant läuft
- [ ] .env konfiguriert
- [ ] Server Start Test erfolgreich
- [ ] Health Check antwortet
- [ ] OAuth Discovery funktioniert

### Deployment

- [ ] Git commit erstellt
- [ ] Feature branch gepushed
- [ ] In main gemerged
- [ ] Release Tag erstellt
- [ ] Docker Image gebaut (optional)
- [ ] Container gestartet (optional)

### Post-Deployment

- [ ] Server läuft stabil
- [ ] Health endpoint antwortet
- [ ] MCP Tools funktionieren
- [ ] Resources verfügbar
- [ ] Prompts verfügbar
- [ ] Logs sehen gut aus
- [ ] Performance acceptable

---

## 🎯 Nächste Schritte

Nach erfolgreichem Deployment:

1. **Monitoring einrichten** - Logs, Metrics, Alerts
2. **Backup-Strategie** - Qdrant Daten regelmäßig sichern
3. **Load Testing** - Performance unter Last testen
4. **Documentation Update** - User-facing Dokumentation
5. **Claude Desktop Integration** - Test mit echtem Client

---

**Status:** Testing Guide Complete  
**Letzte Aktualisierung:** 31. Januar 2026  
**Version:** 2.0.0
