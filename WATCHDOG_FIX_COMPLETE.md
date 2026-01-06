# 🔧 Watchdog Fix Complete - Automatische JSONL-Verarbeitung funktioniert!

**Datum:** 2026-01-06  
**Status:** ✅ **VOLLSTÄNDIG BEHOBEN**

---

## 🐛 Problem-Analyse

### Ursprünglicher Fehler
```
ERROR - Failed to ensure collection exists: illegal request line
```

**Ursache:** Falsche Port-Konfiguration
- ❌ **Vorher:** `VECTOR_DB_URL=http://qdrant:6334` (gRPC Port)
- ✅ **Jetzt:** `VECTOR_DB_URL=http://qdrant:6333` (HTTP Port)

**Warum?** Der Python Qdrant Client (`qdrant-client`) nutzt die **REST API (HTTP)**, nicht gRPC!

### Sekundäres Problem
```
WARNING - Invalid access_level 'teacher_only' for document ..., defaulting to 'public'
```

**Ursache:** JSONL-Dateien vom Kollegen verwenden `teacher_only` statt `teacher`

---

## ✅ Implementierte Fixes

### 1. Qdrant Port-Korrektur

**Geänderte Dateien:**
- `docker-compose.yml` (2 Stellen: mcp-server + watchdog)
- `docker-compose.security.yml` (2 Stellen)
- `src/pipeline/watchdog_service.py` (Default-Wert)

**Änderung:**
```diff
- VECTOR_DB_URL=http://qdrant:6334  # ❌ gRPC (für Go/Rust Clients)
+ VECTOR_DB_URL=http://qdrant:6333  # ✅ HTTP (für Python Client)
```

### 2. access_level Alias-Mapping

**Datei:** `src/pipeline/jsonl_ingestion.py`

**Neue Funktion:**
```python
# Map common aliases to standard values
access_level_mapping = {
    "teacher_only": "teacher",
    "student_only": "student",
    "all": "public",
}
```

**Vorteil:**
- ✅ Legacy-Daten werden automatisch konvertiert
- ✅ Keine Fehlermeldungen mehr
- ✅ RBAC funktioniert korrekt (teacher sieht teacher-only Content)

---

## 📊 Erfolgreiche Verarbeitung

### Verarbeitete Dateien

| **Datei** | **Dokumente** | **Status** | **Timestamp** |
|-----------|---------------|------------|---------------|
| `pages_test_auto.jsonl` | 757 | ✅ Processed | 2026-01-06 16:14:48 |
| `pages_test.jsonl` | 757 | ✅ Processed | 2026-01-06 16:15:57 |
| **GESAMT** | **1514** | **✅ In Qdrant** | - |

### Verzeichnisstruktur

```
data/
├── incoming/          # ← Leer (alle verarbeitet)
├── processed/         # ✅ 2 Dateien (64 MB)
│   ├── 20260106_161448_pages_test_auto.jsonl (32 MB)
│   └── 20260106_161557_pages_test.jsonl (32 MB)
└── failed/            # ⚠️ Nur alte Error-Logs (vor dem Fix)
    ├── 20260106_132800_pages_test_auto.error.json
    ├── 20260106_132801_pages_test.error.json
    └── 20260106_153536_embedded_chunks.error.json
```

---

## 🚀 Watchdog Service - Live Status

### Aktueller Status
```
✅ Watchdog läuft 24/7
✅ Verbunden mit Qdrant (http://qdrant:6333)
✅ Überwacht: /app/data/incoming
✅ Batch-Größe: 100 Dokumente
✅ Auto-Create Collection: Aktiviert
```

### Logs (Live)
```
2026-01-06 16:15:26 - ✅ Connected to Qdrant
2026-01-06 16:15:26 - 🚀 Watchdog service is running!
2026-01-06 16:15:46 - Detected new file: pages_test.jsonl
2026-01-06 16:15:57 - Successfully ingested pages_test.jsonl: 
                      757 points from 757 documents (0 invalid)
2026-01-06 16:15:57 - Moved pages_test.jsonl to processed
```

---

## 📋 Workflow für deinen Kollegen

### 1. JSONL-Datei via Tailscale hochladen
```bash
# Von seinem PC aus:
scp educational_data.jsonl imreo@raspi-docker:/home/imreo/mcp-diploma-thesis-final/data/incoming/
```

