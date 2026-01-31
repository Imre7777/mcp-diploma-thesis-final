# LeoWiki MCP Server - Complete API Documentation

**Version:** 2.0.0 (Professional Refactoring)  
**Date:** January 31, 2026  
**Architecture:** FastMCP with Scalekit OAuth 2.1

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [MCP Tools](#mcp-tools)
4. [MCP Resources](#mcp-resources)
5. [MCP Prompts](#mcp-prompts)
6. [Error Handling](#error-handling)
7. [Examples](#examples)

---

## Overview

The LeoWiki MCP Server provides semantic search over educational content with sophisticated role-based access control. The server follows FastMCP best practices and implements a two-tool architecture for security by design.

**Key Principles:**
- **Security by Design**: Separate tools for different roles (no parameter manipulation)
- **User Experience First**: Natural language responses, no technical jargon
- **DSGVO Compliant**: Audit logging, pseudonymization, access control
- **Professional Grade**: Progress reporting, middleware, dependency injection

---

## Authentication

### OAuth 2.1 Flow

The server implements OAuth 2.1 Protected Resource pattern via Scalekit.

**Endpoints:**
- `GET /.well-known/oauth-protected-resource` - OAuth discovery metadata
- `GET /auth/login` - Initiate OAuth flow
- `GET /callback` - OAuth callback handler
- `GET /auth/logout` - End session

**Token Format:**
```
Authorization: Bearer <access_token>
```

**JWT Claims:**
- `sub`: User ID
- `email`: User email
- `role`: User role (student, teacher, admin)
- `scope`: OAuth scopes
- `iss`: Scalekit issuer URL
- `aud`: Expected audience

### Access Control

**Three Roles:**

1. **Student** - Limited access
   - Can use: `search_content_student`
   - Sees: Student-level educational content only
   
2. **Teacher** - Extended access
   - Can use: `search_content_teacher`, `get_collection_stats`
   - Sees: Student + teacher content (exam materials, solutions, internal docs)
   
3. **Admin** - Full access
   - Can use: All tools
   - Sees: All content at all levels

---

## MCP Tools

### 1. search_content_student

**Purpose:** Search educational content with student-level access.

**Access:** All authenticated users

**Annotations:**
- `readOnlyHint`: true (no side effects)
- `idempotentHint`: true (deterministic results)
- `openWorldHint`: false (bounded dataset)

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query in German or English |
| `limit` | integer | No | 10 | Max results (1-20) |

**Returns:**

```json
{
  "content": [{
    "type": "text",
    "text": "<formatted search results>"
  }]
}
```

**Example Request:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "search_content_student",
    "arguments": {
      "query": "Was ist objektorientierte Programmierung?",
      "limit": 5
    }
  }
}
```

**Example Response:**
```
**Objektorientierte Programmierung (OOP)**

OOP ist ein Programmierparadigma, das auf dem Konzept von "Objekten" basiert...

(Quelle: SEW Unterrichtsmaterialien)

---

**Klassen und Objekte**

In der OOP werden Daten und Funktionen zu Objekten zusammengefasst...

(Quelle: Java Tutorial)
```

**Progress Updates:**
1. "Analysiere Suchanfrage..."
2. "Generiere Embedding..."
3. "Wende Zugriffs-Filter an..."
4. "Durchsuche Wissensdatenbank..."
5. "Formatiere Ergebnisse..."

**Filters Applied:**
- Access level: `student` only
- Content visible to students

---

### 2. search_content_teacher

**Purpose:** Search educational content with teacher-level access (full access).

**Access:** Teachers and Admins only

**Annotations:**
- `readOnlyHint`: true
- `idempotentHint`: true
- `openWorldHint`: false

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query in German or English |
| `limit` | integer | No | 10 | Max results (1-20) |

**Returns:** Same format as `search_content_student`

**Differences from Student Tool:**
- Access to teacher-internal documents
- Exam materials and solutions
- Administrative guidelines
- All namespaces

**Example Query:**
```
"No-Blame-Approach Anleitung für Klassenvorstände"
```

**Filters Applied:**
- Access level: `student` AND `teacher`
- All content visible to teachers

---

### 3. get_collection_stats

**Purpose:** Get detailed database statistics.

**Access:** Teachers and Admins only (enforced by RBACEnforcementMiddleware)

**Annotations:**
- `readOnlyHint`: true

**Parameters:** None (uses context)

**Returns:**

```json
{
  "content": [{
    "type": "text",
    "text": "**Collection Statistics**\n\nCollection: educational_content\nTotal Documents: 757\n..."
  }]
}
```

**Information Provided:**
- Total document count
- Vector dimensions
- Distance metric
- Access level distribution
- Collection health
- Optimizer status

---

### 4. health_check

**Purpose:** Basic server health check.

**Access:** All users (public)

**Parameters:** None

**Returns:**
```json
{
  "content": [{
    "type": "text",
    "text": "Server: MCP Educational Server v1.0.0\nStatus: Healthy ✓"
  }]
}
```

---

## MCP Resources

Resources expose read-only data to help LLMs understand the server.

### Static Resources

#### leowiki://categories

**Description:** List of available content categories

**Returns:** JSON array with category information

```json
[
  {
    "id": "sew",
    "name": "Software Engineering",
    "name_de": "Softwareentwicklung",
    "description": "Programming, OOP, Design Patterns...",
    "icon": "💻"
  },
  ...
]
```

**Use Case:** Help LLM understand content organization and suggest relevant categories.

---

#### leowiki://access-levels

**Description:** RBAC documentation explaining roles and permissions

**Returns:** JSON object with role definitions

```json
{
  "student": {
    "name": "Student",
    "description": "Access to student-level content",
    "can_access": ["student"],
    "example_content": [...]
  },
  ...
}
```

**Use Case:** Help LLM explain access restrictions to users.

---

#### leowiki://search-hints

**Description:** Search tips and best practices

**Returns:** Markdown document with search guidance

**Use Case:** Help users formulate better queries.

---

### Dynamic Resources

#### leowiki://stats

**Description:** Live collection statistics

**Returns:** JSON with real-time database metrics

```json
{
  "collection": "educational_content",
  "total_documents": 757,
  "vector_dimensions": 3072,
  "status": "healthy",
  "last_checked": "2026-01-31T10:30:00Z"
}
```

**Use Case:** Monitor system health, inform users about available content.

---

#### leowiki://topic/{topic_id}

**Description:** Detailed information about a specific topic (template resource)

**Example URIs:**
- `leowiki://topic/sew-java-oop`
- `leowiki://topic/nwt-subnetting-basics`

**Returns:** JSON with topic details (respects RBAC)

**Use Case:** Deep dive into specific topics.

---

#### leowiki://recent/{count}

**Description:** Recently updated content (template resource)

**Example URIs:**
- `leowiki://recent/5` - Last 5 updates
- `leowiki://recent/10` - Last 10 updates

**Returns:** JSON array with recent items (max 20, filtered by role)

**Use Case:** Help users discover new content.

---

## MCP Prompts

Prompts are reusable templates for common educational workflows.

### 1. explain_topic

**Purpose:** Generate structured topic explanation

**Parameters:**
- `topic` (string): Topic to explain
- `difficulty` (string): beginner, intermediate, advanced
- `include_examples` (boolean): Include practical examples

**Generated Prompt Structure:**
1. Definition
2. Core concepts
3. Practical relevance
4. Examples (if requested)
5. Common mistakes
6. Summary

**Example:**
```
Prompt: explain_topic(topic="Polymorphismus", difficulty="intermediate")

Output: "Erkläre das Thema 'Polymorphismus' für einen Schüler auf Fortgeschrittenen-Niveau..."
```

---

### 2. create_quiz

**Purpose:** Generate quiz questions for assessment

**Parameters:**
- `topic` (string): Quiz subject
- `num_questions` (integer): 1-10 questions
- `question_type` (string): multiple_choice, true_false, short_answer, mixed
- `difficulty` (string): beginner, intermediate, advanced

**Output Format:** JSON schema for quiz structure

---

### 3. compare_concepts

**Purpose:** Compare related concepts side-by-side

**Parameters:**
- `concepts` (string): Comma-separated concepts (e.g., "Vererbung, Komposition")
- `aspects` (string): Comparison aspects (e.g., "definition,usage,advantages")

**Use Case:** Help students understand differences and make informed choices.

---

### 4. summarize_search

**Purpose:** Synthesize multiple search results into coherent answer

**Parameters:**
- `query` (string): Original search query

**Special:** Reads `leowiki://categories` resource for context

**Use Case:** Transform technical search results into natural language answers.

---

### 5. learning_path

**Purpose:** Generate personalized learning roadmap

**Parameters:**
- `goal` (string): Learning objective
- `current_level` (string): Current knowledge level
- `time_available` (string): Available timeframe

**Returns:** Multi-message conversation starter

**Use Case:** Guide students through structured learning journeys.

---

## Error Handling

### Error Response Format

```json
{
  "content": [{
    "type": "text",
    "text": "<user-friendly error message>"
  }],
  "isError": true
}
```

### Error Types

1. **Validation Error** - Invalid input (empty query, out of range limit)
   - Response: Friendly German message explaining the issue
   
2. **Authorization Error** - Insufficient permissions (RBAC)
   - Response: "Access denied. This operation requires: teacher, admin"
   
3. **Search Error** - Database or embedding service failure
   - Response: "Es ist ein Fehler bei der Suche aufgetreten..."
   
4. **Not Found** - No results
   - Response: "Ich konnte leider keine Informationen finden..."

### Error Masking

`mask_error_details=True` in production:
- Internal errors hidden from clients
- Stack traces only in logs
- User-friendly error messages

---

## Examples

### Example 1: Student Searches for Course Material

**Request:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "search_content_student",
    "arguments": {
      "query": "Java ArrayList Methoden",
      "limit": 3
    }
  }
}
```

**Response:**
```
**Java ArrayList - Wichtige Methoden**

Die ArrayList-Klasse bietet folgende wichtige Methoden:
- add(element): Fügt Element hinzu
- get(index): Gibt Element an Position zurück
- remove(index): Entfernt Element
- size(): Gibt Anzahl Elemente zurück

(Quelle: SEW Java Tutorial)

---

**ArrayList vs Array**

ArrayLists sind dynamisch und können wachsen, während Arrays eine feste Größe haben...

(Quelle: Java Collections Framework)
```

**Note:** No technical details (scores, database info) visible to user.

---

### Example 2: Teacher Searches for Exam Material

**Request:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "search_content_teacher",
    "arguments": {
      "query": "Prüfungsfragen OOP mit Lösungen",
      "limit": 5
    }
  }
}
```

**Response:** Includes teacher-only content (exam solutions, internal guidelines).

---

### Example 3: Using Resources

**Read Categories:**
```json
{
  "method": "resources/read",
  "params": {
    "uri": "leowiki://categories"
  }
}
```

**Response:** JSON array of all categories.

---

### Example 4: Using Prompts

**Get Learning Path Prompt:**
```json
{
  "method": "prompts/get",
  "params": {
    "name": "learning_path",
    "arguments": {
      "goal": "Java Backend Development",
      "current_level": "beginner",
      "time_available": "2 months"
    }
  }
}
```

**Response:** Multi-message prompt to start learning conversation.

---

## Progress Reporting

Both search tools report progress via Server-Sent Events (SSE):

```
event: progress
data: {"progress": 0, "total": 4, "message": "Analysiere Suchanfrage..."}

event: progress
data: {"progress": 1, "total": 4, "message": "Generiere Embedding..."}

event: progress
data: {"progress": 2, "total": 4, "message": "Wende Zugriffs-Filter an..."}

event: progress
data: {"progress": 3, "total": 4, "message": "Durchsuche Wissensdatenbank..."}

event: progress
data: {"progress": 4, "total": 4, "message": "Formatiere Ergebnisse..."}

event: result
data: {"content": [...]}
```

---

## Best Practices

### For LLMs Using This Server

**1. Presentation Guidelines:**
- Present results naturally and directly
- NEVER mention technical details (scores, result counts, database info)
- Focus on CONTENT, not mechanics

**2. Style:**
- Short, precise answers
- Friendly but professional tone
- Adapt to audience (student vs. teacher)

**3. Sources:**
- Only at the end, in parentheses
- Format: "(Quelle: [Document Type])"
- NOT: Long URLs or technical paths

**4. Error Handling:**
- Friendly explanations when no results
- NOT: "Der Server hat 0 Ergebnisse zurückgegeben"
- BUT: "Ich konnte leider keine Informationen dazu finden"

### For Developers

**1. Tool Selection:**
- Use `search_content_student` for student users
- Use `search_content_teacher` for teachers
- NEVER try to manipulate access via parameters

**2. Resource Usage:**
- Read `leowiki://categories` before suggesting searches
- Check `leowiki://stats` for system health
- Use `leowiki://search-hints` to help users

**3. Prompt Usage:**
- Use `explain_topic` for structured explanations
- Use `create_quiz` for assessment generation
- Use `learning_path` for study planning

---

## API Endpoints (HTTP)

### Public Endpoints (No Auth)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/.well-known/oauth-protected-resource` | GET | OAuth discovery |
| `/auth/login` | GET | OAuth login |
| `/callback` | GET | OAuth callback |
| `/docs` | GET | Swagger UI |

### Protected Endpoints (Require Auth)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/mcp` | POST | MCP protocol (tools, resources, prompts) |
| `/auth/logout` | GET | Logout |
| `/auth/user` | GET | Current user info |

---

## Rate Limiting

- **Standard Users**: 100 requests/hour
- **Teachers**: 500 requests/hour (configurable)
- **Admins**: Unlimited

Enforced per IP address for authenticated requests.

---

## Monitoring & Logging

### Log Levels

- **DEBUG**: Detailed execution traces
- **INFO**: Request lifecycle, user actions
- **WARNING**: Validation failures, access denials
- **ERROR**: Exceptions, system failures

### Audit Logging

All tool invocations are logged with:
- Request ID (correlation)
- User ID (pseudonymized hash)
- User role
- Tool name
- Timestamp
- Success/failure

**Format:**
```
[AUDIT] Tool invocation successful - request_id=a3b4c5d6, tool=search_content_student, user=1234567890, role=student
```

**Retention:** 90 days (DSGVO compliant)

---

## Performance

| Metric | Target | Typical |
|--------|--------|---------|
| **Response Time (p50)** | < 500ms | ~340ms |
| **Response Time (p95)** | < 1000ms | ~450ms |
| **Embedding Generation** | < 100ms | ~80ms |
| **Vector Search** | < 300ms | ~200ms |
| **Progress Reporting** | Real-time | SSE |

---

## Security

### Input Validation

- Query length: max 500 characters
- Limit: 1-20 range enforced
- Character whitelist for German text
- SQL injection pattern detection

### RBAC Enforcement

**Two-Level RBAC:**

1. **Tool Level** - Separate tools per role (this document)
2. **Middleware Level** - RBACEnforcementMiddleware blocks admin tools

### Audit Trail

- All searches logged
- User actions pseudonymized
- 90-day retention
- DSGVO compliant

---

## Troubleshooting

### No Results Found

**Possible Causes:**
1. Content not yet indexed
2. Too specific query
3. Wrong language (try German terms)
4. Access level restrictions

**Solutions:**
- Use broader terms
- Check `leowiki://search-hints` resource
- Try synonyms
- Verify access level

### Access Denied

**Cause:** Tool requires higher privilege

**Solution:** Use appropriate tool for your role:
- Students → `search_content_student`
- Teachers → `search_content_teacher`

### Slow Performance

**Check:**
1. Qdrant health via `/health` endpoint
2. OpenAI API status
3. Network connectivity

---

## Version History

### v2.0.0 (2026-01-31) - Professional Refactoring

**Added:**
- Two-tool RBAC architecture (security by design)
- 6 MCP resources
- 5 educational prompts
- 4 custom middleware components
- Lifespan-based dependency injection
- Progress reporting
- Tool annotations
- CLAUDE presentation instructions

**Changed:**
- Single `search_content` → Two separate tools
- Manual initialization → Lifespan pattern
- Basic logging → Structured logging with correlation IDs

**Security:**
- Enhanced RBAC enforcement
- Audit logging for DSGVO compliance
- Error detail masking

### v1.0.0 (2026-01-26) - Initial Release

**Added:**
- Basic semantic search
- OAuth 2.1 integration
- Qdrant database
- RBAC filtering

---

## Support

**Technical Issues:**
- GitHub Issues: [Project Repository]
- Email: leowiki-support@htl-leonding.ac.at

**Documentation:**
- README.md - Overview and quick start
- API.md - This document
- refactor/*.md - Design decisions and best practices

---

## References

**Standards:**
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [OAuth 2.1](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-07)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)

**Implementation Guides:**
- `refactor/FastMCP_SDK_Reference3.md` - FastMCP features
- `refactor/LeoWiki_MCP_Enhancement_Plan.md` - Enhancement plan
- `refactor/leowiki_rbac_tools_implementation.md` - Two-tool RBAC
- `refactor/MCP_Server_Best_Practices_Diplomarbeit.md` - Best practices

---

**Last Updated:** 2026-01-31  
**Document Version:** 2.0.0  
**Status:** Production Ready
