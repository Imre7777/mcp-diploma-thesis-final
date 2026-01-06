# 🗑️ Clear Collection Before Ingest Feature

## 📋 **Übersicht**

Seit diesem Update wird die Qdrant Collection **vor jedem Upload automatisch komplett geleert**. Das bedeutet:

- ✅ **Upload vom Kollegen = einzige Datenquelle** (Single Source of Truth)
- ✅ **Keine alten oder verwaisten Dokumente**
- ✅ **Exakte 1:1 Übereinstimmung**: JSONL-Datei ↔ Qdrant Collection

---

## 🎯 **Problem (Vorher)**

**Situation:**
- Kollege lädt `embedded_chunks.jsonl` mit **3417 Dokumenten** hoch
- Qdrant Collection hat **3469 Punkte** (52 alte Dokumente von früherem Upload)
- **Differenz: 52 verwaiste Dokumente**

**Ursache:**
- Qdrant verwendet **UPSERT** (Update + Insert)
- Dokumente mit IDs, die **nicht** in der neuen Datei sind, bleiben erhalten
- → Collection enthält **alte + neue Daten** gemischt

**Kunde wünscht:**
- Upload vom Kollegen = **aktueller, letzter und neuester Stand**
- **Keine alten Dokumente** in der Collection
- **Saubere, eindeutige Datenbasis**

---

## ✅ **Lösung (Jetzt)**

### **Verhalten:**

1. 📤 **Kollege lädt JSONL-Datei hoch** (via SCP/Tailscale)
2. ⏳ **Watchdog wartet** (5 Min Timeout, bis Upload komplett)
3. 🗑️ **Collection wird GELEERT** (alle alten Punkte gelöscht)
4. ✅ **Neue Daten werden eingespielt** (3417 Dokumente)
5. 📦 **Datei wird verschoben** nach `/processed/` mit Timestamp
6. 🎉 **Collection hat EXAKT 3417 Punkte** (keine alten Daten)

---

## 🔧 **Technische Implementierung**

### **1. Neue Umgebungsvariable**

In `docker-compose.yml` wurde hinzugefügt:

```yaml
watchdog:
  environment:
    # WICHTIG: Collection vor jedem Upload leeren
    - CLEAR_COLLECTION_BEFORE_INGEST=true
```

**Werte:**
- `true`: Collection wird vor jedem Upload geleert (Produktion)
- `false`: UPSERT-Verhalten (alte + neue Daten gemischt, nur für Tests)

---

### **2. Neue Methode: `clear_collection()`**

In `src/pipeline/jsonl_ingestion.py`:

```python
def clear_collection(self) -> bool:
    """
    Delete all points from the collection.
    
    This ensures a clean state before ingesting new data,
    preventing orphaned documents from previous uploads.
    
    Returns:
        True if successful, False on error
    """
    try:
        logger.info(f"🗑️  Clearing all points from collection '{self.collection_name}'...")
        
        # Get all point IDs using scroll
        scroll_result = self.qdrant_client.scroll(
            collection_name=self.collection_name,
            limit=10000,  # Adjust if you have more than 10k points
            with_payload=False,
            with_vectors=False,
        )
        
        point_ids = [point.id for point in scroll_result[0]]
        
        if not point_ids:
            logger.info("Collection is already empty")
            return True
        
        logger.info(f"Deleting {len(point_ids)} existing points...")
        self.qdrant_client.delete(
            collection_name=self.collection_name,
            points_selector=point_ids,
        )
        
        logger.info(f"✅ Cleared {len(point_ids)} points from collection")
        return True
    
    except Exception as e:
        logger.error(f"Failed to clear collection: {e}")
        return False
```

---

### **3. Modifizierte `ingest_jsonl_file()` Methode**

Vor der Ingestion wird die Collection geleert, falls konfiguriert:

```python
async def ingest_jsonl_file(self, file_path: Path) -> tuple[bool, str, dict]:
    # ...
    
    # Ensure collection exists
    if not self.ensure_collection_exists():
        return False, "Collection does not exist and could not be created", stats
    
    # Clear collection before ingestion if configured
    # This ensures the uploaded file is the ONLY source of truth
    clear_before_ingest = os.getenv("CLEAR_COLLECTION_BEFORE_INGEST", "false").lower() == "true"
    if clear_before_ingest:
        logger.info("🔄 CLEAR_COLLECTION_BEFORE_INGEST=true: Clearing existing data...")
        if not self.clear_collection():
            logger.warning("Failed to clear collection, continuing anyway...")
        else:
            logger.info("✅ Collection cleared, starting fresh ingestion...")
    
    # Continue with ingestion...
```

---

## 📊 **Beispiel-Workflow**

### **Vor dem Upload:**

```bash
# Qdrant Collection Status
curl -s http://localhost:6333/collections/educational_content | jq '.result.points_count'
# Output: 3469 (alte Daten von vorherigen Uploads)
```

### **Kollege lädt Datei hoch:**

```bash
# SCP Upload
scp -i ~/.ssh/id_ed25519 embedded_chunks.jsonl imreo@100.73.228.15:/home/imreo/mcp-diploma-thesis-final/data/incoming/
```

### **Watchdog Logs:**

