# 🔌 Claude Desktop Connection Options

**Which config should you use?**

---

## 📊 Quick Decision Matrix

| Who | Where | Best Method | Why |
|-----|-------|-------------|-----|
| **You (Local)** | Same Raspberry Pi | Option 1: Direct STDIO | ✅ Fastest, no network latency |
| **You (Local)** | Same network | Option 2: HTTP Bridge | ✅ Tests production setup |
| **Remote Colleague** | Internet | Option 2: HTTP Bridge | ✅ Only option that works remotely |

---

## ✅ Option 1: Direct STDIO (Local Only - FASTEST)

**Best for:** You, running Claude Desktop on the same Raspberry Pi

### Configuration:

```json
{
  "mcpServers": {
    "leowiki-mcp-local": {
      "command": "python3",
      "args": [
        "/home/imreo/mcp-diploma-thesis-final/main.py"
      ],
      "env": {
        "OPENAI_API_KEY": "sk-proj-...",
        "ENABLE_AUTH": "false",
        "VECTOR_DB_URL": "http://localhost:6333",
        "DEFAULT_COLLECTION": "educational_content"
      }
    }
  }
}
```

### Pros:
- ✅ **Fastest** - No network overhead
- ✅ **Most direct** - Python process talks directly to Claude
- ✅ **Easy debugging** - See logs immediately
- ✅ **No HTTP bridge needed**

### Cons:
- ❌ Only works on the same machine
- ❌ Requires local Python environment
- ❌ Can't test production HTTPS setup

### When to use:
- Development on the Raspberry Pi
- Fastest response times
- Local testing

---

## ✅ Option 2: HTTP Bridge via npx (Local + Remote - WORKS EVERYWHERE)

**Best for:** Remote colleagues testing from anywhere in the world

### Configuration:

```json
{
  "mcpServers": {
    "leowiki-mcp-remote": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/client",
        "https://leowiki-mcp.stream/mcp"
      ],
      "env": {}
    }
  }
}
```

### Pros:
- ✅ **Works remotely** - Anywhere with internet
- ✅ **No local server needed** - Just Node.js/npx
- ✅ **Tests production setup** - Uses real HTTPS endpoint
- ✅ **Easy to share** - Same config for everyone

### Cons:
- ⚠️ Slower than STDIO (network latency)
- ⚠️ Requires internet connection
- ⚠️ Depends on npx being available

### When to use:
- **Remote colleagues** testing the server
- Testing from Windows/Mac machines
- Production-like testing
- **This is what your colleagues should use!**

---

## 🌍 Option 3: HTTP Bridge (Alternative - No npx)

**Best for:** Systems without Node.js/npx

You can also create a simple Python bridge script:

### Create `/home/imreo/mcp-diploma-thesis-final/http_bridge.py`:

```python
#!/usr/bin/env python3
"""
HTTP-to-STDIO Bridge for MCP
Allows Claude Desktop to connect to remote HTTP MCP servers
"""
import sys
import json
import requests

MCP_SERVER_URL = "https://leowiki-mcp.stream/mcp"

def main():
    """Forward STDIO messages to HTTP MCP server"""
    for line in sys.stdin:
        try:
            request = json.loads(line)
            response = requests.post(
                MCP_SERVER_URL,
                json=request,
                headers={"Content-Type": "application/json"}
            )
            print(json.dumps(response.json()), flush=True)
        except Exception as e:
            error = {
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": str(e)},
                "id": request.get("id")
            }
            print(json.dumps(error), flush=True)

if __name__ == "__main__":
    main()
```

### Configuration:

```json
{
  "mcpServers": {
    "leowiki-mcp-bridge": {
      "command": "python3",
      "args": [
        "/home/imreo/mcp-diploma-thesis-final/http_bridge.py"
      ],
      "env": {}
    }
  }
}
```

---

## 🎯 Recommended Setup

### For You (Raspberry Pi):

**Use Option 1 (Direct STDIO)** for fastest performance:

```json
{
  "mcpServers": {
    "leowiki-mcp": {
      "command": "python3",
      "args": ["/home/imreo/mcp-diploma-thesis-final/main.py"],
      "env": {
        "OPENAI_API_KEY": "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",
        "ENABLE_AUTH": "false",
        "VECTOR_DB_URL": "http://localhost:6333"
      }
    }
  }
}
```

