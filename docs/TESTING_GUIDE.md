# Testing Guide - LeoWiki MCP Server

## Übersicht

Der LeoWiki MCP Server verwendet **deterministische Tests** basierend auf FastMCP Best Practices. Die Tests benötigen keine externen Abhängigkeiten (Qdrant, OpenAI) und liefern reproduzierbare Ergebnisse.

**Referenz:** https://gofastmcp.com/patterns/testing

---

## Test-Suite Statistik

| Datei | Tests | Beschreibung |
|-------|-------|--------------|
| `test_tools_deterministic.py` | 21 | Tools, Resources, Prompts |
| `test_rbac_deterministic.py` | 30 | RBAC Permissions |
| `test_query_logger.py` | 11 | Query-Logging |
| **Gesamt** | **62** | |

---

## Tests Ausführen

### Im Docker Container (empfohlen)

```bash
# Alle Tests
docker exec mcp-server python -m pytest tests/ -v

# Einzelne Test-Datei
docker exec mcp-server python -m pytest tests/test_tools_deterministic.py -v

# Mit Coverage
docker exec mcp-server python -m pytest tests/ --cov=src --cov-report=term-missing
```

### Lokal (falls Python-Umgebung vorhanden)

```bash
cd /home/imreo/mcp-diploma-thesis-final
python -m pytest tests/ -v
```

### In GitHub Actions CI

Die Tests werden automatisch bei jedem Push ausgeführt:
- Workflow: `.github/workflows/ci.yml`
- Status: https://github.com/Imre7777/mcp-diploma-thesis-final/actions

---

## Test-Architektur

### Prinzipien (FastMCP Best Practices)

1. **In-Memory Transport**: Kein Netzwerk-Overhead, Tests laufen direkt gegen Server-Instanz
2. **Mocked Dependencies**: Qdrant und OpenAI werden durch deterministische Mock-Daten ersetzt
3. **Self-Contained**: Jeder Test ist unabhängig von anderen Tests
4. **Single Behavior**: Ein Test prüft genau ein Verhalten

### Test-Server Factory

```python
def create_test_server():
    """
    Erstellt einen isolierten Test-Server mit:
    - Keine echte Qdrant-Verbindung
    - Keine echten OpenAI API-Calls
    - Kontrollierte, deterministische Antworten
    """
    mcp = FastMCP("LeoWiki-Test")
    
    # Mock-Daten für deterministische Tests
    MOCK_STUDENT_RESULTS = [
        {"title": "Java Grundlagen", "text": "...", "source": "wiki/java"},
    ]
    
    @mcp.tool(name="search_content_student")
    async def search_student(query: str) -> dict:
        # Deterministische Implementierung
        ...
    
    return mcp
```

### FastMCP Client Fixture

```python
@pytest_asyncio.fixture
async def client(test_server):
    """In-Memory Client - kein Netzwerk."""
    from fastmcp import Client
    async with Client(test_server) as c:
        yield c
```

---

## Test-Kategorien

### 1. Tool Tests (`test_tools_deterministic.py`)

**Was wird getestet:**
- Tool-Registrierung (alle Tools vorhanden)
- Student Search (Content-Filterung, keine Lehrer-Inhalte)
- Teacher Search (voller Zugriff)
- Health Check
- Input Validation (Unicode, Sonderzeichen, leere Queries)
- Error Handling (user-friendly Fehlermeldungen)

**Beispiel:**
```python
class TestStudentSearch:
    @pytest.mark.asyncio
    async def test_student_search_excludes_teacher_content(self, client):
        """Schüler dürfen keine Lehrer-Inhalte sehen."""
        result = await client.call_tool("search_content_student", {"query": "Java"})
        text = result.content[0].text
        
        assert "Prüfungsfragen" not in text  # Lehrer-Content
        assert "Notenschlüssel" not in text  # Lehrer-Content
```

### 2. Resource Tests (`test_tools_deterministic.py`)

**Was wird getestet:**
- Resources sind registriert
- JSON-Format korrekt
- Statistik-Daten vorhanden

**Beispiel:**
```python
class TestResources:
    @pytest.mark.asyncio
    async def test_categories_resource_returns_json(self, client):
        result = await client.read_resource("leowiki://categories")
        data = json.loads(result[0].text)
        assert isinstance(data, list)
```

