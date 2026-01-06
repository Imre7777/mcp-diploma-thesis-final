# ✅ Watchdog Service Aktiviert - Automatische JSONL-Verarbeitung

**Datum:** 06. Januar 2026  
**Status:** 🟢 **Watchdog läuft und überwacht Verzeichnis**

---

## 🎯 Was wurde aktiviert

### Automatische Datei-Verarbeitung

Der **Watchdog Service** überwacht das `incoming/` Verzeichnis und verarbeitet automatisch neue JSONL-Dateien:

```
Kollege uploaded Datei via Tailscale
        ↓
/home/imreo/mcp-diploma-thesis-final/data/incoming/datei.jsonl
        ↓ (Watchdog erkennt neue Datei)
Automatische Verarbeitung startet
        ↓
- Validierung (JSONL-Format, Pflichtfelder)
- Embedding-Extraktion
- Qdrant-Upload mit RBAC-Metadaten
        ↓
Bei Erfolg → /data/processed/20260106_HHMMSS_datei.jsonl
Bei Fehler → /data/failed/20260106_HHMMSS_datei.jsonl + .error.json
```

**Verarbeitungszeit:** 5-30 Sekunden (je nach Dateigröße)

---

## 🐳 Docker Service

### Container-Konfiguration

```yaml
watchdog:
  container_name: mcp-watchdog
  restart: unless-stopped
  command: python -m src.pipeline.watchdog_service
  
  environment:
    - VECTOR_DB_URL=http://qdrant:6334
    - DEFAULT_COLLECTION=educational_content
    - INCOMING_DIR=/app/data/incoming
    - PROCESSED_DIR=/app/data/processed
    - FAILED_DIR=/app/data/failed
    - OPENAI_API_KEY=${OPENAI_API_KEY}
  
  volumes:
    - ./data/incoming:/app/data/incoming
    - ./data/processed:/app/data/processed
    - ./data/failed:/app/data/failed
    - ./data/statistics:/app/data/statistics
```

### Status prüfen

```bash
# Container-Status:
docker compose ps watchdog

# Logs anzeigen:
docker compose logs -f watchdog

# Neustart (falls nötig):
docker compose restart watchdog
```

---

## 📂 Verzeichnis-Struktur

```
/home/imreo/mcp-diploma-thesis-final/data/
├── incoming/          ← Kollege uploaded hier
│   └── (leer nach Verarbeitung)
│
├── processed/         ← Erfolgreich verarbeitete Dateien
│   ├── 20260106_143000_education_data.jsonl
│   ├── 20260106_150000_course_materials.jsonl
│   └── ...
│
├── failed/            ← Fehlgeschlagene Dateien
│   ├── 20260106_145000_invalid_data.jsonl
│   ├── 20260106_145000_invalid_data.error.json  ← Error-Log
│   └── ...
│
└── statistics/        ← Verarbeitungs-Statistiken
    └── ingestion_stats.json
```

---

## 🔄 Workflow

### 1. Kollege uploaded Datei

```bash
# Via Tailscale SCP:
scp education_data.jsonl imreo@100.73.228.15:/home/imreo/mcp-diploma-thesis-final/data/incoming/
```

### 2. Watchdog erkennt Datei (sofort)

```
2026-01-06 14:30:05 - INFO - Detected new file: education_data.jsonl
2026-01-06 14:30:05 - INFO - Processing file: education_data.jsonl
```

### 3. Validierung & Verarbeitung

```
2026-01-06 14:30:05 - INFO - Parsing JSONL file...
2026-01-06 14:30:06 - INFO - Validating 150 documents...
2026-01-06 14:30:07 - INFO - Upserting batch 1/2 (100 points)
2026-01-06 14:30:08 - INFO - Upserting batch 2/2 (50 points)
```

### 4. Datei wird verschoben

**Bei Erfolg:**
```
2026-01-06 14:30:09 - INFO - Successfully processed 150 documents
2026-01-06 14:30:09 - INFO - Moved education_data.jsonl to processed: 20260106_143009_education_data.jsonl
```