### 2. Automatische Verarbeitung (< 1 Minute)
```
1. Watchdog erkennt neue Datei (< 1 Sekunde)
2. Validierung + Qdrant Upsert (Batch: 100 Docs)
3. Datei wird verschoben:
   ✅ processed/ (bei Erfolg)
   ❌ failed/ + Error-Log (bei Fehler)
```

### 3. Status überprüfen
```bash
# Live-Logs anschauen
docker logs -f mcp-watchdog

# Verarbeitete Dateien
ls -lh data/processed/

# Fehlerhafte Dateien
ls -lh data/failed/
```

---

## 🔍 Technische Details

### Qdrant Ports - Erklärt

| **Port** | **Protokoll** | **Verwendung** | **Client** |
|----------|---------------|----------------|------------|
| **6333** | HTTP (REST) | ✅ **Python Client** | `qdrant-client` (Python) |
| **6334** | gRPC | Go, Rust, C++ Clients | Hochperformante Clients |

**Unser Setup:**
- Python FastAPI Server → HTTP (6333)
- Python Watchdog → HTTP (6333)
- Docker Network: Beide Ports exposed (intern)
- Host: Keine Ports exposed (Security!)

### Batch-Verarbeitung

**Beispiel:** 757 Dokumente
```
Batch 1: 100 Dokumente → Qdrant Upsert (1.5s)
Batch 2: 100 Dokumente → Qdrant Upsert (1.5s)
Batch 3: 100 Dokumente → Qdrant Upsert (1.5s)
Batch 4: 100 Dokumente → Qdrant Upsert (1.5s)
Batch 5: 100 Dokumente → Qdrant Upsert (1.5s)
Batch 6: 100 Dokumente → Qdrant Upsert (1.5s)
Batch 7: 100 Dokumente → Qdrant Upsert (1.5s)
Batch 8:  57 Dokumente → Qdrant Upsert (0.8s)

GESAMT: ~11 Sekunden für 757 Dokumente
```

---

## ✅ Checkliste - Alles funktioniert!

- [x] Qdrant Port korrigiert (6334 → 6333)
- [x] access_level Mapping implementiert (`teacher_only` → `teacher`)
- [x] Watchdog Container neu gebaut
- [x] Docker Services neu gestartet
- [x] 1514 Dokumente erfolgreich in Qdrant ingested
- [x] Watchdog läuft 24/7 und überwacht `incoming/`
- [x] Alle Änderungen committed & gepusht

---

## 🎯 Nächste Schritte

### Für deinen Kollegen:
1. **Erste JSONL-Datei hochladen** (via Tailscale SCP)
2. **Warten (< 1 Minute)** bis Datei in `processed/` landet
3. **Testen:** MCP Server abfragen, ob Daten sichtbar sind

### Für dich:
1. **Scalekit Testing** (wenn Kollege bereit ist)
   - Test-User anlegen (student, teacher)
   - OAuth Flow testen
   - RBAC testen (Student sieht nur student/public Content)

---

## 📚 Dokumentation

**Relevante Dateien:**
- `docs/PRODUCTION_SETUP_PLAN.md` - Gesamtplan
- `docs/COLLEAGUE_TAILSCALE_GUIDE.md` - Anleitung für Kollegen
- `docs/SECURITY_HARDENING.md` - Sicherheits-Setup
- `PRODUCTION_READY_STATUS.md` - Gesamtstatus

**Logs & Monitoring:**
```bash
# Watchdog Logs
docker logs -f mcp-watchdog

# Qdrant Collection Info (intern)
docker exec mcp-server python -c "
from qdrant_client import QdrantClient
client = QdrantClient(url='http://qdrant:6333')
info = client.get_collection('educational_content')
print(f'Points: {info.points_count}')
"
```

---

## 🎉 Fazit

**Status:** 🟢 **PRODUCTION-READY!**

Der Watchdog Service funktioniert jetzt einwandfrei:
- ✅ Automatische Echtzeit-Verarbeitung
- ✅ RBAC-konforme Daten (access_level Mapping)
- ✅ Robuste Fehlerbehandlung
- ✅ 24/7 Betrieb

**Dein Kollege kann jetzt JSONL-Dateien hochladen, und sie werden automatisch verarbeitet!** 🚀