### For Remote Colleagues (Windows/Mac/Linux):

**Use Option 2 (HTTP via npx)** - works from anywhere:

```json
{
  "mcpServers": {
    "leowiki-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/client",
        "https://leowiki-mcp.stream/mcp"
      ],
      "env": {}
    }
  }
}
```

---

## 📝 Instructions for Remote Colleagues

Send them this config:

### Claude Desktop Config for Remote Testing

**Step 1:** Find your config file:
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

**Step 2:** Add this configuration:

```json
{
  "mcpServers": {
    "leowiki-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/client",
        "https://leowiki-mcp.stream/mcp"
      ],
      "env": {}
    }
  }
}
```

**Step 3:** Restart Claude Desktop completely

**Step 4:** Test with:
```
Use the search_content tool to search for "HTL Leonding"
```

---

## 🧪 Testing Each Option

### Test Direct STDIO (Option 1):

```bash
# On Raspberry Pi
cd /home/imreo/mcp-diploma-thesis-final

# Test in terminal first
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python3 main.py
```

### Test HTTP Bridge (Option 2):

```bash
# From any computer with internet
npx -y @modelcontextprotocol/client https://leowiki-mcp.stream/mcp
```

### Test Production Endpoint:

```bash
# HTTP health check
curl https://leowiki-mcp.stream/health

# MCP tools list
curl -X POST https://leowiki-mcp.stream/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

---

## 🔍 Comparison

| Feature | Direct STDIO (Option 1) | HTTP Bridge (Option 2) |
|---------|-------------------------|------------------------|
| **Speed** | ⚡ Very Fast | 🐢 Network latency |
| **Remote Access** | ❌ No | ✅ Yes |
| **Setup** | Python + deps | Just npx |
| **Internet Required** | ❌ No | ✅ Yes |
| **Production Testing** | ❌ No (local) | ✅ Yes (HTTPS) |
| **Colleague Access** | ❌ No | ✅ Yes |
| **Best For** | Local dev | Remote testing |

---

## 💡 Pro Tips

### For Development (You):
- Use **Option 1** (Direct STDIO) most of the time
- Switch to **Option 2** when testing production setup
- Keep both configs in your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "leowiki-local": {
      "command": "python3",
      "args": ["/home/imreo/mcp-diploma-thesis-final/main.py"],
      "env": {...}
    },
    "leowiki-remote": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/client", "https://leowiki-mcp.stream/mcp"],
      "env": {}
    }
  }
}
```

Then you can choose which one to use in Claude Desktop!

### For Remote Colleagues:
- **Only Option 2 works** for them
- They need:
  - Node.js/npx installed (usually comes with Node.js)
  - Internet connection
  - The public URL: `https://leowiki-mcp.stream/mcp`

---

## ❓ FAQ

### Q: Which is shorter/simpler?

**A:** Option 2 (HTTP Bridge) is simpler for remote users:
- ✅ Fewer lines in config
- ✅ No environment variables needed
- ✅ Works out of the box with just npx

### Q: Will Option 2 work for my colleague in another country?

**A:** Yes! ✅ As long as:
- They have internet access
- `leowiki-mcp.stream` is publicly accessible (it is!)
- Their firewall doesn't block HTTPS (unlikely)

### Q: Which should I recommend to colleagues?

**A:** **Option 2 (HTTP Bridge via npx)** - it's the only one that works remotely!

### Q: Can I use both?

**A:** Yes! You can have multiple MCP servers in your config. Name them differently:
- `"leowiki-local"` for Option 1
- `"leowiki-remote"` for Option 2

---

## 🎯 Summary

**For Your Colleagues (Remote Testing):**
```json
{
  "mcpServers": {
    "leowiki-mcp": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/client", "https://leowiki-mcp.stream/mcp"],
      "env": {}
    }
  }
}
```
✅ **This is the shortest config that works remotely!**

**For You (Local Development):**
```json
{
  "mcpServers": {
    "leowiki-mcp": {
      "command": "python3",
      "args": ["/home/imreo/mcp-diploma-thesis-final/main.py"],
      "env": {
        "OPENAI_API_KEY": "...",
        "ENABLE_AUTH": "false"
      }
    }
  }
}
```
✅ **Fastest for local development!**

---

*Last Updated: January 8, 2026*  
*Recommended for colleagues: Option 2 (HTTP Bridge)*