### 3. Prompt Tests (`test_tools_deterministic.py`)

**Was wird getestet:**
- Prompts sind registriert
- Parameter werden korrekt eingefügt
- Difficulty-Level funktioniert

**Beispiel:**
```python
class TestPrompts:
    @pytest.mark.asyncio
    async def test_explain_topic_prompt(self, client):
        result = await client.get_prompt("explain_topic", {"topic": "Java"})
        assert "Java" in result.messages[0].content.text
```

### 4. RBAC Tests (`test_rbac_deterministic.py`)

**Was wird getestet:**
- Schüler-Berechtigungen (nur student search + health)
- Lehrer-Berechtigungen (student + teacher search + health)
- Admin-Berechtigungen (alles)
- Security Isolation (keine Privilege Escalation)
- Permission Matrix (parametrisierte Tests)

**Beispiel:**
```python
class TestSecurityIsolation:
    def test_student_cannot_escalate_to_teacher(self):
        """KRITISCH: Schüler dürfen nie Lehrer-Tools sehen."""
        student_tools = get_allowed_tools("student")
        assert "search_content_teacher" not in student_tools
```

### 5. Query Logger Tests (`test_query_logger.py`)

**Was wird getestet:**
- Log-Datei wird erstellt
- JSONL-Format korrekt
- Unicode wird erhalten
- Statistik-Berechnung
- Thread-Safety (100 concurrent writes)
- Edge Cases (leere Queries, lange Responses)

**Beispiel:**
```python
class TestThreadSafety:
    def test_concurrent_writes(self, logger, temp_log_dir):
        """100 gleichzeitige Schreibvorgänge."""
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(log_entry, i) for i in range(100)]
        
        # Alle 100 Einträge müssen vorhanden sein
        assert len(lines) == 100
```

---

## Neue Tests Hinzufügen

### Neuen Tool-Test hinzufügen

```python
class TestNeuerTool:
    @pytest.mark.asyncio
    async def test_tool_returns_expected(self, client):
        result = await client.call_tool("tool_name", {"param": "value"})
        assert "expected" in result.content[0].text
```

### Neuen RBAC-Test hinzufügen

```python
@pytest.mark.parametrize("role,tool,expected", [
    ("student", "new_tool", False),
    ("teacher", "new_tool", True),
    ("admin", "new_tool", True),
])
def test_new_tool_permissions(self, role, tool, expected):
    allowed = get_allowed_tools(role)
    assert (tool in allowed) == expected
```

### Mock-Daten erweitern

In `create_test_server()`:
```python
MOCK_NEW_DATA = [
    {"field": "value", ...},
]

@mcp.tool(name="new_tool")
async def new_tool() -> dict:
    return {"content": [{"type": "text", "text": str(MOCK_NEW_DATA)}]}
```

---

## Troubleshooting

### Tests finden keine Module

```bash
# Sicherstellen, dass pytest im Container verfügbar ist
docker exec mcp-server pip list | grep pytest
```

### Async Tests schlagen fehl

```python
# pytest-asyncio Konfiguration am Dateianfang
pytestmark = pytest.mark.asyncio(loop_scope="function")

# Async Fixtures mit pytest_asyncio.fixture
@pytest_asyncio.fixture
async def client(test_server):
    ...
```

### Container hat alte Test-Dateien

```bash
# Manuell kopieren
docker cp tests/test_file.py mcp-server:/app/tests/

# Oder: Container neu bauen
docker compose build mcp-server
docker compose up -d
```

---

## CI/CD Integration

Die Tests sind in die GitHub Actions CI Pipeline integriert:

```yaml
# .github/workflows/ci.yml
- name: Run tests
  run: |
    pytest tests/ -v --tb=short
  env:
    ENABLE_AUTH: "false"
    ENABLE_RBAC: "false"
```

**Trigger:**
- Push auf `main` oder `feature/*`
- Pull Requests auf `main`

**Status Badge:**
![CI](https://github.com/Imre7777/mcp-diploma-thesis-final/actions/workflows/ci.yml/badge.svg)

---

## Weiterführende Ressourcen

- [FastMCP Testing Patterns](https://gofastmcp.com/patterns/testing)
- [FastMCP Test Examples](https://github.com/jlowin/fastmcp/tree/main/tests)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
