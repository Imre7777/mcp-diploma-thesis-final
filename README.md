<div align="center">

# 🎓 LeoWiki MCP Server

### Semantische Suche über Unterrichtsmaterialien mit rollenbasierter Zugriffskontrolle

A production-ready **Model Context Protocol (MCP)** server that gives LLMs secure, role-aware semantic search over educational content — deployed on a Raspberry Pi with Docker.

<br>

[![CI](https://github.com/Imre7777/mcp-diploma-thesis-final/actions/workflows/ci.yml/badge.svg)](https://github.com/Imre7777/mcp-diploma-thesis-final/actions/workflows/ci.yml)
[![Live Demo](https://img.shields.io/badge/Live-leowiki--mcp.stream-2ea44f?logo=serverfault&logoColor=white)](https://leowiki-mcp.stream)
[![Grade](https://img.shields.io/badge/Diplomarbeit-Sehr%20gut-brightgreen)](#-academic-context)

<br>

![Python](https://img.shields.io/badge/Python_3.11+-3776AB?style=flat&logo=python&logoColor=white)
![FastMCP](https://img.shields.io/badge/FastMCP_3.0-000000?style=flat&logo=fastapi&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Qdrant](https://img.shields.io/badge/Qdrant_Vector_DB-DC244C?style=flat&logo=qdrant&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI_Embeddings-412991?style=flat&logo=openai&logoColor=white)
![OAuth2.1](https://img.shields.io/badge/OAuth_2.1-EB5424?style=flat&logo=auth0&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![Caddy](https://img.shields.io/badge/Caddy-1F88C0?style=flat&logo=caddy&logoColor=white)

</div>

---

## 📌 Über dieses Projekt

Dieses Repository ist die **Diplomarbeit** von **Imre Obermüller** und **Jan Ritt** an der **HTL Leonding** (Betreuung: **Rainer Stropek**), abgeschlossen 2026 mit der Beurteilung **„Sehr gut"**. Die Arbeit dient an der Schule inzwischen als **Referenzvorlage für weitere Jahrgänge**.

Die Aufgabe: ein bestehendes Schul-Wiki („LeoWiki") so aufbereiten, dass ein LLM (z. B. Claude) **inhaltlich und rollengerecht** darauf zugreifen kann — Schüler:innen sehen andere Inhalte als Lehrkräfte, und alles läuft über einen sauber abgesicherten, öffentlich erreichbaren MCP-Server.

> 🔗 **Live:** [leowiki-mcp.stream](https://leowiki-mcp.stream) · **API-Docs (Swagger):** [/docs](https://leowiki-mcp.stream/docs)

---

## ⭐ Highlights

- 🔍 **Semantische Suche** über 6.000+ indexierte Dokumente (OpenAI `text-embedding-3-large`, 3072 Dim., Cosine-Similarity in Qdrant)
- 🔐 **RBAC „by design":** zwei getrennte Such-Tools statt eines Parameters — das verhindert eine Rechte-Umgehung durch Parameter-Manipulation (Zero-Trust, serverseitige Filterung)
- 🛡️ **OAuth 2.1** (Scalekit) mit JWT-Validierung, **HTTPS** via Caddy & Let's Encrypt, **DSGVO-konformes** Audit-Logging mit Pseudonymisierung
- 🧩 **Voller MCP-Funktionsumfang:** 5 Tools, 6 Resources, 2 Prompts, 4 eigene Middleware-Komponenten (FastMCP 3.0)
- 🔄 **Automatische Ingestion:** Watchdog-Service erkennt neue JSONL-Dateien und aktualisiert die Vektor-DB ohne Downtime
- 🐳 **Containerisiert & deployed:** Multi-Service Docker-Compose-Stack, produktiv auf einem Raspberry Pi
- 📊 **Messbar:** eigene Benchmark-Suite (Such-Qualität & Transport-Vergleich) unter `data/benchmark/`

---

## 📑 Inhalt

- [Architektur](#-architektur)
- [MCP-Funktionen](#-mcp-funktionen)
- [Tech-Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Konfiguration](#-konfiguration)
- [API-Endpunkte](#-api-endpunkte)
- [Tests](#-tests)
- [Screenshots](#-screenshots)
- [Academic Context](#-academic-context)
- [Autoren](#-autoren)

---

## 🏛 Architektur

```
                          INTERNET
                 https://leowiki-mcp.stream
                            │  443 / HTTPS
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  mcp-caddy        TLS (Let's Encrypt) · Reverse Proxy · SSE   │
└──────────────────────────┬───────────────────────────────────┘
                            │  8000 (intern)
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  mcp-server       FastMCP 3.0 · OAuth 2.1 (Scalekit)          │
│                   5 Tools · 6 Resources · 2 Prompts           │
│                   4 Middleware + Query-Logging                │
└──────────────────────────┬───────────────────────────────────┘
                            │  6333 (intern)
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  mcp-qdrant       Vektor-DB · 6.000+ Docs · Cosine-Similarity │
└──────────────────────────────────────────────────────────────┘
                            ▲
┌──────────────────────────────────────────────────────────────┐
│  mcp-watchdog     überwacht data/incoming/ → Auto-Ingestion   │
└──────────────────────────────────────────────────────────────┘
```

---

## 🧩 MCP-Funktionen

### Tools (5)

| Tool | Beschreibung | Zugriff |
|------|--------------|---------|
| `search_content_student` | Semantische Suche (nur Schüler-Inhalte) | Student, Teacher, Admin |
| `search_content_teacher` | Semantische Suche (voller Zugriff) | Teacher, Admin |
| `get_collection_stats` | Datenbank-Statistiken | Admin |
| `get_query_statistics` | Analyse der Query-Logs | Admin |
| `health_check` | Server-Status | Alle |

> **Security by Design:** Zwei getrennte Such-Tools statt eines `role`-Parameters — so lässt sich die Zugriffsstufe nicht durch manipulierte Parameter aushebeln. Lehrkräfte nutzen beide Tools, um Ergebnisse zu vergleichen.

### Resources (6) · Admin-only

`leowiki://categories` · `leowiki://access-levels` · `leowiki://search-hints` · `leowiki://system-prompt` · `leowiki://stats` (dynamisch) · `leowiki://recent/{count}` (Template)

*Für Schüler:innen und Lehrkräfte ausgeblendet — verhindert Prompt-Injection und verbirgt die Systemarchitektur.*

### Prompts (2)

`explain_topic` — didaktisch strukturierte Themen-Erklärung · `summarize_search` — Synthese von Suchergebnissen

### Middleware (4)

`RequestLogging` (Correlation-IDs, Timing) · `UserContext` (JWT-Claims → MCP-Context) · `RBACEnforcement` (Tool-Level-Zugriff + Tool-List-Filterung) · `AuditLogging` (DSGVO-konform, pseudonymisiert)

---

## 🛠 Tech-Stack

| Bereich | Technologien |
|---------|--------------|
| **Sprache** | Python 3.11+ |
| **MCP / API** | FastMCP 3.0, FastAPI, Server-Sent Events (SSE) |
| **KI / Suche** | OpenAI `text-embedding-3-large`, Qdrant (Vektor-DB), Cosine-Similarity |
| **Auth / Security** | OAuth 2.1 (Scalekit), JWT, RBAC, Audit-Logging (DSGVO) |
| **Infra / Deployment** | Docker & Docker Compose, Caddy (Reverse Proxy, TLS), Raspberry Pi |
| **Qualität** | pytest, GitHub Actions (CI), eigene Benchmark-Suite |

---

## 🚀 Quick Start

**Voraussetzungen:** Docker & Docker Compose · OpenAI API Key

```bash
# Repository klonen
git clone https://github.com/Imre7777/mcp-diploma-thesis-final.git
cd mcp-diploma-thesis-final

# Umgebungsvariablen anlegen und OPENAI_API_KEY eintragen
cp env.example .env

# Services starten
docker compose up -d
docker compose ps
```

Danach lokal erreichbar unter `http://localhost:8000` (Swagger-UI: `http://localhost:8000/docs`).

---

## ⚙️ Konfiguration

```bash
# Erforderlich
OPENAI_API_KEY=sk-...

# Optional (Defaults)
HTTP_HOST=0.0.0.0
HTTP_PORT=8000
VECTOR_DB_URL=http://qdrant:6333
DEFAULT_COLLECTION=educational_content
ENABLE_RBAC=true
ENABLE_AUTH=false          # in Produktion: true

# OAuth (Produktion)
SCALEKIT_ENV_URL=https://...
SCALEKIT_CLIENT_ID=...
SCALEKIT_CLIENT_SECRET=...
```

Secrets liegen ausschließlich in `.env` (per `.gitignore` ausgeschlossen) — keine hartkodierten Zugangsdaten im Code.

---

## 🌐 API-Endpunkte

| Endpoint | Methode | Auth | Beschreibung |
|----------|---------|------|--------------|
| `/health` | GET | – | Health-Check |
| `/docs` | GET | – | Swagger-UI |
| `/.well-known/oauth-protected-resource` | GET | – | OAuth-Discovery |
| `/mcp` | POST | ✳ | MCP-Protokoll |
| `/sse` | GET | ✳ | Server-Sent Events |

✳ Authentifizierung erforderlich, wenn `ENABLE_AUTH=true`.

---

## ✅ Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
pytest tests/ --cov=src        # mit Coverage
```

---

## 📸 Screenshots

<!--
  TODO: Screenshots hier einfügen für maximale Wirkung bei Recruitern.
  Empfohlen: 2–3 Bilder in docs/img/ ablegen und unten einbinden, z. B.:

  1. Claude Desktop, das den MCP-Server nutzt (Suche + Ergebnis)
  2. Swagger-UI unter /docs
  3. Ein Benchmark-Diagramm aus data/benchmark/

  Einbindung:
  ![Claude Desktop nutzt den MCP-Server](docs/img/claude-desktop.png)
  ![Swagger UI](docs/img/swagger.png)
-->

> Screenshots folgen. In der Zwischenzeit ist der Server **live testbar** unter [leowiki-mcp.stream/docs](https://leowiki-mcp.stream/docs), und Benchmark-Ergebnisse liegen unter [`data/benchmark/`](data/benchmark/).

---

## 🎓 Academic Context

Diplomarbeit an der **HTL Leonding**, Abteilung Informatik — Beurteilung **„Sehr gut"**. Untersuchte Forschungsfragen:

1. **RQ1** — Umsetzung von RBAC in Vektor-Datenbanken
2. **RQ2** — Optimale Datenstrukturen für die Suche in Unterrichtsinhalten
3. **RQ3** — Automatisierte Ingestion-Pipelines mit Qualitätskontrolle

**Zentrale Erkenntnisse:** Die Zwei-Tool-RBAC-Architektur verhindert Parameter-Manipulation zuverlässig; ein Post-Filtering-Ansatz beherrscht Inhalte mit gemischten Zugriffsstufen; der Watchdog-Service ermöglicht nahtlose Inhalts-Updates.

Ausführliche Dokumentation (Architektur, Deployment, Auth) im Ordner [`docs/`](docs/).

---

## 👥 Autoren

- **Imre Obermüller** — [GitHub](https://github.com/Imre7777) · imre.obermueller@gmail.com
- **Jan Ritt**
- Betreuung: **Rainer Stropek**

---

## 🙏 Acknowledgments

**HTL Leonding** (Projektbetreuung) · **Qdrant** (Vektor-DB) · **FastMCP** (MCP-Implementierung) · **OpenAI** (Embeddings) · **Scalekit** (OAuth)

---

<div align="center">

**Status:** Production Ready · **Version:** 2.0.1

*Educational project — HTL Leonding Diploma Thesis*

</div>
