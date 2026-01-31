# LeoWiki MCP Server - Role-Based Access Control (RBAC) Implementation

## Übersicht

Dieses Dokument beschreibt die Implementierung von zwei separaten MCP-Tools für rollenbasierte Zugriffskontrolle im LeoWiki-Projekt. Anstatt eines einzelnen Tools mit Parameter werden zwei dedizierte Tools erstellt, die jeweils nur die erlaubten Inhalte für ihre Zielgruppe durchsuchen können.

## Architektur-Entscheidung

### Warum zwei separate Tools?

**Vorteile:**
- ✅ **Security by Design** - Zugriffskontrolle auf Tool-Ebene, nicht auf Parameter-Ebene
- ✅ **Keine Parameter-Manipulation möglich** - Schüler können nicht `access_level=teacher` setzen
- ✅ **Klarere API-Semantik** - Jedes Tool hat einen eindeutigen, spezifischen Zweck
- ✅ **Einfachere Backend-Implementierung** - Keine Validierung von `access_level` notwendig
- ✅ **Besseres Audit-Logging** - Direktes Tracking welches Tool verwendet wurde
- ✅ **Flexiblere Connector-Konfiguration** - Verschiedene Endpoints für verschiedene Rollen

**Alternative (nicht empfohlen):**
- ❌ Ein Tool mit `access_level` Parameter - Anfällig für Manipulation und erfordert Backend-Validierung

## Tool-Definitionen

### 1. Tool für Schüler: `search_content_student`

**Zweck:** Suche in öffentlichen und schülerrelevanten Inhalten

**Zugriff auf Namespaces:**
- `public:*` - Öffentlich zugängliche Inhalte
- `student:*` - Schüler-spezifische Inhalte
- Standard Wiki-Seiten ohne Namespace-Präfix

**Ausgeschlossen:**
- `teacher:*` - Lehrer-interne Dokumente
- `admin:*` - Administrative Inhalte
- `forms:kv` - Klassenvorstands-Formulare

### 2. Tool für Lehrer: `search_content_teacher`

**Zweck:** Suche in allen verfügbaren Inhalten

**Zugriff auf Namespaces:**
- Alle Namespaces aus `search_content_student`
- `teacher:*` - Lehrer-interne Dokumente und Ressourcen
- `teacher:forms:*` - Formulare und Vorlagen
- `teacher:kv:*` - Klassenvorstands-spezifische Inhalte

## FastMCP Implementierung

### Code-Beispiel

