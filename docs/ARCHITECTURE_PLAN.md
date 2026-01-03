# MCP Diploma Thesis - Complete Architecture Plan

## Project: Educational MCP Server with Role-Based Access Control

**Author**: Obermüller Imre  
**Date**: January 3, 2026  
**Version**: 2.0 (Refactored)

---

## 🎯 Executive Summary

This system provides a **Model Context Protocol (MCP) server** for educational content with:
- **Role-Based Access Control (RBAC)**: Students see filtered content, teachers see all
- **Custom OAuth Server**: Manages authentication and user roles
- **MCP Streaming Protocol**: Efficient handling of large datasets
- **Automated Data Pipeline**: Colleague uploads data → automatic Qdrant insertion
- **Remote Deployment**: Production-ready server for multiple concurrent users

---

## 🏗️ System Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        EXTERNAL USERS                            │
│  ┌──────────────┐              ┌──────────────┐                │
│  │   Students   │              │   Teachers   │                │
│  └──────┬───────┘              └──────┬───────┘                │
└─────────┼──────────────────────────────┼──────────────────────┘
          │                              │
          │   HTTPS (OAuth)              │   HTTPS (OAuth)
          │                              │
┌─────────▼──────────────────────────────▼──────────────────────┐
│                     CADDY REVERSE PROXY                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  • TLS Termination                                       │  │
│  │  • OAuth Redirect                                        │  │
│  │  │  • Rate Limiting                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────┬──────────────────────────────────────────────────────┘
          │
          │   Forward with role headers
          │
┌─────────▼──────────────────────────────────────────────────────┐
│              CUSTOM OAUTH SERVER (Python/FastAPI)               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  • User Authentication                                   │  │
│  │  • Role Management (student/teacher)                     │  │
│  │  • JWT Token Generation                                  │  │
│  │  • Session Management                                    │  │
│  │  • User Database (SQLite/PostgreSQL)                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────┬──────────────────────────────────────────────────────┘
          │
          │   JWT with role claims
          │
┌─────────▼──────────────────────────────────────────────────────┐
│                   MCP SERVER (Python/FastAPI)                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  MCP TOOLS (with Streaming)                              │  │
│  │  ┌────────────┐  ┌─────────────┐  ┌──────────────────┐  │  │
│  │  │    Ping    │  │   Vector    │  │    Advanced      │  │  │
│  │  │   Health   │  │   Search    │  │    Search        │  │  │
│  │  │   Check    │  │  (Streamed) │  │  (Filtered+      │  │  │
│  │  │            │  │             │  │   Streamed)      │  │  │
│  │  └────────────┘  └─────────────┘  └──────────────────┘  │  │
│  │                                                          │  │
│  │  ROLE-BASED ACCESS CONTROL LAYER                        │  │
│  │  • Extract JWT role                                     │  │
│  │  • Apply filters: student/teacher                       │  │
│  │  • Log access attempts                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────┬──────────────────────────────────────────────────────┘
          │
          │   Query with role filter
          │
┌─────────▼──────────────────────────────────────────────────────┐
│                    QDRANT VECTOR DATABASE                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Collections:                                            │  │
│  │  • educational_content                                   │  │
│  │    - Vectors (embeddings)                                │  │
│  │    - Metadata:                                           │  │
│  │      * content_type: "student" | "teacher" | "all"       │  │
│  │      * subject, category, date, etc.                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────▲──────────────────────────────────────────────────────┘
          │
          │   Auto-load data
          │
┌─────────┴──────────────────────────────────────────────────────┐
│              DATA LOADING PIPELINE (File Watcher)               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. Monitor /data/incoming/ directory                    │  │
│  │  2. Detect new JSON file (via SCP from colleague)        │  │
│  │  3. Parse and validate JSON structure                    │  │
│  │  4. Extract role metadata (student/teacher markers)      │  │
│  │  5. Generate embeddings                                  │  │
│  │  6. Insert into Qdrant with role metadata                │  │
│  │  7. Move to /data/processed/                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Authentication & Authorization Flow

### OAuth Flow with Role-Based Access

```
1. User visits MCP server URL
   ↓
2. Caddy intercepts → No valid session
   ↓
3. Redirect to Custom OAuth Server login page
   ↓
4. User enters credentials (username/password)
   ↓
5. OAuth Server validates credentials
   ↓
6. OAuth Server checks user role in database
   │
   ├─ Role: "student"  → Generate JWT with role claim "student"
   └─ Role: "teacher"  → Generate JWT with role claim "teacher"
   ↓
7. Return JWT token to client (as cookie or header)
   ↓
8. Client makes MCP request with JWT
   ↓
9. MCP Server extracts JWT and validates signature
   ↓
10. MCP Server extracts role from JWT claims
    ↓
11. Apply role-based filtering:
    │
    ├─ student: Filter Qdrant query → content_type IN ["student", "all"]
    └─ teacher: No filter → Show ALL content
    ↓
12. Execute MCP tool with filtered results
    ↓
13. Stream results back to client (MCP Streaming Protocol)
```

