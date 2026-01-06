# 🖥️ Claude Desktop Setup & Testing Guide

## 📋 Overview

This guide will help you configure Claude Desktop to connect to your MCP Educational Server with Scalekit OAuth 2.1 authentication.

---

## 🎯 **Step 1: Locate Claude Desktop Config**

Claude Desktop stores its MCP server configuration in:

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Full path (usually):**
```
C:\Users\imreo\AppData\Roaming\Claude\claude_desktop_config.json
```

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

---

## 🛠️ **Step 2: Update Configuration**

### Option A: Use the Generated Config (Recommended)

I've created a complete configuration file for you: `claude_desktop_config.json` in your project root.

**To use it:**
1. Copy the entire contents of `claude_desktop_config.json`
2. Open the Claude Desktop config file (path above)
3. **Backup your existing config first!**
4. Replace or merge with the new configuration

### Option B: Manual Configuration

If you prefer to manually edit your existing config:

```json
{
  "mcpServers": {
    "mcp-edu-server": {
      "command": "python",
      "args": [
        "C:\\Users\\imreo\\Documents\\MCP_diploma_thesis_final\\main.py"
      ],
      "env": {
        "SCALEKIT_ENV_URL": "https://mcpeduauth.scalekit.dev",
        "SCALEKIT_CLIENT_ID": "skc_106606852871095042",
        "SCALEKIT_CLIENT_SECRET": "your_secret_here",
        "SCALEKIT_MCP_SERVER_ID": "res_106614051991192578",
        "SCALEKIT_EXPECTED_AUDIENCE": "http://localhost:8000",
        "SCALEKIT_PROTECTED_RESOURCE_METADATA": "{\"authorization_servers\":[\"https://mcpeduauth.scalekit.dev/resources/res_106614051991192578\"],\"bearer_methods_supported\":[\"header\"],\"resource\":\"http://localhost:8000\",\"resource_documentation\":\"http://localhost:8000/docs\",\"scopes_supported\":[]}",
        "OPENAI_API_KEY": "your_openai_key_here",
        "VECTOR_DB_URL": "http://localhost:6334",
        "DEFAULT_COLLECTION": "educational_content",
        "ENABLE_RBAC": "True",
        "DEFAULT_USER_ROLE": "student",
        "HTTP_PORT": "8000",
        "ENABLE_AUTH": "True"
      }
    }
  }
}
```

**⚠️ Important Notes:**
- Replace `your_secret_here` and `your_openai_key_here` with actual values from `.env`
- Use double backslashes `\\` in Windows paths
- Ensure Qdrant is running before starting Claude Desktop

---

## 🔄 **Step 3: Restart Claude Desktop**

1. **Completely quit** Claude Desktop (not just close the window)
   - Right-click the tray icon → "Quit"
   - Or use Task Manager to end the process
2. **Restart** Claude Desktop
3. Check for MCP connection in the Claude Desktop interface

---

## 🧪 **Step 4: Test the Connection**

### Test 1: Check MCP Tools Available

In Claude Desktop, type:
```
What MCP tools do you have available?
```

**Expected Response:**
You should see:
- `health_check` - Server health status
- `search_content` - Search educational content with RBAC

### Test 2: Test Health Check Tool

Ask Claude:
```
Can you check the health of the MCP server using the health_check tool?
```

**Expected Response:**
```json
{
  "status": "healthy",
  "server": "MCP Educational Server",
  "version": "1.0.0",
  "authentication": "enabled",
  "rbac": "enabled"
}
```

### Test 3: Test Search Tool

Ask Claude:
```
Search for "quadratic equations" using the search_content tool
```

**Expected Behavior:**
- If Scalekit OAuth is working: Search executes and returns results
- If authentication fails: Error message about invalid token

---

## 🔐 **Step 5: Scalekit OAuth Flow**

### How It Should Work:

1. **Claude Desktop starts** and reads the MCP config
2. **Discovers OAuth metadata** from `/.well-known/oauth-protected-resource`
3. **Redirects you to Scalekit** for authentication (login page)
4. **You log in** with your Scalekit test organization credentials
5. **Scalekit issues a JWT token** with your role (student/teacher/admin)
6. **Claude Desktop uses the token** for all subsequent MCP requests
7. **Your MCP server validates** the token using Scalekit SDK

### If OAuth Flow Doesn't Start:

This might happen because Claude Desktop's MCP implementation may not fully support the OAuth 2.1 Protected Resource pattern yet. In that case, you have two options:

