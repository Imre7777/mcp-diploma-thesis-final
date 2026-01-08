# 🚀 Quick Start Guide: Remote Testing with Claude Desktop

**For:** External testers connecting from anywhere  
**Server:** https://leowiki-mcp.stream  
**Date:** January 8, 2026  
**Current Status:** ✅ Server Online & Ready

---

## ⚡ FASTEST START (5 Minutes)

### What Your Colleague Needs:
1. ✅ Claude Desktop installed ([download here](https://claude.ai/download))
2. ✅ Internet connection
3. ✅ Scalekit OAuth credentials (see below)

---

## 🔐 STEP 1: Get OAuth Credentials

### Current Scalekit Configuration:
- **Authorization Server:** https://mcpeduauth.scalekit.dev
- **Client ID:** `skc_35934031996379566`
- **Client Secret:** `test_sk_JnDlRTWW5RnNdg2TLYCWnuPg2O2cKrDAJHkp8dhFxg5NEG-PaYiYv3OT1X1v_jgz`

### Test Users Available:
You need to create test users in Scalekit Dashboard or provide credentials to your colleague.

**Recommended test users:**
- `student@test.local` (role: student) - sees only public/student content
- `teacher@test.local` (role: teacher) - sees student + teacher content
- `admin@test.local` (role: admin) - sees everything

**Create users at:** https://app.scalekit.com

---

## 🖥️ STEP 2: Configure Claude Desktop

### Location of Config File:

**Windows:**
```
C:\Users\[USERNAME]\AppData\Roaming\Claude\claude_desktop_config.json
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

### Configuration Method A: HTTP Transport (Recommended for Remote)

**Add this to `claude_desktop_config.json`:**

```json
{
  "mcpServers": {
    "leowiki-mcp": {
      "url": "https://leowiki-mcp.stream/mcp",
      "transport": "http",
      "auth": {
        "type": "oauth2",
        "oauth2": {
          "authorizationUrl": "https://mcpeduauth.scalekit.dev/authorize",
          "tokenUrl": "https://mcpeduauth.scalekit.dev/oauth/token",
          "clientId": "skc_35934031996379566",
          "clientSecret": "test_sk_JnDlRTWW5RnNdg2TLYCWnuPg2O2cKrDAJHkp8dhFxg5NEG-PaYiYv3OT1X1v_jgz",
          "scopes": ["mcp:read", "mcp:write"]
        }
      }
    }
  }
}
```

**Note:** This configuration enables automatic OAuth authentication flow in Claude Desktop.

---

### Configuration Method B: Alternative with Token (If Method A doesn't work)

If Claude Desktop doesn't support automatic OAuth flow yet, use a manual Bearer token:

#### First, get a token manually:

```bash
# Your colleague runs this from their terminal:
curl -X POST https://mcpeduauth.scalekit.dev/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=skc_35934031996379566" \
  -d "client_secret=test_sk_JnDlRTWW5RnNdg2TLYCWnuPg2O2cKrDAJHkp8dhFxg5NEG-PaYiYv3OT1X1v_jgz" \
  -d "scope=mcp:read mcp:write"
```

**Response will contain:**
```json
{
  "access_token": "eyJhbGc...",
  "expires_in": 3600
}
```

#### Then use the token in Claude Desktop config:

```json
{
  "mcpServers": {
    "leowiki-mcp": {
      "url": "https://leowiki-mcp.stream/mcp",
      "transport": "http",
      "headers": {
        "Authorization": "Bearer YOUR_ACCESS_TOKEN_HERE"
      }
    }
  }
}
```

**Important:** Token expires after 1 hour, so you'll need to refresh it.

---

## 🧪 STEP 3: Test the Connection

### 1. Restart Claude Desktop

**Windows:**
- Close Claude Desktop completely (check Task Manager)
- Restart the app

**macOS:**
- Cmd+Q to quit
- Reopen Claude Desktop

**Linux:**
```bash
pkill -f claude
# Then restart
```

### 2. Verify Connection

Look for the **🔌 MCP icon** in the bottom-right corner of Claude Desktop.

- **Green/Active** = Connected ✅
- **Gray/Inactive** = Not connected ❌

Click the icon to see "leowiki-mcp" in the list.

---

### 3. Test Queries

#### Test 1: List Available Tools

In Claude Desktop, type:
```
What MCP tools do you have available?
```

**Expected:** Claude should list:
- `ping` - Health check
- `vector_search` - Semantic search
- `advanced_search` - Filtered search

---

#### Test 2: Health Check

```
Use the ping tool to check if the MCP server is healthy
```

**Expected response:**
```json
{
  "status": "healthy",
  "server": "MCP Educational Server",
  "version": "1.0.0"
}
```

---

#### Test 3: Semantic Search

```
Search for "HTL Leonding" using the vector_search tool
```

**Expected:** Claude uses the tool and returns search results (if data is loaded).

---

#### Test 4: RBAC (Role-Based Access)

If logged in as **student:**
```
Search for content about "teacher materials"
```
**Expected:** Only sees student-accessible content

If logged in as **teacher:**
```
Search for content about "exam solutions"
```
**Expected:** Sees both student and teacher content

---

## 🆘 TROUBLESHOOTING

### Problem: "Cannot connect to MCP server"

**Quick checks:**

1. **Test server is online:**
```bash
curl https://leowiki-mcp.stream/health
```
Should return: `{"status":"healthy",...}`

2. **Test OAuth discovery:**
```bash
curl https://leowiki-mcp.stream/.well-known/oauth-protected-resource
```
Should return OAuth metadata

3. **Validate JSON config:**
- Copy your config to https://jsonlint.com
- Must be valid JSON (no trailing commas!)

---

### Problem: "Authentication failed"

**Solutions:**

1. **Check credentials:**
   - Client ID: `skc_35934031996379566`
   - Client Secret: `test_sk_JnDlRTWW5RnNdg2TLYCWnuPg2O2cKrDAJHkp8dhFxg5NEG-PaYiYv3OT1X1v_jgz`
   - No extra spaces or line breaks

2. **Test OAuth directly:**
```bash
curl -X POST https://mcpeduauth.scalekit.dev/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=skc_35934031996379566" \
  -d "client_secret=test_sk_JnDlRTWW5RnNdg2TLYCWnuPg2O2cKrDAJHkp8dhFxg5NEG-PaYiYv3OT1X1v_jgz"
```

3. **Check Scalekit Dashboard:**
   - Login at https://app.scalekit.com
   - Verify redirect URIs include: `claude-desktop://auth/callback`

---

### Problem: "Tools not showing up"

**Solutions:**

1. Completely restart Claude Desktop (kill process)
2. Wait 10 seconds after startup
3. Check Claude Desktop logs:
   - Windows: `%APPDATA%\Claude\logs\`
   - macOS: `~/Library/Logs/Claude/`
   - Linux: `~/.config/Claude/logs/`

---

### Problem: "No search results"

**Possible causes:**

1. **Database might be empty** - Check with admin
2. **RBAC filtering** - Student role can't see teacher content
3. **Search term too specific** - Try more general terms

---

## 📊 WHAT TO TEST

### Functionality Tests:
- [ ] Connection establishes
- [ ] OAuth login works
- [ ] Tools are listed
- [ ] Health check (`ping` tool)
- [ ] Basic search (`vector_search`)
- [ ] Advanced search with filters
- [ ] RBAC (different roles see different content)

### Performance Tests:
- [ ] Response time < 3 seconds
- [ ] Multiple queries in succession
- [ ] Large result sets

### Edge Cases:
- [ ] Empty search query
- [ ] Very long search query
- [ ] Special characters (ä, ö, ü, ß)
- [ ] Different languages (German, English)

---

## 📈 EXPECTED PERFORMANCE

| Operation | Expected Time |
|-----------|---------------|
| Connection | 2-5 seconds |
| OAuth login | 5-10 seconds |
| Health check | < 1 second |
| Search query | 1-3 seconds |
| Large results | 2-5 seconds |

---

## 🔒 SECURITY & PRIVACY

### What the server sees:
- ✅ Your search queries
- ✅ Tool usage
- ✅ Timestamps
- ✅ Your IP address

### What the server DOESN'T see:
- ❌ Your Claude conversations (only the tool calls)
- ❌ Other tools you use
- ❌ Personal data (unless you send it)

**All traffic is encrypted via HTTPS (TLS 1.3)**

---

## 💡 TIPS

### Effective Search Queries:

**Good:**
```
"Search for Python programming basics"
"Find information about the Matura exam"
"What is HTL Leonding?"
```

**Less effective:**
```
"py" (too short)
"12345" (no semantic meaning)
```

### Force Tool Usage:

If Claude doesn't use the tool automatically:
```
Please use EXACTLY the vector_search tool to search for "HTL Leonding"
```

---

## 📞 SUPPORT

**If you encounter issues, contact:**

**Administrator:** Obermüller Imre  
**Email:** imre.obermueller@gmail.com

**Provide this information:**
1. Operating system (Windows/macOS/Linux)
2. Claude Desktop version
3. Exact error message
4. What you tried
5. Logs (if available)

---

## ✅ SUCCESS CHECKLIST

You're successful when:

- [x] Claude Desktop shows MCP icon (🔌)
- [x] Icon is green/active
- [x] "leowiki-mcp" is listed
- [x] Claude can list the tools
- [x] Health check works
- [x] Search returns results
- [x] No errors in logs
- [x] Response times are good (< 3 sec)

---

## 🎯 QUICK COMMAND REFERENCE

### Test from Command Line:

```bash
# Test server is up
curl https://leowiki-mcp.stream/health

# Test OAuth discovery
curl https://leowiki-mcp.stream/.well-known/oauth-protected-resource

# Get access token
curl -X POST https://mcpeduauth.scalekit.dev/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=skc_35934031996379566" \
  -d "client_secret=test_sk_JnDlRTWW5RnNdg2TLYCWnuPg2O2cKrDAJHkp8dhFxg5NEG-PaYiYv3OT1X1v_jgz"

# Test authenticated endpoint (with token)
curl https://leowiki-mcp.stream/mcp \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'
```

---

## 🚀 START NOW!

1. ✅ Install Claude Desktop
2. ✅ Edit config file
3. ✅ Add server configuration (see STEP 2)
4. ✅ Save and restart Claude Desktop
5. ✅ Look for 🔌 icon
6. ✅ Start testing!

**Good luck! 🎉**

---

**Server Status:** 🟢 Online & Ready  
**Last Updated:** January 8, 2026  
**Version:** 1.0.0

**Server URL:** https://leowiki-mcp.stream  
**Documentation:** https://leowiki-mcp.stream/docs