**Bei Fehler:**
```
2026-01-06 14:30:09 - ERROR - Validation failed: Missing field 'access_level' in document 45
2026-01-06 14:30:09 - ERROR - Moved education_data.jsonl to failed: 20260106_143009_education_data.jsonl
2026-01-06 14:30:09 - INFO - Error log written to: 20260106_143009_education_data.error.json
```

---

## 🧪 Testing

### Test 1: Einfache Test-Datei

```bash
# Test-Datei erstellen:
echo '{"id":"test_001","title":"Watchdog Test","content":"Testing automatic processing","metadata":{"frontmatter":{"access_level":"student"}}}' > /home/imreo/mcp-diploma-thesis-final/data/incoming/test_watchdog.jsonl

# Warten (5-10 Sekunden)

# Prüfen ob verarbeitet:
ls -lh /home/imreo/mcp-diploma-thesis-final/data/processed/ | grep test_watchdog

# Sollte zeigen:
# 20260106_HHMMSS_test_watchdog.jsonl
```

### Test 2: Logs beobachten

```bash
# Terminal 1: Logs anzeigen
docker compose logs -f watchdog

# Terminal 2: Datei uploaden
scp test.jsonl imreo@100.73.228.15:/home/imreo/mcp-diploma-thesis-final/data/incoming/

# Terminal 1 sollte sofort Verarbeitung zeigen
```

### Test 3: Fehlerhafte Datei

```bash
# Ungültige JSONL (fehlendes Feld):
echo '{"id":"bad_001","title":"Invalid"}' > /home/imreo/mcp-diploma-thesis-final/data/incoming/invalid_test.jsonl

# Warten (5-10 Sekunden)

# Prüfen:
ls -lh /home/imreo/mcp-diploma-thesis-final/data/failed/ | grep invalid_test

# Error-Log lesen:
cat /home/imreo/mcp-diploma-thesis-final/data/failed/*invalid_test.error.json
```

---

## 📊 Monitoring

### Logs in Echtzeit

```bash
# Alle Watchdog-Logs:
docker compose logs -f watchdog

# Nur Fehler:
docker compose logs watchdog | grep ERROR

# Nur erfolgreiche Verarbeitungen:
docker compose logs watchdog | grep "Successfully processed"
```

### Statistiken

```bash
# Verarbeitungs-Statistiken:
cat /home/imreo/mcp-diploma-thesis-final/data/statistics/ingestion_stats.json

# Beispiel-Output:
{
  "total_files": 15,
  "successful": 13,
  "failed": 2,
  "total_documents": 1234,
  "last_processed": "2026-01-06T14:30:00",
  "by_access_level": {
    "student": 800,
    "teacher": 400,
    "admin": 34
  }
}
```

### Container-Health

```bash
# Container-Status:
docker compose ps watchdog

# Sollte zeigen:
# mcp-watchdog   Up X minutes (healthy)

# Ressourcen-Nutzung:
docker stats mcp-watchdog --no-stream
```

---

## 🔧 Troubleshooting

### Problem: Watchdog läuft nicht

```bash
# Status prüfen:
docker compose ps watchdog

# Logs anzeigen:
docker compose logs watchdog | tail -50

# Neustart:
docker compose restart watchdog
```

### Problem: Datei wird nicht verarbeitet

**Mögliche Ursachen:**

1. **Datei ist noch nicht komplett hochgeladen**
   - Watchdog wartet auf vollständigen Upload
   - Lösung: Warten (SCP zeigt 100% wenn fertig)

2. **Falsches Dateiformat**
   - Nur `.jsonl` Dateien werden verarbeitet
   - Lösung: Datei muss `.jsonl` Extension haben

3. **Watchdog ist gestoppt**
   - Lösung: `docker compose restart watchdog`

