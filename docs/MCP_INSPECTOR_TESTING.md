# 🔍 MCP Inspector Testing Guide

## 📋 Overview

MCP Inspector is an official tool from the MCP team that provides a web-based interface for testing MCP servers. It's perfect for:
- Testing MCP tools without OAuth complexity
- Debugging server responses
- Verifying functionality before Claude Desktop integration
- Visual inspection of MCP protocol messages

---

## 🛠️ Step 1: Install MCP Inspector

### Prerequisites
- Node.js and npm must be installed
- Check with: `node --version` and `npm --version`

### Installation

**Option A: Global Installation (Recommended)**
```bash
npm install -g @modelcontextprotocol/inspector
```

**Option B: npx (No Installation Required)**
```bash
# Will download and run automatically
npx @modelcontextprotocol/inspector
```

---

## 🚀 Step 2: Launch MCP Inspector with Your Server

### Method 1: With Authentication Disabled (Easier for First Test)

**1. Temporarily disable authentication:**

Edit your `.env` file (or create one from `.environ`):
```env
ENABLE_AUTH=False
```

**2. Launch MCP Inspector:**
```bash
cd "C:\Users\imreo\Documents\MCP_diploma_thesis_final"
.\venv\Scripts\activate
mcp-inspector python main.py
```

**3. Open in browser:**
- MCP Inspector will automatically open at `http://localhost:5173`
- If not, manually navigate to that URL

---

### Method 2: With Authentication Enabled (Full OAuth Testing)

**Keep `ENABLE_AUTH=True` in `.env`**

```bash
cd "C:\Users\imreo\Documents\MCP_diploma_thesis_final"
.\venv\Scripts\activate
mcp-inspector python main.py
```

MCP Inspector will:
1. Discover OAuth endpoints automatically
2. Show OAuth configuration
3. Allow you to manually provide Bearer tokens for testing

---

## 🧪 Step 3: Test Your MCP Tools

### Expected Interface

You should see:

```
╔══════════════════════════════════════════╗
║         MCP INSPECTOR                    ║
╠══════════════════════════════════════════╣
║  Server: MCP Educational Server          ║
║  Status: Connected ✓                     ║
║                                          ║
║  Available Tools:                        ║
║    • health_check                        ║
║    • search_content                      ║
╚══════════════════════════════════════════╝
```

---

### Test 1: Health Check Tool

**1. Click on `health_check` tool**

**2. Execute (no parameters needed)**

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

**✅ Success if**: Status is "healthy"

---

### Test 2: Search Content Tool (Without Auth)

**If auth is disabled (`ENABLE_AUTH=False`):**

**1. Click on `search_content` tool**

**2. Fill in parameters:**
```json
{
  "query": "mathematics",
  "limit": 5,
  "access_level": "student"
}
```

**3. Execute**

**Expected Response:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "Found 5 results for 'mathematics'\n\n**Result 1** (score: 0.892)\n..."
    }
  ]
}
```

**✅ Success if**: Results are returned with relevant content

---

### Test 3: Search Content Tool (With Auth)

**If auth is enabled (`ENABLE_AUTH=True`):**

**1. MCP Inspector will show OAuth configuration**

**2. You'll need to provide a Bearer token manually**
   - Either generate one from Scalekit dashboard
   - Or temporarily disable auth for testing

**3. Inspector will show request/response with full OAuth details**

---

## 📊 Test Cases to Try

### Basic Searches

| Test | Query | Expected Results |
|------|-------|------------------|
| 1 | "mathematics" | Math-related content |
| 2 | "science" | Science topics |
| 3 | "history" | Historical content |
| 4 | "" (empty) | Error handling |
| 5 | "xyzabc123notreal" | No results (graceful) |

### RBAC Testing (with auth disabled)

| Access Level | Query | Should Return |
|--------------|-------|---------------|
| student | "test" | Student-level content only |
| teacher | "test" | Student + teacher content |
| admin | "test" | All content |

### Performance Testing

| Test | Limit | Measure |
|------|-------|---------|
| Small | 5 | Response time < 500ms |
| Medium | 25 | Response time < 1s |
| Large | 100 | Response time < 2s |

---

## 🔍 What to Look For

### Successful Test Indicators:

1. **Connection Status**: "Connected" indicator is green
2. **Tools Visible**: Both `health_check` and `search_content` appear
3. **Health Check**: Returns "healthy" status
4. **Search Results**: Relevant content returned
5. **Response Times**: < 1 second for typical queries
6. **Error Handling**: Graceful errors for invalid inputs

### Red Flags:

- ❌ "Connection Failed" or "Disconnected"
- ❌ No tools visible
- ❌ Timeout errors (> 5 seconds)
- ❌ Server crashes on certain inputs
- ❌ Incorrect RBAC filtering

---

## 📸 Screenshots for Your Thesis

Capture these for documentation:

1. ✅ MCP Inspector interface with server connected
2. ✅ List of available MCP tools
3. ✅ Health check successful response
4. ✅ Search query and results
5. ✅ RBAC filtering demonstration (different roles)
6. ✅ Response time metrics
7. ✅ OAuth configuration (if enabled)

---

## 🐛 Troubleshooting

### Issue: "Connection Failed"

**Solution:**
```bash
# Check if server is running
python tests/test_server_endpoints.py

