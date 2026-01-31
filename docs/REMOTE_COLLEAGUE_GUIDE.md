# 🌍 Remote Testing Guide - For Colleagues

**Quick start guide for testing the LeoWiki MCP Server from anywhere in the world**

---

## ✅ What You Need

- Claude Desktop installed ([download here](https://claude.ai/download))
- Internet connection
- Node.js with npx (usually included with Node.js)

---

## 📝 Setup Instructions

### Step 1: Find Your Claude Desktop Config File

**Windows:**
```
C:\Users\YOUR_NAME\AppData\Roaming\Claude\claude_desktop_config.json
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

### Step 2: Copy This Configuration

Open the file and paste this:

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

**That's it!** This is the shortest working configuration. ✅

---

### Step 3: Restart Claude Desktop

**Windows:**
1. Right-click Claude in taskbar → Quit
2. Wait 5 seconds
3. Start Claude Desktop again

**macOS:**
1. Press Cmd+Q
2. Wait 5 seconds
3. Start Claude Desktop again

**Linux:**
```bash
pkill -f claude
sleep 5
# Start Claude Desktop again
```

---

### Step 4: Test the Connection

In Claude Desktop, type:

```
Use the search_content tool to search for "HTL Leonding"
```

**Expected result:** Claude uses the tool and shows search results ✅

---

## 🧪 Quick Tests

### Test 1: List Available Tools

Ask Claude:
```
What MCP tools do you have available?
```

**Expected:** Claude lists:
- `search_content` - Search educational content
- `health_check` - Check server health

### Test 2: Search Test

Ask Claude:
```
Search for "programming" in the educational database
```

**Expected:** Claude performs a search and shows results

---

## 🆘 Troubleshooting

### Problem: "npx: command not found"

**Solution:** Install Node.js from https://nodejs.org

```bash
# Verify npx is installed
npx --version
```

### Problem: "Connection refused"

**Solution:** Test if server is accessible

```bash
# Should return JSON with status
curl https://leowiki-mcp.stream/health
```

### Problem: "MCP icon not showing"

**Solution:** 
1. Completely quit Claude Desktop
2. Wait 10 seconds
3. Restart Claude Desktop
4. Look for 🔌 icon in bottom right

### Problem: "Invalid JSON in config file"

**Solution:** Validate your config

```bash
# Linux/macOS
cat ~/.config/Claude/claude_desktop_config.json | python3 -m json.tool

# Windows PowerShell
Get-Content "$env:APPDATA\Claude\claude_desktop_config.json" | python -m json.tool
```

---

## 📊 What's Happening Behind the Scenes

```
Your Computer          Internet          Raspberry Pi
┌─────────────┐       ┌────────┐       ┌────────────┐
│   Claude    │       │  HTTPS │       │ MCP Server │
│   Desktop   │◄─────►│        │◄─────►│  (Imre's)  │
└─────────────┘  npx  └────────┘       └────────────┘
```

The `npx @modelcontextprotocol/client` command:
1. Downloads a small HTTP-to-STDIO bridge
2. Connects to `https://leowiki-mcp.stream/mcp`
3. Forwards Claude's requests to the remote server
4. Returns responses back to Claude Desktop

---

## 🎯 What Works

✅ Search educational content  
✅ Get collection statistics  
✅ Health checks  
✅ RBAC (role-based access control)  
✅ All features accessible remotely  

---

## 🔒 Security & Privacy

- All connections use **HTTPS** (encrypted)
- Server is located in Austria (HTL Leonding)
- Authentication is currently **disabled** for testing
- Your searches are logged for debugging only
- No personal data collected

---

## 💬 Feedback

Please report:
- ✅ What works well
- ❌ What doesn't work
- 🐛 Any bugs or errors
- 💡 Improvement suggestions

**Contact:** Obermüller Imre  
**Server:** https://leowiki-mcp.stream  
**Status:** Check at https://leowiki-mcp.stream/health

---

## ✨ Summary

**The configuration is literally just 3 lines:**

```json
"command": "npx",
"args": ["-y", "@modelcontextprotocol/client", "https://leowiki-mcp.stream/mcp"],
"env": {}
```

**Yes, this works from anywhere in the world! 🌍**

No VPN needed, no special setup, just internet access.

---

*HTL Leonding - MCP Educational Server*  
*Diploma Thesis Project - 2026*
