# Scalekit MCP Server Setup Guide

This guide documents the Scalekit configuration for the MCP Educational Server.

## 📋 Scalekit Dashboard Configuration

### 1. MCP Server Created

**Server Details:**
- **Name:** MCP Educational Server  
- **Resource ID:** `res_10661405199119278`
- **Environment URL:** `https://mcpeduauth.scalekit.dev`
- **Authorization Server:** `https://mcpeduauth.scalekit.dev/resources/res_10661405199119278`

**Settings:**
- ✅ Allow dynamic client registration
- ✅ Allow Client ID Metadata Document (CIMD)

### 2. Environment Credentials

```bash
SCALEKIT_ENVIRONMENT_URL=https://mcpeduauth.scalekit.dev
SCALEKIT_CLIENT_ID=skc_35934031996379566
SCALEKIT_CLIENT_SECRET=test_sk_Tl4Uv0wfF9XHVLVm1w8t0SrDK7CWr8
SCALEKIT_ENVIRONMENT_ID=env_35934029899511342
```

### 3. MCP-Specific Configuration

```bash
SCALEKIT_MCP_RESOURCE_ID=res_10661405199119278
SCALEKIT_AUTH_SERVER=https://mcpeduauth.scalekit.dev/resources/res_10661405199119278
```

---

## 🔐 OAuth 2.0 Protected Resource Metadata

Our server implements the OAuth 2.0 Protected Resource Metadata specification required by Scalekit for MCP client discovery.

### Endpoint

```
GET /.well-known/oauth-protected-resource/res_10661405199119278
```

### Response

```json
{
  "resource": "http://localhost:8000",
  "authorization_servers": [
    "https://mcpeduauth.scalekit.dev/resources/res_10661405199119278"
  ],
  "bearer_methods_supported": ["header"],
  "resource_documentation": "http://localhost:8000/docs",
  "scopes_supported": []
}
```

**Note:** We use role-based access control (RBAC) instead of OAuth scopes.

---

## 🔑 JWT Token Validation

### Token Validation Flow

1. **Extract Token:** From `Authorization: Bearer <token>` header
2. **Validate with Scalekit:**
   - Verify signature using Scalekit client
   - Check expiration
   - Validate audience (our MCP server URL)
3. **Extract Claims:**
   - `sub`: User ID
   - `email`: User email
   - `roles`: User roles (student, teacher, admin)
   - `org_id`: Organization ID
4. **Map to Internal Role:**
   - Multiple roles → Use highest privilege
   - No role → Default to `student`

### Scalekit SDK Usage

```python
from scalekit import ScalekitClient
from scalekit.common.scalekit import TokenValidationOptions

# Initialize client
scalekit_client = ScalekitClient(
    env_url="https://mcpeduauth.scalekit.dev",
    client_id="skc_35934031996379566",
    client_secret="test_sk_Tl4Uv0wfF9XHVLVm1w8t0SrDK7CWr8",
)

# Validate token
options = TokenValidationOptions(
    issuer=scalekit_client.env_url,
    audience="http://localhost:8000",
)

is_valid = scalekit_client.validate_access_token(token, options=options)

# Get claims
claims = scalekit_client.validate_token_and_get_claims(token, options=options)
```

---

## 👥 Role-Based Access Control (RBAC)

### Roles (No Public!)

| Role | Access Level | Can See |
|------|-------------|---------|
| **student** | 1 | student content only |
| **teacher** | 2 | student + teacher content |
| **admin** | 3 | all content (student + teacher + admin) |

### Role Hierarchy

```
┌─────────────────────────────────────────────┐
│              AUTHENTICATED                   │
│  ┌─────────────────────────────────────┐   │
│  │           ADMIN                      │   │
│  │  Sees: student + teacher + admin     │   │
│  │  ┌──────────────────────────────┐   │   │
│  │  │       TEACHER                │   │   │
│  │  │  Sees: student + teacher     │   │   │
│  │  │  ┌────────────────────────┐  │   │   │
│  │  │  │     STUDENT             │  │   │   │
│  │  │  │  Sees: student only     │  │   │   │
│  │  │  └────────────────────────┘  │   │   │
│  │  └──────────────────────────────┘   │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### Content Filtering

Content in Qdrant has `access_level` metadata:
- `"student"`: Visible to all authenticated users
- `"teacher"`: Visible to teachers and admins only
- `"admin"`: Visible to admins only

Search queries automatically filter by user role:

```python
# Student query
filters = {"access_level": ["student"]}

# Teacher query  
filters = {"access_level": ["student", "teacher"]}

# Admin query
filters = {"access_level": ["student", "teacher", "admin"]}
```

---

## 🛡️ Authentication Middleware

### Public Endpoints (No Auth Required)

- `/health` - Health check for monitoring
- `/auth/login` - OAuth login initiation
- `/auth/callback` - OAuth callback
- `/auth/logout` - Logout
- `/.well-known/*` - OAuth metadata discovery

### Protected Endpoints (Auth Required)

- `/mcp` - MCP tool calls
- `/sse` - Server-Sent Events
- `/docs` - API documentation (protected in production, public in DEBUG mode)

### Middleware Flow

```
1. Request arrives
   ↓
2. Check if endpoint is public
   ↓ (if not public)
3. Extract Bearer token from Authorization header
   ↓
4. Validate token with Scalekit
   ↓
5. Extract user info and role
   ↓
6. Attach to request.state.user
   ↓
7. Continue to endpoint handler
```

---

## 🧪 Testing

### Step 1: Start Server

```bash
cd C:\Users\imreo\Documents\MCP_diploma_thesis_final
.\venv\Scripts\python.exe main.py
```

### Step 2: Check Health (Public)

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "server": "mcp-educational-server",
  "initialized": true,
  "rbac_enabled": true,
  "authentication": "required"
}
```

### Step 3: Check OAuth Metadata (Public)

```bash
curl http://localhost:8000/.well-known/oauth-protected-resource/res_10661405199119278
```

Expected response:
```json
{
  "resource": "http://localhost:8000",
  "authorization_servers": [
    "https://mcpeduauth.scalekit.dev/resources/res_10661405199119278"
  ],
  "bearer_methods_supported": ["header"],
  "resource_documentation": "http://localhost:8000/docs",
  "scopes_supported": []
}
```

### Step 4: Try Protected Endpoint (Should Fail)

```bash
curl http://localhost:8000/docs
```

Expected response:
```json
{
  "detail": "Authentication required. Please log in."
}
```

### Step 5: Test with Valid Token (Next Step)

Once we have OAuth flow working:

```bash
curl -H "Authorization: Bearer <valid-token>" http://localhost:8000/docs
```

---

## 📚 References

- [Scalekit Documentation](https://docs.scalekit.com/)
- [Scalekit MCP Servers](https://docs.scalekit.com/mcp-servers)
- [OAuth 2.0 Protected Resource Metadata (RFC 8414)](https://datatracker.ietf.org/doc/html/rfc8414)
- [MCP HTTP Streamable Specification](https://modelcontextprotocol.io/docs/transports/http-streamable)

---

## 🚀 Next Steps

1. ✅ Scalekit MCP Server created
2. ✅ Environment credentials configured
3. ✅ OAuth metadata endpoint implemented
4. ✅ JWT validation middleware implemented
5. ⏳ OAuth login/callback flow (Day 3-4)
6. ⏳ Test with real JWT tokens (Day 5)