---

## 📊 Data Model

### JSON Input Format (from Colleague)

```json
{
  "documents": [
    {
      "id": "doc_001",
      "title": "Introduction to Python",
      "content": "Python is a high-level programming language...",
      "visibility": "all",
      "metadata": {
        "subject": "Computer Science",
        "difficulty": "beginner",
        "created_date": "2024-01-15"
      }
    },
    {
      "id": "doc_002",
      "title": "Student Assignment 1",
      "content": "Complete the following exercises...",
      "visibility": "student",
      "metadata": {
        "subject": "Computer Science",
        "type": "assignment",
        "due_date": "2024-02-01"
      }
    },
    {
      "id": "doc_003",
      "title": "Teacher Solution Guide",
      "content": "Answer key for assignment 1...",
      "visibility": "teacher",
      "metadata": {
        "subject": "Computer Science",
        "type": "solution",
        "confidential": true
      }
    }
  ]
}
```

**Visibility Rules:**
- `"all"`: Visible to students AND teachers
- `"student"`: Visible to students AND teachers
- `"teacher"`: Visible ONLY to teachers

### Qdrant Schema

```python
# Collection: educational_content
{
    "id": "doc_001",
    "vector": [0.123, 0.456, ...],  # 384-dim embedding
    "payload": {
        "title": "Introduction to Python",
        "content": "Python is a high-level...",
        "visibility": "all",  # KEY FIELD for filtering
        "metadata": {
            "subject": "Computer Science",
            "difficulty": "beginner",
            "created_date": "2024-01-15"
        }
    }
}
```

---

## 🛠️ Technology Stack

### Backend
- **Python 3.11+**: Core language
- **FastAPI**: Web framework for OAuth and MCP server
- **MCP SDK**: Model Context Protocol implementation
- **PyJWT**: JWT token handling
- **Sentence-Transformers**: Text embeddings (all-MiniLM-L6-v2)
- **Qdrant Client**: Vector database client
- **Watchdog**: File system monitoring
- **Pydantic**: Data validation

### Database
- **Qdrant**: Vector database for content
- **SQLite/PostgreSQL**: User management database for OAuth

### Infrastructure
- **Docker & Docker Compose**: Containerization
- **Caddy**: Reverse proxy, TLS, rate limiting
- **Systemd**: Process management on Raspberry Pi