# If not, start it manually first
python main.py
# Then in another terminal:
mcp-inspector
```

### Issue: "No tools visible"

**Solution:**
- Check server logs for errors
- Verify FastMCP is properly initialized
- Try restarting MCP Inspector

### Issue: "Authentication errors"

**Solution:**
```bash
# Temporarily disable auth for testing
# In .env:
ENABLE_AUTH=False

# Restart server and inspector
```

### Issue: "Search returns no results"

**Solution:**
```bash
# Verify Qdrant has data
curl http://localhost:6334/collections/educational_content

# Should show points_count: 757
```

### Issue: "Slow response times"

**Solution:**
- Check Qdrant is running: `docker ps`
- Check OpenAI API key is valid
- Reduce limit parameter (try limit=5)

---

## 📝 Testing Checklist

Use this checklist during testing:

### Setup
- [ ] MCP Inspector installed
- [ ] Server is running
- [ ] Qdrant is running (757 documents)
- [ ] `.env` file configured

### Basic Functionality
- [ ] MCP Inspector connects to server
- [ ] Tools are visible (health_check, search_content)
- [ ] Health check returns healthy status
- [ ] Search tool accepts parameters
- [ ] Search returns results

### Search Quality
- [ ] Results are relevant to query
- [ ] Scores are reasonable (0.5 - 1.0)
- [ ] Response time < 1 second
- [ ] Handles empty queries gracefully
- [ ] Handles large result sets

### RBAC (with auth disabled)
- [ ] Student role filters correctly
- [ ] Teacher role sees more content
- [ ] Admin role sees all content

### Performance
- [ ] Multiple consecutive searches work
- [ ] No memory leaks (check Task Manager)
- [ ] Server doesn't crash

### OAuth (if enabled)
- [ ] OAuth discovery metadata visible
- [ ] Authorization server URL shown
- [ ] Token validation requirements clear

---

## 🎯 Success Criteria

**You're ready for Claude Desktop integration if:**

✅ All basic functionality tests pass  
✅ Search returns relevant results  
✅ Response times are acceptable (< 1s)  
✅ RBAC filtering works correctly  
✅ No crashes or errors  
✅ Performance is stable  

---

## 📊 Test Results Template

Use this to document your results:

```markdown
# MCP Inspector Test Results

**Date**: [DATE]
**Server Version**: 1.0.0
**Documents in Qdrant**: 757

## Test Results

### Health Check
- Status: [ ] PASS / [ ] FAIL
- Response Time: ___ ms
- Notes: ___

### Search Tool
- Status: [ ] PASS / [ ] FAIL
- Average Response Time: ___ ms
- Relevance: [ ] Good / [ ] Fair / [ ] Poor
- Notes: ___

### RBAC Filtering
- Student filtering: [ ] PASS / [ ] FAIL
- Teacher filtering: [ ] PASS / [ ] FAIL
- Admin filtering: [ ] PASS / [ ] FAIL
- Notes: ___

### Performance
- Memory usage: ___ MB
- CPU usage: ___ %
- Stable after 10+ queries: [ ] YES / [ ] NO
- Notes: ___

## Issues Found
1. ___
2. ___

## Recommendations
1. ___
2. ___
```

---

## ⏭️ Next Steps After Testing

Once MCP Inspector testing is complete:

1. **Document Results**: Fill in the test results template
2. **Fix Any Issues**: Address problems found
3. **Re-test**: Verify fixes work
4. **Enable Authentication**: Set `ENABLE_AUTH=True`
5. **Move to Claude Desktop**: Follow `CLAUDE_DESKTOP_SETUP.md`

---

## 📚 References

- **MCP Inspector**: https://github.com/modelcontextprotocol/inspector
- **MCP Specification**: https://modelcontextprotocol.io/
- **FastMCP**: https://github.com/jlowin/fastmcp

---

**Ready to test?** Let's launch MCP Inspector! 🚀