4. **Berechtigungsprobleme**
   ```bash
   # Berechtigungen prüfen:
   ls -ld /home/imreo/mcp-diploma-thesis-final/data/incoming/
   
   # Falls nötig:
   sudo chown -R imreo:imreo /home/imreo/mcp-diploma-thesis-final/data/
   ```

### Problem: Datei landet in failed/

```bash
# Error-Log lesen:
cat /home/imreo/mcp-diploma-thesis-final/data/failed/*DATEINAME.error.json

# Zeigt exakte Fehlermeldung:
{
  "file": "dateiname.jsonl",
  "timestamp": "20260106_143000",
  "message": "Missing required field: 'access_level' in document 45",
  "stats": {
    "total_lines": 150,
    "failed_line": 45
  }
}
```

**Häufige Fehler:**

1. **Missing field: 'access_level'**
   - Dokument hat kein `metadata.frontmatter.access_level`
   - Lösung: Feld hinzufügen

2. **Invalid access_level**
   - Wert ist nicht "student", "teacher" oder "admin"
   - Lösung: Korrekten Wert verwenden

3. **Invalid JSONL format**
   - Datei ist kein valides JSONL (z.B. JSON-Array statt Zeilen)
   - Lösung: Jede Zeile = ein JSON-Objekt

---

## 🔐 Sicherheit

### Automatische Verarbeitung

- ✅ Nur `.jsonl` Dateien werden verarbeitet
- ✅ Validierung vor Verarbeitung
- ✅ Fehlerhafte Dateien werden isoliert
- ✅ Error-Logs für Debugging
- ✅ Keine Ausführung von Code aus Dateien

### Isolation

- ✅ Watchdog läuft in separatem Container
- ✅ Nur Zugriff auf data/ Verzeichnisse
- ✅ Kein Netzwerk-Zugriff nach außen (nur zu Qdrant)
- ✅ Restart-Policy: unless-stopped

---

## 📝 Für Kollegen

### Was Sie wissen müssen

**Upload wie gewohnt:**
```bash
scp ihre_datei.jsonl imreo@100.73.228.15:/home/imreo/mcp-diploma-thesis-final/data/incoming/
```

**Das passiert automatisch:**
1. ✅ Datei wird erkannt (innerhalb von Sekunden)
2. ✅ Validierung & Verarbeitung
3. ✅ Upload zu Qdrant
4. ✅ Datei wird nach `processed/` verschoben

**Sie müssen NICHTS machen!**

**Bestätigung erhalten:**
- Option A: Fragen Sie Imre nach Status
- Option B: SSH zum Pi und prüfen Sie `processed/` Verzeichnis
- Option C: Warten Sie auf Bestätigungs-Email (falls eingerichtet)

**Bei Problemen:**
- Datei landet in `failed/` statt `processed/`
- Error-Log wird erstellt: `DATEINAME.error.json`
- Kontaktieren Sie Imre mit Dateinamen

---

## ✅ Vorteile

| Feature | Vorher (manuell) | Jetzt (automatisch) |
|---------|------------------|---------------------|
| **Verarbeitung** | Manuell starten | ✅ Automatisch |
| **Wartezeit** | Bis Imre verfügbar | ✅ Sofort (5-30 Sek) |
| **Fehlerkennung** | Manuell prüfen | ✅ Automatisch + Log |
| **Verfügbarkeit** | Geschäftszeiten | ✅ 24/7 |
| **Skalierung** | Begrenzt | ✅ Unbegrenzt |

---

## 🚀 Status

**Watchdog Service:** ✅ **AKTIV**

- ✅ Container läuft
- ✅ Überwacht `/data/incoming/`
- ✅ Verarbeitet automatisch
- ✅ Fehlerbehandlung aktiv
- ✅ Logs verfügbar

**Kollege kann jetzt:**
- ✅ Dateien hochladen via Tailscale
- ✅ Automatische Verarbeitung erfolgt
- ✅ Keine manuelle Intervention nötig

**Next:** Sicherheits-Verbesserungen (Netzwerk-Isolation)