### Security
- **JWT**: Token-based authentication
- **bcrypt**: Password hashing
- **HTTPS**: TLS encryption (Let's Encrypt via Caddy)

---

## 🔧 MCP Tools Specification

### Tool 1: Ping (Health Check)

**Purpose**: Verify server availability

**Input**: None

**Output**:
```json
{
  "status": "ok",
  "timestamp": "2026-01-03T14:30:00Z",
  "version": "2.0.0",
  "role": "student"
}
```

**Streaming**: No

---

### Tool 2: Vector Search (Standard)

**Purpose**: Semantic search in educational content

**Input**:
```json
{
  "query": "What is Python programming?",
  "limit": 10
}
```

**Output** (Streamed):
```json
{
  "results": [
    {
      "id": "doc_001",
      "score": 0.95,
      "title": "Introduction to Python",
      "content": "Python is a high-level programming language...",
      "metadata": { ... }
    },
    ...
  ],
  "total": 10,
  "filtered_by_role": "student"
}
```

**Streaming**: Yes (results streamed as they're retrieved)

**Role Filtering**:
- Student: Only see `visibility IN ["student", "all"]`
- Teacher: See ALL documents

---

### Tool 3: Advanced Search (Filtered)

**Purpose**: Search with advanced filters and metadata

**Input**:
```json
{
  "query": "Python exercises",
  "limit": 10,
  "filters": {
    "subject": "Computer Science",
    "difficulty": "beginner",
    "date_from": "2024-01-01",
    "date_to": "2024-12-31"
  },
  "score_threshold": 0.7
}
```

**Output** (Streamed):
```json
{
  "results": [
    {
      "id": "doc_002",
      "score": 0.88,
      "title": "Student Assignment 1",
      "content": "Complete the following exercises...",
      "metadata": {
        "subject": "Computer Science",
        "difficulty": "beginner",
        "type": "assignment"
      }
    },
    ...
  ],
  "total": 5,
  "filtered_by_role": "student",
  "applied_filters": { ... }
}
```

**Streaming**: Yes

**Role Filtering**: Same as Vector Search + metadata filters

---

## 📡 MCP Streaming Protocol

### Why Streaming?

- **Large Result Sets**: Educational content can return hundreds of documents
- **Better UX**: Users see results as they arrive
- **Resource Efficiency**: Lower memory usage, progressive rendering
- **Network Optimization**: Reduces perceived latency

### Implementation

MCP Streaming uses **Server-Sent Events (SSE)** or **WebSocket** for real-time data delivery:

```python
# MCP Server streaming implementation
async def stream_search_results(query: str, role: str):
    """Stream search results progressively"""
    
    # Send initial metadata
    yield {
        "type": "metadata",
        "query": query,
        "role": role,
        "timestamp": datetime.now()
    }
    
    # Stream results as they're retrieved from Qdrant
    async for result in qdrant_search_stream(query, role):
        yield {
            "type": "result",
            "data": result
        }
    
    # Send completion signal
    yield {
        "type": "complete",
        "total_results": count
    }
```

**MCP Protocol Format**:
```
data: {"type": "metadata", "query": "..."}

data: {"type": "result", "data": {...}}

data: {"type": "result", "data": {...}}

data: {"type": "complete", "total_results": 10}
```

---

## 🚀 Deployment Architecture

### Raspberry Pi Production Setup

```
Raspberry Pi (Remote Server)
├── OS: Raspberry Pi OS (64-bit)
├── Docker Engine
│   ├── Container: caddy (ports 80, 443)
│   ├── Container: oauth-server (port 8001)
│   ├── Container: mcp-server (port 8000)
│   └── Container: qdrant (port 6333)
├── Persistent Volumes:
│   ├── /data/qdrant_storage → Qdrant data
│   ├── /data/incoming → SCP upload target
│   ├── /data/processed → Processed files
│   └── /data/oauth_db → User database
└── Systemd Services:
    └── docker-compose (auto-start on boot)
```

### Network Configuration

```
Internet
   ↓
Router (Port Forwarding: 80 → Pi:80, 443 → Pi:443)
   ↓
Raspberry Pi (Static IP: 192.168.1.100)
   ↓
Caddy (Public Domain: your-domain.com)
```

---

## 📁 Complete Project Structure

```
MCP_diploma_thesis_final/
│
├── README.md                          # Project overview
├── ARCHITECTURE.md                    # This document
├── DEPLOYMENT.md                      # Deployment guide
├── DEVELOPMENT.md                     # Development setup
├── API_DOCUMENTATION.md               # API/Tool reference
│
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment template
├── .gitignore                         # Git ignore
├── docker-compose.yml                 # Orchestration
├── Caddyfile                          # Reverse proxy config
│
├── src/
│   ├── __init__.py
│   │
│   ├── main.py                        # MCP Server entry point
│   ├── oauth_server.py                # OAuth server entry point
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                # Configuration management
│   │   └── logging_config.py          # Logging setup
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── oauth_handler.py           # OAuth flow logic
│   │   ├── jwt_manager.py             # JWT creation/validation
│   │   ├── user_manager.py            # User CRUD operations
│   │   └── models.py                  # User/Role data models
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── qdrant_client.py           # Qdrant connection
│   │   ├── data_loader.py             # Auto data insertion
│   │   ├── embeddings.py              # Text embedding generation
│   │   └── user_db.py                 # OAuth user database
│   │
│   ├── rbac/
│   │   ├── __init__.py
│   │   ├── access_control.py          # Role-based filtering
│   │   ├── decorators.py              # @require_role decorators
│   │   └── permissions.py             # Permission definitions
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py                    # Base tool class
│   │   ├── ping.py                    # Health check tool
│   │   ├── vector_search.py           # Standard search
│   │   └── advanced_search.py         # Advanced filtered search
│   │
│   ├── streaming/
│   │   ├── __init__.py
│   │   ├── mcp_streamer.py            # MCP streaming implementation
│   │   └── sse_handler.py             # Server-Sent Events
│   │
│   ├── server/
│   │   ├── __init__.py
│   │   ├── mcp_server.py              # MCP server implementation
│   │   ├── http_server.py             # HTTP/REST endpoints
│   │   └── middleware.py              # Request/response middleware
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py                  # Logging utilities
│       ├── validators.py              # Input validation
│       ├── exceptions.py              # Custom exceptions
│       └── helpers.py                 # Common utilities
│
├── data/
│   ├── incoming/                      # SCP target for new files
│   ├── processed/                     # Successfully loaded files
│   ├── failed/                        # Failed validation files
│   └── backups/                       # Periodic backups
│
├── scripts/
│   ├── watch_and_load.py              # File watcher service
│   ├── setup_users.py                 # Initialize OAuth users
│   ├── backup_qdrant.sh               # Backup script
│   └── deploy.sh                      # Deployment script
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Pytest configuration
│   ├── test_auth.py                   # OAuth tests
│   ├── test_rbac.py                   # Role filtering tests
│   ├── test_tools.py                  # MCP tool tests
│   ├── test_streaming.py              # Streaming tests
│   ├── test_data_loader.py            # Data pipeline tests
│   └── test_integration.py            # End-to-end tests
│
└── docs/
    ├── images/                        # Architecture diagrams
    ├── examples/                      # Example JSON files
    ├── ARCHITECTURE.md                # System architecture
    ├── DEPLOYMENT.md                  # Deployment guide
    ├── API_DOCUMENTATION.md           # API reference
    ├── SECURITY.md                    # Security considerations
    └── THESIS_NOTES.md                # Thesis-specific notes
```

---

## 🔒 Security Considerations

### 1. Authentication
- ✅ JWT tokens with expiration (1 hour)
- ✅ Refresh tokens (7 days)
- ✅ Password hashing with bcrypt (12 rounds)
- ✅ HTTPS only (TLS 1.3)

### 2. Authorization
- ✅ Role-based access control (RBAC)
- ✅ Server-side filtering (never trust client)
- ✅ Audit logging of access attempts

### 3. Data Protection
- ✅ Teacher content never exposed to students
- ✅ Qdrant access restricted to MCP server
- ✅ Environment variables for secrets
- ✅ No credentials in code or logs

### 4. Network Security
- ✅ Caddy rate limiting (100 req/min per IP)
- ✅ CORS configuration
- ✅ Input validation and sanitization

---

## 📈 Performance Requirements

### Expected Load
- **Concurrent Users**: 50-100 students + 10-20 teachers
- **Query Response Time**: < 500ms (95th percentile)
- **Streaming Latency**: < 100ms first result
- **Data Upload Processing**: < 5 minutes for 10K documents

### Optimization Strategies
- Connection pooling to Qdrant
- In-memory caching of common queries (Redis)
- Efficient embedding model (384-dim vectors)
- Batch processing for data uploads

---

## 🎓 Diploma Thesis Focus Areas

### Key Contributions
1. **Novel RBAC for MCP**: First implementation of role-based filtering in MCP
2. **Educational Use Case**: Practical application for schools/universities
3. **Streaming Protocol**: Efficient handling of large datasets
4. **Automated Pipeline**: SCP → Qdrant integration

### Thesis Chapters Alignment
1. **Introduction**: Problem statement (secure educational content delivery)
2. **Related Work**: OAuth, RBAC, Vector databases, MCP protocol
3. **System Design**: This architecture
4. **Implementation**: Code with professional documentation
5. **Evaluation**: Performance tests, security audit, user study
6. **Conclusion**: Future work (AI tutors, multi-language support)

---

## 📝 Next Steps

### Phase 1: Foundation (Week 1)
- [ ] Setup project structure
- [ ] Configure Docker environment
- [ ] Initialize Qdrant database
- [ ] Create base MCP server

### Phase 2: OAuth Implementation (Week 2)
- [ ] Build custom OAuth server
- [ ] Implement user database
- [ ] Create JWT management
- [ ] Integrate with Caddy

### Phase 3: RBAC & Tools (Week 3)
- [ ] Implement role-based filtering
- [ ] Build 3 MCP tools
- [ ] Add streaming support
- [ ] Write comprehensive tests

### Phase 4: Data Pipeline (Week 4)
- [ ] File watcher implementation
- [ ] JSON parser with role extraction
- [ ] Automatic Qdrant insertion
- [ ] Error handling and logging

### Phase 5: Deployment & Testing (Week 5)
- [ ] Deploy to Raspberry Pi
- [ ] End-to-end testing
- [ ] Security audit
- [ ] Performance benchmarking
- [ ] Documentation finalization

---

## 📞 Support & Maintenance

### Monitoring
- Health check endpoint: `/health`
- Metrics endpoint: `/metrics`
- Log aggregation: Docker logs

### Backup Strategy
- Daily Qdrant snapshots
- Weekly full backups
- User database backups before updates

---

**End of Architecture Document**

For implementation details, see:
- `DEPLOYMENT.md` - Deployment instructions
- `API_DOCUMENTATION.md` - API reference
- `DEVELOPMENT.md` - Development setup
