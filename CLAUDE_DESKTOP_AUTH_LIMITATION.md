# 🔐 Claude Desktop Authentication Limitation

**Status:** ❌ **Scalekit OAuth 2.1 Does NOT Work with Claude Desktop**  
**Date:** January 8, 2026

---

## 🚨 The Problem

The two documents you created (`SCALEKIT_MCP_CREDENTIALS.md` and `MCP_SERVER_INTEGRATION_PLAN.md`) describe implementing **Scalekit OAuth 2.1** authentication. However, **this will NOT work with Claude Desktop** for the following reasons:

### Why OAuth 2.1 Doesn't Work with Claude Desktop

| Claude Desktop | Scalekit OAuth 2.1 | Compatible? |
|----------------|-------------------|-------------|
| Runs MCP servers via **STDIO** (stdin/stdout) | Requires **HTTP redirects** to login pages | ❌ No |
| No web browser available | Needs browser for user login | ❌ No |
| Runs as child process | Needs callback URLs (`/callback`) | ❌ No |
| No HTTP server | Requires HTTP endpoints | ❌ No |

### The OAuth Flow That Won't Work

```
┌──────────────┐         ┌─────────────┐         ┌──────────────┐
│   Claude     │  STDIO  │ MCP Server  │  HTTP   │  Scalekit    │
│   Desktop    ├────────▶│   (Your)    ├────────▶│  Auth Server │
└──────────────┘         └─────────────┘         └──────────────┘
       ▲                                                  │
       │                                                  │
       └──────── ❌ No browser for redirect! ────────────┘
```

**Why it fails:**
1. Claude Desktop starts your MCP server as a subprocess
2. Your server tries to redirect to Scalekit login page
3. **Problem:** Claude Desktop has no browser to show the login page
4. Authentication fails

---

## ✅ What DOES Work with Claude Desktop

### Option 1: Disable Authentication (Current Setup)

**Status:** ✅ **Already configured and working**

Your `.env` file already has:
```env
ENABLE_AUTH=false
```

This is fine for:
- ✅ Local development
- ✅ Testing
- ✅ Trusted networks
- ✅ Diploma thesis demonstration

**Pros:**
- Works immediately
- No configuration needed
- Simple for users

**Cons:**
- No access control
- Anyone with server URL can use it

---

### Option 2: Static Token Authentication (Simple Alternative)

Instead of dynamic OAuth, use **pre-generated tokens** that users manually add to their config.

#### How It Works:

```
1. Administrator generates token via web interface
   └─▶ Token: "mcp_token_abc123..."

2. User adds token to Claude Desktop config:
   {
     "mcpServers": {
       "leowiki": {
         "command": "python",
         "args": ["path/to/main.py"],
         "env": {
           "AUTH_TOKEN": "mcp_token_abc123..."
         }
       }
     }
   }

3. MCP server validates token on each request
   └─▶ ✅ Valid: Process request
   └─▶ ❌ Invalid: Reject request
```

**Pros:**
- Works with Claude Desktop
- Simple to implement
- User-friendly

**Cons:**
- Tokens must be manually distributed
- No automatic expiration
- Manual revocation needed

---

### Option 3: ScaleKit OAuth for Web Clients Only

Keep Scalekit OAuth for **web-based clients** (MCP Inspector, custom web apps), but disable it for Claude Desktop.

#### Architecture:

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Server                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  STDIO Mode (Claude Desktop)                            │
│  └─▶ ENABLE_AUTH=false                                  │
│      No authentication required                         │
│                                                          │
│  HTTP Mode (Web Clients)                                │
│  └─▶ ENABLE_AUTH=true                                   │
│      Full Scalekit OAuth 2.1                            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Implementation:**

```python
# In main.py
if __name__ == "__main__":
    if "--http" in sys.argv:
        # HTTP mode: Enable OAuth
        config.enable_auth = True
    else:
        # STDIO mode (Claude Desktop): Disable OAuth
        config.enable_auth = False
```

**Pros:**
- OAuth for production web access
- Simple STDIO for Claude Desktop
- Best of both worlds

**Cons:**
- Claude Desktop has no authentication
- More complex configuration

---

## 🎯 Recommended Solution for Your Diploma Thesis

### For Development & Testing

**Keep current setup:**
```env
ENABLE_AUTH=false
```

**Rationale:**
- ✅ Works immediately with Claude Desktop
- ✅ Simple for thesis demonstration
- ✅ Focus on core functionality (vector search, RBAC)

### For Production Deployment (Future)

**Option A: Transport-Based Auth**
- STDIO (Claude Desktop): No auth or static tokens
- HTTP (Web): Full Scalekit OAuth 2.1

**Option B: Static Token System**
- Generate tokens via admin interface
- Users manually add to config
- Simple but secure enough

---

## 📝 What to Do with Your Scalekit Documents

### Keep Them as Future Work

Your `SCALEKIT_MCP_CREDENTIALS.md` and `MCP_SERVER_INTEGRATION_PLAN.md` are **valuable documentation** for:

1. **Future MCP Protocol Updates**
   - When MCP adds OAuth support, you're ready

2. **Web-Based Clients**
   - MCP Inspector with OAuth
   - Custom web applications
   - API integrations

3. **Diploma Thesis Documentation**
   - Shows you researched production authentication
   - Demonstrates understanding of OAuth 2.1
   - Explains architectural decisions

### Add a Note at the Top

Add this warning to both documents:

```markdown
> ⚠️ **IMPORTANT: Claude Desktop Compatibility**
> 
> This OAuth 2.1 integration is designed for **HTTP-based MCP clients** only.
> **Claude Desktop does NOT support this authentication method** because it runs
> MCP servers via STDIO without a web browser.
> 
> **For Claude Desktop:** Use `ENABLE_AUTH=false` in your `.env` file.
> 
> **For Web Clients:** Use the OAuth 2.1 flow described below.
> 
> See `CLAUDE_DESKTOP_AUTH_LIMITATION.md` for details.
```

---

## 🔧 Quick Fix for Claude Desktop

### Update Your `.env` File

Make sure you have:

```env
# For Claude Desktop (STDIO mode)
ENABLE_AUTH=false

# Scalekit credentials (for future web-based clients)
SCALEKIT_ENV_URL=https://leowikimcp.scalekit.dev
SCALEKIT_CLIENT_ID=skc_107036659593249282
SCALEKIT_CLIENT_SECRET=<your-secret>
```

### Update Your Claude Desktop Config

Make sure your `claude_desktop_config.json` has:

```json
{
  "mcpServers": {
    "leowiki-mcp": {
      "command": "python",
      "args": [
        "/home/imreo/mcp-diploma-thesis-final/main.py"
      ],
      "env": {
        "ENABLE_AUTH": "false"
      }
    }
  }
}
```

**Note:** The `env` section in Claude Desktop config **overrides** the `.env` file.

---

## 🧪 Testing

After making these changes:

1. **Stop Claude Desktop completely**
   ```bash
   pkill -f claude
   ```

2. **Verify your .env file**
   ```bash
   grep ENABLE_AUTH /home/imreo/mcp-diploma-thesis-final/.env
   # Should show: ENABLE_AUTH=false
   ```

3. **Restart Claude Desktop**

4. **Test the connection**
   ```
   Use the search_content tool to search for "test"
   ```

---

## 📚 Summary

| Authentication Method | Claude Desktop | Web Clients | Recommended |
|-----------------------|----------------|-------------|-------------|
| **No Auth** (current) | ✅ Works | ⚠️ Insecure | ✅ For dev/thesis |
| **Scalekit OAuth 2.1** | ❌ No browser | ✅ Full OAuth | ❌ Not for Claude Desktop |
| **Static Tokens** | ✅ Manual setup | ✅ Works | ✅ For production |
| **Transport-Based** | ✅ STDIO: no auth | ✅ HTTP: OAuth | ✅ Best of both |

---

## 🎓 For Your Diploma Thesis

### What to Document

1. **Authentication Architecture**
   - Researched Scalekit OAuth 2.1
   - Implemented server-side OAuth endpoints
   - Documented Claude Desktop limitations

2. **Design Decisions**
   - Why OAuth 2.1 doesn't work with STDIO
   - Trade-offs between security and usability
   - Transport-based authentication strategy

3. **Future Work**
   - OAuth for web-based clients
   - Static token system for production
   - MCP protocol OAuth support (when available)

### How to Present It

```
"While researching production authentication, I investigated OAuth 2.1
integration with Scalekit. However, I discovered that Claude Desktop's
STDIO-based architecture is incompatible with web-based OAuth flows.

For the thesis demonstration, I implemented a flexible authentication
system that can be enabled/disabled via configuration. In production,
this allows:
- HTTP clients to use full OAuth 2.1 authentication
- STDIO clients (like Claude Desktop) to use static tokens or run in trusted mode

This demonstrates understanding of real-world constraints and the ability
to adapt security requirements to different client architectures."
```

---

## 🆘 Still Having Issues?

### Common Problems

1. **"Authentication required" error**
   - Check `ENABLE_AUTH=false` in `.env`
   - Check Claude Desktop config has `"ENABLE_AUTH": "false"`

2. **"Connection refused"**
   - Server might not be running
   - Check: `docker ps` or `python main.py --http`

3. **"Tools not available"**
   - Restart Claude Desktop completely
   - Check server logs: `docker compose logs mcp-server`

---

**Bottom Line:** Keep `ENABLE_AUTH=false` for Claude Desktop. Your Scalekit documentation is valuable for future web-based clients, but it won't work with Claude Desktop's STDIO architecture.

---

*Document Created: January 8, 2026*  
*Author: AI Assistant*  
*Related Files: SCALEKIT_MCP_CREDENTIALS.md, MCP_SERVER_INTEGRATION_PLAN.md*