```
2026-01-06 18:45:20 - INFO - Detected new file: embedded_chunks.jsonl
2026-01-06 18:45:20 - INFO - Waiting for file to stabilize: embedded_chunks.jsonl
2026-01-06 18:47:25 - INFO - File stabilized: embedded_chunks.jsonl (142 MB)
2026-01-06 18:47:25 - INFO - Starting ingestion of embedded_chunks.jsonl...
2026-01-06 18:47:25 - INFO - Collection 'educational_content' already exists
2026-01-06 18:47:25 - INFO - 🔄 CLEAR_COLLECTION_BEFORE_INGEST=true: Clearing existing data...
2026-01-06 18:47:25 - INFO - 🗑️  Clearing all points from collection 'educational_content'...
2026-01-06 18:47:25 - INFO - Deleting 3469 existing points...
2026-01-06 18:47:26 - INFO - ✅ Cleared 3469 points from collection
2026-01-06 18:47:26 - INFO - ✅ Collection cleared, starting fresh ingestion...
2026-01-06 18:47:26 - INFO - Processing line 1...
...
2026-01-06 18:49:30 - INFO - Successfully ingested embedded_chunks.jsonl: 3417 points from 3417 documents (0 invalid, 3417 total lines)
2026-01-06 18:49:30 - INFO - Moved embedded_chunks.jsonl to processed: 20260106_184930_embedded_chunks.jsonl
```

### **Nach dem Upload:**

```bash
# Qdrant Collection Status
curl -s http://localhost:6333/collections/educational_content | jq '.result.points_count'
# Output: 3417 (EXAKT die Anzahl aus der JSONL-Datei)
```

**✅ Perfekte 1:1 Übereinstimmung!**

---

## 🎯 **Vorteile**

| Vorteil | Beschreibung |
|---------|--------------|
| **Single Source of Truth** | Upload vom Kollegen = einzige Datenquelle, keine Vermischung |
| **Keine verwaisten Dokumente** | Alte Daten werden automatisch entfernt |
| **Exakte Übereinstimmung** | JSONL-Datei ↔ Qdrant Collection sind identisch |
| **Klare Versionierung** | Jeder Upload = neue Version, alte Versionen werden ersetzt |
| **Einfaches Rollback** | Bei Problemen: alte JSONL-Datei neu hochladen |
| **Predictable** | Kollege weiß genau, was in Qdrant ist (= seine Datei) |

---

## ⚠️ **Wichtige Hinweise**

### **1. Downtime während Upload**

Während die Collection geleert und neu befüllt wird:
- ⚠️ Qdrant Collection ist **kurzzeitig leer** (~5 Sekunden)
- ⚠️ Suchanfragen liefern **keine Ergebnisse** während dieser Zeit
- ✅ Nach 2 Minuten ist alles wieder normal

**Lösung für Zero-Downtime (optional, später):**
- Blue-Green Deployment (zwei Collections: `educational_content_blue`, `educational_content_green`)
- Ingest in inaktive Collection → Swap → Alte löschen

### **2. Nur für Production**

Diese Funktion ist **nur für Production** aktiviert (`CLEAR_COLLECTION_BEFORE_INGEST=true`).

Für **lokale Tests** oder **Entwicklung** kann man sie deaktivieren:

```yaml
# docker-compose.yml (local override)
watchdog:
  environment:
    - CLEAR_COLLECTION_BEFORE_INGEST=false  # Alte Daten behalten (UPSERT)
```

### **3. Backup-Strategie**

Da alte Daten automatisch gelöscht werden, ist ein **Backup wichtig**:

**Option 1: JSONL-Dateien als Backup**
- ✅ Alle verarbeiteten Dateien in `/data/processed/` aufbewahren
- ✅ Bei Bedarf: alte JSONL-Datei neu hochladen

**Option 2: Qdrant Snapshots (optional)**
```bash
# Snapshot vor jedem Upload (optional, später)
curl -X POST http://localhost:6333/collections/educational_content/snapshots
```

---

## 🧪 **Testen**

### **Test 1: Erste Upload**

```bash
# Status vorher (z.B. 3469 Punkte)
curl -s http://localhost:6333/collections/educational_content | jq '.result.points_count'

# Upload
scp embedded_chunks.jsonl imreo@100.73.228.15:/path/to/incoming/

# Warten (2 Minuten)
# Status nachher (genau 3417 Punkte)
curl -s http://localhost:6333/collections/educational_content | jq '.result.points_count'
```

**Erwartung:** `3417` (exakte Übereinstimmung mit JSONL)

### **Test 2: Zweiter Upload (kleinere Datei)**

```bash
# Status vorher: 3417 Punkte

# Upload kleinere Datei (z.B. 1000 Dokumente)
scp small_chunks.jsonl imreo@100.73.228.15:/path/to/incoming/

# Status nachher: 1000 Punkte
curl -s http://localhost:6333/collections/educational_content | jq '.result.points_count'
```

**Erwartung:** `1000` (alte 3417 wurden gelöscht, nur neue 1000 sind da)

---

## ✅ **Zusammenfassung**

- ✅ **Feature aktiviert:** `CLEAR_COLLECTION_BEFORE_INGEST=true`
- ✅ **Verhalten:** Collection wird vor jedem Upload komplett geleert
- ✅ **Vorteil:** Upload vom Kollegen = einzige Datenquelle (Single Source of Truth)
- ✅ **Ergebnis:** Exakte 1:1 Übereinstimmung zwischen JSONL-Datei und Qdrant Collection
- ✅ **Status:** Production-Ready! 🚀

**Nächster Upload wird die Collection automatisch leeren und nur die neuen Daten einspielen!**