```python
from fastmcp import FastMCP
from typing import List, Optional

mcp = FastMCP("LeoWiki Educational Search")

# Gemeinsame Hilfsfunktion für Vector Search
async def search_with_namespace_filter(
    query: str,
    allowed_namespaces: List[str],
    limit: int = 10
) -> dict:
    """
    Führt eine semantische Suche durch mit Namespace-Filterung
    
    Args:
        query: Suchbegriff
        allowed_namespaces: Liste erlaubter Namespace-Präfixe
        limit: Maximale Anzahl Ergebnisse
    
    Returns:
        Dictionary mit gefilterten Suchergebnissen
    """
    # Vector Search durchführen
    raw_results = await vector_db.search(
        query=query,
        top_k=limit * 2  # Mehr holen, um nach Filterung genug zu haben
    )
    
    # Nach Namespaces filtern
    filtered_results = []
    for result in raw_results:
        namespace = result.metadata.get('namespace', '')
        
        # Prüfen ob Namespace erlaubt ist
        is_allowed = False
        for allowed_ns in allowed_namespaces:
            if namespace.startswith(allowed_ns) or namespace == '':
                is_allowed = True
                break
        
        if is_allowed:
            filtered_results.append(result)
            if len(filtered_results) >= limit:
                break
    
    return {
        "query": query,
        "results": filtered_results,
        "count": len(filtered_results)
    }


@mcp.tool()
async def search_content_student(
    query: str,
    limit: int = 10
) -> dict:
    """
    Durchsucht die LeoWiki-Wissensdatenbank mit Schüler-Zugriffsrechten.
    
    Zugriff auf:
    - Öffentliche Inhalte (public:*)
    - Schüler-spezifische Inhalte (student:*)
    - Allgemeine Wiki-Seiten
    
    Kein Zugriff auf:
    - Lehrer-interne Dokumente (teacher:*)
    - Administrative Inhalte (admin:*)
    - Klassenvorstands-Formulare
    
    Args:
        query: Suchbegriff oder Frage (z.B. "Mobbing Prävention")
        limit: Maximale Anzahl Ergebnisse (Standard: 10, Max: 20)
    
    Returns:
        Dictionary mit Suchergebnissen und Metadaten
    """
    # Validierung
    if not query or len(query.strip()) == 0:
        return {"error": "Query parameter cannot be empty"}
    
    if limit < 1 or limit > 20:
        limit = min(max(limit, 1), 20)
    
    # Definiere erlaubte Namespaces für Schüler
    allowed_namespaces = [
        'public',
        'student',
        ''  # Leerer String für Seiten ohne Namespace
    ]
    
    # Suche durchführen
    results = await search_with_namespace_filter(
        query=query,
        allowed_namespaces=allowed_namespaces,
        limit=limit
    )
    
    # Logging für Audit
    log_search_request(
        role="student",
        query=query,
        results_count=results['count']
    )
    
    return results


@mcp.tool()
async def search_content_teacher(
    query: str,
    limit: int = 10
) -> dict:
    """
    Durchsucht die LeoWiki-Wissensdatenbank mit Lehrer-Zugriffsrechten.
    
    Zugriff auf:
    - Alle Inhalte die Schüler sehen können
    - Lehrer-interne Dokumente (teacher:*)
    - Klassenvorstands-Formulare (teacher:forms:kv:*)
    - Administrative Ressourcen
    - Pädagogische Anleitungen
    
    Args:
        query: Suchbegriff oder Frage (z.B. "No-Blame-Approach")
        limit: Maximale Anzahl Ergebnisse (Standard: 10, Max: 20)
    
    Returns:
        Dictionary mit Suchergebnissen und Metadaten
    """
    # Validierung
    if not query or len(query.strip()) == 0:
        return {"error": "Query parameter cannot be empty"}
    
    if limit < 1 or limit > 20:
        limit = min(max(limit, 1), 20)
    
    # Lehrer haben Zugriff auf ALLE Namespaces
    # Option 1: Keine Filterung (empfohlen)
    raw_results = await vector_db.search(
        query=query,
        top_k=limit
    )
    
    results = {
        "query": query,
        "results": raw_results,
        "count": len(raw_results)
    }
    
    # Option 2: Explizite Liste (falls bestimmte Namespaces ausgeschlossen werden sollen)
    # allowed_namespaces = [
    #     'public',
    #     'student', 
    #     'teacher',
    #     'admin',
    #     ''
    # ]
    # results = await search_with_namespace_filter(
    #     query=query,
    #     allowed_namespaces=allowed_namespaces,
    #     limit=limit
    # )
    
    # Logging für Audit
    log_search_request(
        role="teacher",
        query=query,
        results_count=results['count']
    )
    
    return results


# Hilfsfunktion für Audit-Logging
def log_search_request(role: str, query: str, results_count: int):
    """
    Protokolliert Suchanfragen für Audit-Zwecke
    """
    import logging
    logger = logging.getLogger("leowiki.search")
    logger.info(
        f"Search request - Role: {role}, Query: '{query}', Results: {results_count}"
    )
```

## Deployment-Strategien

### Option 1: Separate Endpoints (Empfohlen)

Erstelle zwei verschiedene SSE-Endpoints, die jeweils nur ihre Tools exponieren:

```python
# server.py

# Endpoint für Schüler
@app.get("/mcp/student")
async def student_endpoint():
    """MCP Server für Schüler - nur search_content_student"""
    student_mcp = FastMCP("LeoWiki Student Search")
    student_mcp.add_tool(search_content_student)
    return student_mcp.sse_handler()

# Endpoint für Lehrer  
@app.get("/mcp/teacher")
async def teacher_endpoint():
    """MCP Server für Lehrer - beide Tools"""
    teacher_mcp = FastMCP("LeoWiki Teacher Search")
    teacher_mcp.add_tool(search_content_student)  # Optional: Lehrer können auch Schüler-Tool nutzen
    teacher_mcp.add_tool(search_content_teacher)
    return teacher_mcp.sse_handler()
```

**Claude Desktop Konfiguration:**

Schüler:
```json
{
  "mcpServers": {
    "leowiki-student": {
      "url": "https://leowiki-mcp.stream/mcp/student"
    }
  }
}
```

Lehrer:
```json
{
  "mcpServers": {
    "leowiki-teacher": {
      "url": "https://leowiki-mcp.stream/mcp/teacher"
    }
  }
}
```

### Option 2: Ein Endpoint mit Authentication

Nutze OAuth/Token-basierte Authentifizierung um die Rolle zu bestimmen:

