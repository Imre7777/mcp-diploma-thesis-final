# Environment Setup for Official Scalekit Architecture

## Quick Setup Guide

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root with the following configuration:

```env
# ============================================================================
# Server Configuration
# ============================================================================
SERVER_NAME="MCP Educational Server"
SERVER_VERSION="1.0.0"
SERVER_PORT=8000
LOG_LEVEL=INFO

# ============================================================================
# Scalekit OAuth 2.1 Configuration
# ============================================================================
ENABLE_AUTH=true

# From Scalekit Dashboard (https://app.scalekit.com)
SCALEKIT_ENV_URL=https://your-org.scalekit.com
SCALEKIT_CLIENT_ID=skc_xxxxx
SCALEKIT_CLIENT_SECRET=sks_xxxxx
SCALEKIT_MCP_SERVER_ID=mcp_edu_server

# IMPORTANT: Must match URL in Scalekit dashboard
SCALEKIT_EXPECTED_AUDIENCE=http://localhost:8000/

# Copy JSON from Scalekit MCP Server dashboard (minified, no whitespace)
SCALEKIT_PROTECTED_RESOURCE_METADATA='{"resource":"mcp_edu_server","authorization_servers":["https://..."],"bearer_methods_supported":["header"],"scopes_supported":["mcp:read","mcp:write"]}'

# ============================================================================
# Qdrant Vector Database
# ============================================================================
VECTOR_DB_URL=http://localhost:6334
DEFAULT_COLLECTION=educational_content

# ============================================================================
# OpenAI (for query embeddings)
# ============================================================================
OPENAI_API_KEY=sk-xxxxx
EMBEDDING_MODEL=text-embedding-3-large

# ============================================================================
# RBAC
# ============================================================================
ENABLE_RBAC=true
DEFAULT_USER_ROLE=student
```

### 3. Start Qdrant

```bash
docker run -d --name qdrant-mcp-edu -p 6334:6333 qdrant/qdrant:latest
```

### 4. Run the Server

```bash
python main.py
```

## Scalekit Configuration Steps

### Step 1: Create MCP Server in Scalekit

1. Go to [Scalekit Dashboard](https://app.scalekit.com)
2. Navigate to **MCP Servers** section
3. Click **Create MCP Server**
4. Configure:
   - **Name**: MCP Educational Server
   - **Resource ID**: `mcp_edu_server`
   - **Server URL**: `http://localhost:8000/`
   - **Scopes**: `mcp:read`, `mcp:write`, `usr:read`, `usr:write`

### Step 2: Copy Configuration

1. Copy **Environment URL**: `SCALEKIT_ENV_URL`
2. Copy **Client ID**: `SCALEKIT_CLIENT_ID`
3. Copy **Client Secret**: `SCALEKIT_CLIENT_SECRET`
4. Copy **MCP Server ID**: `SCALEKIT_MCP_SERVER_ID`
5. Copy **Protected Resource Metadata JSON**: `SCALEKIT_PROTECTED_RESOURCE_METADATA`
   - **IMPORTANT**: Minify the JSON (remove all whitespace/newlines)
   - Example tool: https://jsonformatter.org/json-minify

### Step 3: Set Expected Audience

The `SCALEKIT_EXPECTED_AUDIENCE` must **exactly match** the Server URL you configured in Scalekit:
- If Scalekit URL is `http://localhost:8000/` → use `http://localhost:8000/`
- If Scalekit URL is `http://localhost:8000` → use `http://localhost:8000`
- Include/exclude trailing slash to match exactly!

### Step 4: Test Configuration

```bash
# Test OAuth discovery endpoint
curl http://localhost:8000/.well-known/oauth-protected-resource

# Test health endpoint
curl http://localhost:8000/health
```

## Testing with Claude Desktop

### Configure Claude Desktop

Edit Claude Desktop config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add:
```json
{
  "mcpServers": {
    "edu-server": {
      "url": "http://localhost:8000/",
      "oauth": {
        "enabled": true,
        "discoveryUrl": "http://localhost:8000/.well-known/oauth-protected-resource"
      }
    }
  }
}
```

### Test Flow

1. Restart Claude Desktop
2. Claude will detect the MCP server
3. Click "Connect" → redirected to Scalekit for OAuth login
4. After login, Claude receives Bearer token
5. Claude sends requests to MCP server with Bearer token
6. Server validates token with Scalekit SDK
7. Server returns search results based on user's role

## Troubleshooting

### "Scalekit client initialization failed"
- Check `SCALEKIT_ENV_URL`, `SCALEKIT_CLIENT_ID`, `SCALEKIT_CLIENT_SECRET`
- Verify values match Scalekit dashboard exactly

### "Token validation failed"
- Check `SCALEKIT_EXPECTED_AUDIENCE` matches Scalekit Server URL exactly
- Include/exclude trailing slash to match
- Verify token is valid and not expired

### "PROTECTED_RESOURCE_METADATA config missing"
- Copy JSON from Scalekit MCP Server dashboard
- **Minify** the JSON (remove all whitespace)
- Wrap in single quotes in `.env` file

### "Qdrant connection failed"
- Start Qdrant: `docker start qdrant-mcp-edu` or create new container
- Check port: should be 6334 (not 6333)
- Verify `VECTOR_DB_URL=http://localhost:6334`

## Development vs. Production

### Development (Local Testing)
```env
ENABLE_AUTH=false  # Disable auth for testing
SCALEKIT_EXPECTED_AUDIENCE=http://localhost:8000/
```

### Production (Raspberry Pi)
```env
ENABLE_AUTH=true  # Always enable auth in production
SCALEKIT_EXPECTED_AUDIENCE=https://your-domain.com/
VECTOR_DB_URL=http://qdrant:6333  # Docker internal network
```

## Next Steps

1. ✅ Configure environment variables
2. ✅ Start Qdrant container
3. ✅ Run server: `python main.py`
4. ✅ Test OAuth discovery: `curl http://localhost:8000/.well-known/oauth-protected-resource`
5. ✅ Configure Claude Desktop
6. ✅ Test full OAuth flow with Claude Desktop
7. ✅ Deploy to Raspberry Pi

## Resources

- [Scalekit MCP Quickstart](https://docs.scalekit.com/authenticate/mcp/quickstart/)
- [Official Demo Repository](https://github.com/scalekit-inc/mcp-auth-demos)
- [FastMCP Documentation](https://pypi.org/project/fastmcp/)
- [Scalekit Python SDK](https://pypi.org/project/scalekit-sdk-python/)