**Option A: Test with MCP Inspector (Recommended for Development)**
```bash
npm install -g @modelcontextprotocol/inspector
mcp-inspector python main.py
```

**Option B: Temporarily Disable Authentication (Testing Only)**

In your `.env` file:
```env
ENABLE_AUTH=False
```

Then restart the server. **Remember to re-enable it for production!**

---

## 🐛 **Troubleshooting**

### Issue: "MCP server not responding"

**Solution:**
1. Check if Qdrant is running:
   ```bash
   docker ps --filter name=qdrant-mcp-edu
   ```
2. Check if the server starts manually:
   ```bash
   cd "C:\Users\imreo\Documents\MCP_diploma_thesis_final"
   .\venv\Scripts\activate
   python main.py
   ```
3. Check Claude Desktop logs:
   ```
   %APPDATA%\Claude\logs\
   ```

### Issue: "Authentication failed"

**Solution:**
1. Verify Scalekit credentials in `.env` are correct
2. Check if `SCALEKIT_PROTECTED_RESOURCE_METADATA` is properly formatted (no line breaks)
3. Try disabling auth temporarily to test basic functionality

### Issue: "Python not found"

**Solution:**
Update the `command` in `claude_desktop_config.json` to use the full path:
```json
"command": "C:\\Users\\imreo\\Documents\\MCP_diploma_thesis_final\\venv\\Scripts\\python.exe"
```

### Issue: "No search results"

**Solution:**
1. Verify Qdrant has data:
   ```bash
   curl http://localhost:6334/collections/educational_content
   ```
2. Check if data was ingested properly (see `data/processed/` folder)
3. Try with a broader search query

---

## 📊 **Testing Checklist**

Use this checklist to verify everything is working:

- [ ] Claude Desktop shows MCP server as connected
- [ ] `health_check` tool is available
- [ ] `search_content` tool is available
- [ ] Health check returns "healthy" status
- [ ] Search returns results (with or without auth)
- [ ] OAuth flow initiates (or auth is disabled for testing)
- [ ] RBAC filtering works (different results for different roles)

---

## 🔄 **Alternative Testing Method: MCP Inspector**

If Claude Desktop doesn't work yet, use the official MCP Inspector:

### Install MCP Inspector:
```bash
npm install -g @modelcontextprotocol/inspector
```

### Run Your Server in Inspector Mode:
```bash
cd "C:\Users\imreo\Documents\MCP_diploma_thesis_final"
mcp-inspector python main.py
```

This will:
1. Open a web interface at `http://localhost:5173`
2. Show all available MCP tools
3. Let you test tools interactively
4. Display request/response details

**Benefits:**
- Visual interface for testing
- See raw MCP protocol messages
- Test OAuth flow manually
- Debug authentication issues

---

## 📈 **Next Steps After Successful Connection**

Once Claude Desktop is connected:

1. **Test Search Functionality**:
   - Search for various topics
   - Verify relevance scoring
   - Check response times

2. **Test RBAC**:
   - Create test users with different roles in Scalekit
   - Verify content filtering works correctly
   - Test hierarchical permissions (teacher sees student content)

3. **Performance Testing**:
   - Multiple concurrent searches
   - Large result sets
   - Memory usage monitoring

4. **Document Results**:
   - Screenshot successful OAuth flow
   - Record search performance metrics
   - Note any issues for thesis documentation

---

## 🎓 **For Your Thesis**

Document the following:

### Screenshots Needed:
1. ✅ Claude Desktop MCP configuration
2. ⏳ Scalekit OAuth login screen
3. ⏳ Successful authentication confirmation
4. ⏳ MCP tools available in Claude Desktop
5. ⏳ Successful search results
6. ⏳ RBAC filtering demonstration

### Metrics to Capture:
- OAuth flow completion time
- Search response times
- Number of results returned
- RBAC filter effectiveness
- Error rates (if any)

### Technical Details to Note:
- How Claude Desktop discovers OAuth endpoints
- Token validation process
- Role claim extraction from JWT
- RBAC filter application

---

## 📚 **References**

- **Claude Desktop MCP Docs**: https://modelcontextprotocol.io/docs/tools/claude-desktop
- **MCP Inspector**: https://github.com/modelcontextprotocol/inspector
- **Scalekit OAuth Docs**: https://docs.scalekit.com/authenticate/mcp/
- **FastMCP Documentation**: https://github.com/jlowin/fastmcp

---

**Ready to test?** Let me know if you need help with any step! 🚀