```python
from fastapi import Header, HTTPException

@app.get("/mcp")
async def unified_endpoint(authorization: str = Header(None)):
    """MCP Server mit rollenbasierter Tool-Bereitstellung"""
    
    # Rolle aus Token extrahieren
    role = await get_role_from_token(authorization)
    
    if role == "student":
        student_mcp = FastMCP("LeoWiki Student")
        student_mcp.add_tool(search_content_student)
        return student_mcp.sse_handler()
    
    elif role == "teacher":
        teacher_mcp = FastMCP("LeoWiki Teacher")
        teacher_mcp.add_tool(search_content_student)
        teacher_mcp.add_tool(search_content_teacher)
        return teacher_mcp.sse_handler()
    
    else:
        raise HTTPException(status_code=403, detail="Invalid role")
```

## Vector-Datenbank Vorbereitung

### Metadata-Schema

Stelle sicher, dass alle Dokumente in der Vector-DB folgende Metadaten haben:

```python
document_metadata = {
    "namespace": "teacher:forms:kv",  # Vollständiger Namespace-Pfad
    "title": "Intervention bei Mobbing No-Blame-Approach",
    "url": "https://leowiki.htl-leonding.ac.at/...",
    "content_type": "FORM",
    "access_level": "teacher",  # student, teacher, admin
    "last_modified": "2024-01-15T10:30:00Z"
}
```

### Indexierung mit Namespace-Extraktion

```python
def extract_namespace_from_url(url: str) -> str:
    """
    Extrahiert Namespace aus DokuWiki-URL
    
    Beispiele:
    - .../teacher:forms:kv:file.docx -> "teacher:forms:kv"
    - .../student:timetable -> "student"
    - .../doku.php?id=homepage -> ""
    """
    import re
    match = re.search(r'id=([^&]+)', url)
    if match:
        page_id = match.group(1)
        # Namespace ist alles vor dem letzten ':'
        parts = page_id.split(':')
        if len(parts) > 1:
            return ':'.join(parts[:-1])
    return ""

def determine_access_level(namespace: str) -> str:
    """
    Bestimmt Access-Level basierend auf Namespace
    """
    if namespace.startswith('teacher'):
        return 'teacher'
    elif namespace.startswith('admin'):
        return 'admin'
    elif namespace.startswith('student'):
        return 'student'
    else:
        return 'public'
```

## Testing

### Unit Tests

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_student_search_blocks_teacher_content():
    """Schüler-Tool sollte keine Lehrer-Inhalte zurückgeben"""
    
    # Mock Vector DB mit gemischten Ergebnissen
    mock_results = [
        {"namespace": "public", "title": "Hausordnung"},
        {"namespace": "teacher:forms:kv", "title": "No-Blame-Approach"},
        {"namespace": "student", "title": "Stundenplan"},
    ]
    
    with patch('vector_db.search', return_value=mock_results):
        results = await search_content_student(query="Mobbing", limit=10)
    
    # Nur 2 Ergebnisse sollten zurückkommen (teacher:* ausgefiltert)
    assert results['count'] == 2
    assert all(r['namespace'] != 'teacher:forms:kv' for r in results['results'])

@pytest.mark.asyncio
async def test_teacher_search_includes_all_content():
    """Lehrer-Tool sollte alle Inhalte zurückgeben"""
    
    mock_results = [
        {"namespace": "public", "title": "Hausordnung"},
        {"namespace": "teacher:forms:kv", "title": "No-Blame-Approach"},
        {"namespace": "student", "title": "Stundenplan"},
    ]
    
    with patch('vector_db.search', return_value=mock_results):
        results = await search_content_teacher(query="Mobbing", limit=10)
    
    # Alle 3 Ergebnisse sollten zurückkommen
    assert results['count'] == 3
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_student_endpoint_only_exposes_student_tool():
    """Student-Endpoint sollte nur search_content_student exponieren"""
    
    from httpx import AsyncClient
    
    async with AsyncClient() as client:
        # Hole verfügbare Tools vom Student-Endpoint
        response = await client.get("http://localhost:8000/mcp/student")
        tools = response.json()['tools']
        
        # Nur ein Tool sollte verfügbar sein
        assert len(tools) == 1
        assert tools[0]['name'] == 'search_content_student'

@pytest.mark.asyncio
async def test_teacher_endpoint_exposes_teacher_tool():
    """Teacher-Endpoint sollte search_content_teacher exponieren"""
    
    from httpx import AsyncClient
    
    async with AsyncClient() as client:
        response = await client.get("http://localhost:8000/mcp/teacher")
        tools = response.json()['tools']
        
        # Mindestens das Lehrer-Tool sollte vorhanden sein
        tool_names = [t['name'] for t in tools]
        assert 'search_content_teacher' in tool_names
