# LeoWiki MCP Server

**HTL Leonding Educational Content Search with Role-Based Access Control**

A production-ready Model Context Protocol (MCP) server providing semantic search over educational materials with hierarchical role-based access control (RBAC). Deployed on Raspberry Pi with Docker.

[![CI](https://github.com/Imre7777/mcp-diploma-thesis-final/actions/workflows/ci.yml/badge.svg)](https://github.com/Imre7777/mcp-diploma-thesis-final/actions/workflows/ci.yml)
[![Live](https://img.shields.io/badge/Live-leowiki--mcp.stream-blue)](https://leowiki-mcp.stream)
[![MCP](https://img.shields.io/badge/Protocol-MCP%202.0-green)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.11+-yellow)](https://python.org)

---

## Features

### Core
- **Semantic Search** - Vector search using OpenAI embeddings (text-embedding-3-large, 3072 dimensions)
- **Two-Tool RBAC** - Separate `search_content_student` and `search_content_teacher` tools (security by design)
- **OAuth 2.1** - Scalekit integration with JWT validation
- **HTTP Streamable** - FastAPI server with Server-Sent Events (SSE)
- **Auto Ingestion** - Watchdog service monitors for new JSONL files and updates Qdrant

### FastMCP 3.0 Professional Features
- **6 MCP Resources** - Metadata and dynamic content exposure (Admin only)
- **2 MCP Prompts** - Educational templates for structured LLM interactions
- **4 Custom Middleware** - Request logging, user context, RBAC enforcement, audit trails
- **Progress Reporting** - Real-time search progress feedback
- **Tool Annotations** - Hints for LLM optimization (readOnly, idempotent)
- **Query Logging** - Persistent logging for educational analytics (JSONL)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        INTERNET                                 │
│                 https://leowiki-mcp.stream                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Port 443 (HTTPS)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      mcp-caddy                                  │
│    • TLS Terminierung (Let's Encrypt)                           │
│    • Reverse Proxy                                              │
│    • SSE Support (flush_interval -1)                            │
│    • Security Headers (HSTS, XSS, etc.)                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Port 8000 (HTTP, intern)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      mcp-server                                 │
│    • FastMCP 3.0 Protocol                                       │
│    • OAuth 2.1 (Scalekit)                                       │
│    • 5 Tools, 6 Resources, 2 Prompts                            │
│    • 4 Middleware Components + Query Logging                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Port 6333 (HTTP, intern)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      mcp-qdrant                                 │
│    • Vector Database                                            │
│    • 757+ Documents indexed                                     │
│    • Cosine Similarity Search                                   │
└─────────────────────────────────────────────────────────────────┘
                           ▲
                           │
┌─────────────────────────────────────────────────────────────────┐
│                      mcp-watchdog                               │
│    • Monitors data/incoming/ for JSONL files                    │
│    • Auto-ingests new content                                   │
│    • CLEAR_COLLECTION_BEFORE_INGEST=true                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## MCP Capabilities

### Tools (5)

| Tool | Description | Access |
|------|-------------|--------|
| `search_content_student` | Semantic search (student content only) | Student, Teacher, Admin |
| `search_content_teacher` | Semantic search (full access) | Teacher, Admin |
| `get_collection_stats` | Database statistics | Admin only |
| `get_query_statistics` | Query logging analytics | Admin only |
| `health_check` | Server status | All users |

**Security by Design:** Two separate search tools prevent RBAC bypass via parameter manipulation. Teachers can use both search tools to compare results.

### Resources (6) - Admin Only

| URI | Description | Type |
|-----|-------------|------|
| `leowiki://categories` | Content categories (SEW, NWT, etc.) | Static |
| `leowiki://access-levels` | RBAC documentation | Static |
| `leowiki://search-hints` | Search tips and best practices | Static |
| `leowiki://system-prompt` | Claude behavioral guidelines | Static |
| `leowiki://stats` | Live collection statistics | Dynamic |
| `leowiki://recent/{count}` | Recently updated content | Template |

**Note:** Resources are hidden from students and teachers for security reasons (prevents prompt injection, hides system architecture).

### Prompts (2) - All Roles

| Prompt | Description |
|--------|-------------|
| `explain_topic` | Structured topic explanation (pedagogical) |
| `summarize_search` | Search result synthesis |

### Middleware (4)

1. **RequestLoggingMiddleware** - Correlation IDs, timing, structured logs
2. **UserContextMiddleware** - JWT claims extraction → MCP context
3. **RBACEnforcementMiddleware** - Tool-level access control + tool list filtering
4. **AuditLoggingMiddleware** - DSGVO-compliant audit trails (pseudonymization)

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API key

### Local Development

```bash
# Clone
git clone https://github.com/Imre7777/mcp-diploma-thesis-final.git
cd mcp-diploma-thesis-final

# Create .env
cp env.example .env
# Edit .env and add OPENAI_API_KEY

# Start services
docker compose up -d

# Check status
docker compose ps
```

### Production Deployment (Raspberry Pi)

```bash
# SSH to Pi
ssh imreo@leowiki-mcp.stream

# Deploy
cd ~/mcp-diploma-thesis-final
git pull
docker compose up -d --build
```

---

## Project Structure

```
mcp-diploma-thesis-final/
├── main.py                      # Server entry point
├── Dockerfile                   # MCP server image
├── Dockerfile.watchdog          # Watchdog service image
├── docker-compose.yml           # Multi-service deployment
├── Caddyfile                    # Reverse proxy config
│
├── src/
│   ├── auth/                    # OAuth flow
│   ├── backends/                # Qdrant client
│   ├── config/                  # Server configuration
│   ├── middleware/
│   │   ├── scalekit_auth.py    # OAuth 2.1 validation
│   │   └── mcp_middleware.py   # FastMCP middleware (4 components)
│   ├── pipeline/
│   │   ├── jsonl_ingestion.py  # JSONL processing
│   │   └── watchdog_service.py # File monitoring
│   ├── prompts/
│   │   └── educational.py      # 2 prompt templates
│   ├── resources/
│   │   ├── metadata.py         # 4 static resources
│   │   └── content.py          # 2 dynamic resources
│   ├── server/
│   │   ├── lifespan.py         # Dependency injection
│   │   └── oauth_metadata.py   # OAuth discovery
│   ├── tools/
│   │   └── search_tools.py     # 5 tools (search, stats, health)
│   └── utils/
│       ├── embeddings.py       # OpenAI embedding service
│       └── query_logger.py     # Persistent query logging (JSONL)
│
├── data/
│   ├── incoming/               # Drop JSONL files here
│   ├── processed/              # Successfully processed
│   ├── failed/                 # Failed ingestions
│   └── statistics/             # Query logs for analytics
│
├── docs/                       # Documentation
│   └── refactor/               # Enhancement plans & references
└── tests/                      # Test suite
```

---

## Data Ingestion

### For Your Colleague (Scraper)

1. Create JSONL file with pre-computed embeddings:
```json
{"id": "doc-1", "text": "Content...", "embedding": [0.1, 0.2, ...], "metadata": {...}}
```

2. Upload to server:
```bash
scp embedded_chunks.jsonl imreo@leowiki-mcp.stream:~/mcp-diploma-thesis-final/data/incoming/
```

3. Watchdog automatically:
   - Detects new file
   - Clears existing collection (`CLEAR_COLLECTION_BEFORE_INGEST=true`)
   - Imports all documents
   - Moves file to `data/processed/`

---

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional (defaults shown)
HTTP_HOST=0.0.0.0
HTTP_PORT=8000
VECTOR_DB_URL=http://qdrant:6333
DEFAULT_COLLECTION=educational_content
ENABLE_RBAC=true
ENABLE_AUTH=false  # Set true for production

# OAuth (for production)
SCALEKIT_ENV_URL=https://...
SCALEKIT_CLIENT_ID=...
SCALEKIT_CLIENT_SECRET=...
```

---

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | No | Health check |
| `/docs` | GET | No | Swagger UI |
| `/.well-known/oauth-protected-resource` | GET | No | OAuth discovery |
| `/mcp` | POST | Yes* | MCP protocol |
| `/sse` | GET | Yes* | Server-Sent Events |

*Authentication required when `ENABLE_AUTH=true`

---

## Testing

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src
```

---

## Academic Context

This project is part of a diploma thesis at HTL Leonding investigating:

1. **RQ1**: Implementation of RBAC in vector databases
2. **RQ2**: Optimal data structures for educational content search
3. **RQ3**: Automated ingestion pipelines with quality control

**Key Findings:**
- Two-tool RBAC architecture prevents parameter manipulation
- Post-filtering approach handles mixed-access content
- Watchdog service enables seamless content updates

---

## Security

- **OAuth 2.1** via Scalekit with JWT validation
- **RBAC** enforced at tool level (not parameter level)
- **HTTPS** via Caddy with automatic Let's Encrypt
- **Error Masking** hides internal details from clients
- **Audit Logging** with pseudonymization (DSGVO compliant)
- **Secrets** managed via environment variables

---

## Contributing

This is a diploma thesis project.

- **GitHub**: https://github.com/Imre7777/mcp-diploma-thesis-final
- **Issues**: Bug reports welcome
- **Documentation**: See `docs/` folder

---

## License

Educational project - HTL Leonding Diploma Thesis

---

## Acknowledgments

- **HTL Leonding** - Project supervision
- **Qdrant** - Vector database
- **FastMCP** - MCP protocol implementation
- **OpenAI** - Embedding API
- **Scalekit** - OAuth infrastructure

---

**Status**: Production Ready  
**Version**: 2.1.0  
**Last Updated**: 2026-02-05
