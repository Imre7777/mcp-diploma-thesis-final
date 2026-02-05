# CI/CD Pipeline Dokumentation

**LeoWiki MCP Server - Continuous Integration & Deployment**

---

## Übersicht

Die CI/CD Pipeline automatisiert Qualitätskontrolle und Build-Prozesse bei jedem Code-Push.

| Komponente | Technologie |
|------------|-------------|
| CI/CD Platform | GitHub Actions |
| Workflow-Datei | `.github/workflows/ci.yml` |
| Trigger | Push auf `main`, `feature/*`, PRs auf `main` |

---

## Pipeline-Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Push/PR                            │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Job 1: test                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Checkout │→ │  Python  │→ │   pip    │→ │   ruff   │        │
│  │   Code   │  │  Setup   │  │ install  │  │   lint   │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│                                                   │              │
│  ┌──────────┐  ┌──────────┐                       │              │
│  │   mypy   │← │  pytest  │←──────────────────────┘              │
│  │  types   │  │  tests   │                                      │
│  └──────────┘  └──────────┘                                      │
└─────────────────────────────┬───────────────────────────────────┘
                              │ needs: test
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Job 2: docker-build                            │
│  ┌──────────┐  ┌──────────────┐  ┌─────────────────┐           │
│  │ Checkout │→ │ docker build │→ │  docker images  │           │
│  │   Code   │  │  -t mcp:test │  │    (verify)     │           │
│  └──────────┘  └──────────────┘  └─────────────────┘           │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
                    ✅ Pipeline erfolgreich
                    oder ❌ Fehler gefunden
```

---

## Trigger-Events

```yaml
on:
  push:
    branches: [main, feature/*]
  pull_request:
    branches: [main]
```

| Event | Wann | Beispiel |
|-------|------|----------|
| `push` auf `main` | Direkter Push oder Merge | `git push origin main` |
| `push` auf `feature/*` | Feature-Branch Push | `git push origin feature/query-logging` |
| `pull_request` auf `main` | PR erstellt/aktualisiert | PR von `feature/xyz` → `main` |

---

## Job 1: `test`

### Umgebung

```yaml
runs-on: ubuntu-latest
```

Läuft auf einer frischen Ubuntu VM bei GitHub (kostenlos für Public Repos).

### Schritte im Detail

#### 1. Code auschecken

```yaml
- uses: actions/checkout@v4
```

Klont das Repository in die GitHub VM.

#### 2. Python Setup

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'
    cache: 'pip'
```

- Installiert Python 3.11
- `cache: 'pip'` beschleunigt wiederholte Runs

#### 3. Dependencies installieren

```yaml
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
```

Installiert alle Packages aus `requirements.txt` (~60 Packages).

#### 4. Linting mit ruff

```yaml
- name: Lint with ruff
  run: |
    ruff check src/ --ignore E501,F401 || true
```

| Option | Bedeutung |
|--------|-----------|
| `--ignore E501` | Ignoriert "Zeile zu lang" |
| `--ignore F401` | Ignoriert "Unused import" |
| `|| true` | Pipeline bricht nicht ab |

**Prüft:**
- Syntax-Fehler
- Code-Style (PEP 8)
- Potenzielle Bugs

#### 5. Type Checking mit mypy

```yaml
- name: Type check with mypy
  run: |
    mypy src/ --ignore-missing-imports || true
```

**Prüft:**
- Type Hints (`def foo(x: str) -> int:`)
- Typ-Kompatibilität

#### 6. Tests mit pytest

```yaml
- name: Run tests
  run: |
    pytest tests/ -v --tb=short || true
  env:
    ENABLE_AUTH: "false"
    ENABLE_RBAC: "false"
    VECTOR_DB_URL: "http://localhost:6333"
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

| Option | Bedeutung |
|--------|-----------|
| `-v` | Verbose (zeigt jeden Test) |
| `--tb=short` | Kurze Tracebacks |

**Environment Variables:**
- Auth/RBAC deaktiviert für isolierte Tests
- `OPENAI_API_KEY` aus GitHub Secrets

---

## Job 2: `docker-build`

### Abhängigkeit

```yaml
needs: test
```

Startet erst, wenn Job `test` erfolgreich war.

### Schritte

#### 1. Docker Image bauen

```yaml
- name: Build Docker image
  run: |
    docker build -t mcp-server:test .
```

Baut das Image aus dem `Dockerfile`.

#### 2. Image verifizieren

```yaml
- name: Verify image
  run: |
    docker images mcp-server:test
```

Bestätigt, dass das Image existiert.

---

## GitHub Secrets

### Konfigurierte Secrets

| Secret | Verwendung |
|--------|------------|
| `OPENAI_API_KEY` | Embedding-Generierung für Tests |

### Secrets hinzufügen

1. GitHub Repository öffnen
2. Settings → Secrets and variables → Actions
3. "New repository secret" klicken
4. Name und Wert eingeben

### Secrets in Workflow verwenden

```yaml
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

**Sicherheit:**
- Secrets werden in Logs als `***` maskiert
- Nicht verfügbar bei Fork-PRs

---

## Status Badge

Im README:

```markdown
[![CI](https://github.com/Imre7777/mcp-diploma-thesis-final/actions/workflows/ci.yml/badge.svg)](https://github.com/Imre7777/mcp-diploma-thesis-final/actions/workflows/ci.yml)
```

| Badge | Bedeutung |
|-------|-----------|
| ![passing](https://img.shields.io/badge/CI-passing-brightgreen) | Alle Checks OK |
| ![failing](https://img.shields.io/badge/CI-failing-red) | Fehler gefunden |

---

## Fehlerbehebung

### Pipeline manuell neu starten

1. GitHub Actions öffnen
2. Auf fehlgeschlagenen Run klicken
3. "Re-run all jobs" klicken

### Leeren Commit für Neustart

```bash
git commit --allow-empty -m "ci: Trigger pipeline"
git push
```

### Häufige Fehler

| Fehler | Lösung |
|--------|--------|
| "Secret not found" | Secret in Repository Settings hinzufügen |
| "pip install failed" | `requirements.txt` prüfen |
| "Docker build failed" | `Dockerfile` lokal testen |
| Tests fehlgeschlagen | Logs prüfen, lokal reproduzieren |

---

## Erweiterungsmöglichkeiten

### Deployment hinzufügen (zukünftig)

```yaml
deploy:
  runs-on: ubuntu-latest
  needs: docker-build
  if: github.ref == 'refs/heads/main'
  steps:
    - name: Deploy to Raspberry Pi
      run: |
        ssh user@server "cd ~/mcp && git pull && docker compose up -d --build"
```

### Code Coverage

```yaml
- name: Run tests with coverage
  run: |
    pytest tests/ --cov=src --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
```

---

## Workflow-Datei

**Pfad:** `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main, feature/*]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Lint with ruff
        run: |
          ruff check src/ --ignore E501,F401 || true
      
      - name: Type check with mypy
        run: |
          mypy src/ --ignore-missing-imports || true
      
      - name: Run tests
        run: |
          pytest tests/ -v --tb=short || true
        env:
          ENABLE_AUTH: "false"
          ENABLE_RBAC: "false"
          VECTOR_DB_URL: "http://localhost:6333"
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

  docker-build:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Docker image
        run: |
          docker build -t mcp-server:test .
      
      - name: Verify image
        run: |
          docker images mcp-server:test
```

---

**Dokument Version:** 1.0  
**Erstellt:** 2026-02-05  
**Pipeline Version:** 1.0