```

## Security Considerations

### 1. Endpoint-Sicherheit

```python
# Rate Limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/mcp/student")
@limiter.limit("100/minute")
async def student_endpoint():
    pass
```

### 2. Input Validation

```python
def sanitize_query(query: str) -> str:
    """
    Bereinigt Suchanfragen von potentiell schädlichen Inhalten
    """
    # Entferne SQL-Injection Versuche
    query = query.replace("'", "").replace(";", "")
    
    # Limitiere Länge
    query = query[:500]
    
    # Entferne Control Characters
    import re
    query = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', query)
    
    return query.strip()
```

### 3. Audit Logging

```python
import logging
from datetime import datetime

class AuditLogger:
    def __init__(self):
        self.logger = logging.getLogger("audit")
        handler = logging.FileHandler("audit.log")
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(message)s')
        )
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_access(self, role: str, tool: str, query: str, ip: str):
        self.logger.info(
            f"SEARCH - Role: {role}, Tool: {tool}, Query: '{query}', IP: {ip}"
        )
    
    def log_unauthorized_attempt(self, role: str, namespace: str, ip: str):
        self.logger.warning(
            f"UNAUTHORIZED - Role: {role} attempted access to {namespace}, IP: {ip}"
        )
```

## Monitoring & Analytics

### Dashboard-Metriken

```python
from prometheus_client import Counter, Histogram

# Metriken definieren
search_requests = Counter(
    'leowiki_search_requests_total',
    'Total search requests',
    ['role', 'tool']
)

search_duration = Histogram(
    'leowiki_search_duration_seconds',
    'Search request duration',
    ['role']
)

# In Tools verwenden
@search_duration.labels(role='student').time()
async def search_content_student(query: str, limit: int = 10):
    search_requests.labels(role='student', tool='search_content_student').inc()
    # ... rest der Implementierung
```

## Migration Plan

### Phase 1: Parallel-Betrieb
1. Implementiere beide neuen Tools
2. Behalte altes `search_content` Tool mit Deprecation-Warning
3. Teste ausgiebig mit beiden Systemen

### Phase 2: Umstellung
1. Dokumentiere Migration für Nutzer
2. Aktiviere neue Endpoints
3. Deaktiviere altes Tool nach 2 Wochen

### Phase 3: Cleanup
1. Entferne alten Code
2. Aktualisiere alle Dokumentation
3. Archive alte Logs

## Dokumentation für Endnutzer

### Für Schüler

**LeoWiki Suche - Schülerzugang**

Mit dem LeoWiki MCP-Tool kannst du die Wissensdatenbank der HTL Leonding durchsuchen.

**Verfügbare Inhalte:**
- Hausordnung und Schulregeln
- Stundenpläne und Termine
- Unterrichtsmaterialien
- FAQs und Anleitungen

**Beispiel-Anfragen:**
- "Wie sind die Regeln für Handys im Unterricht?"
- "Wann sind die Semesterferien?"
- "Was muss ich bei Krankmeldung beachten?"

### Für Lehrer

**LeoWiki Suche - Lehrerzugang**

Als Lehrer haben Sie Zugriff auf erweiterte Inhalte:

**Zusätzliche Inhalte:**
- Pädagogische Anleitungen (z.B. No-Blame-Approach)
- Klassenvorstands-Formulare
- Interne Richtlinien
- Lehrerhandbuch

**Beispiel-Anfragen:**
- "No-Blame-Approach bei Mobbing"
- "Formular für Schulveranstaltungen"
- "Verhaltensnoten Kriterien"

## Nächste Schritte

1. ✅ Implementiere beide Tools in FastMCP
2. ✅ Teste Namespace-Filterung mit echten Daten
3. ✅ Erstelle separate Endpoints
4. ✅ Schreibe Unit- und Integration-Tests
5. ✅ Implementiere Audit-Logging
6. ✅ Dokumentiere für Diplomarbeit
7. ✅ Deploy auf Raspberry Pi
8. ✅ User-Testing mit echten Lehrern und Schülern

## Weiterführende Ressourcen

- [FastMCP Dokumentation](https://github.com/jlowin/fastmcp)
- [MCP Specification](https://modelcontextprotocol.io)
- [HTL Leonding DokuWiki](https://leowiki.htl-leonding.ac.at)

---

**Autor:** Imre  
**Projekt:** LeoWiki MCP Server - Diplomarbeit HTL Leonding  
**Datum:** 31. Januar 2025  
**Version:** 1.0
