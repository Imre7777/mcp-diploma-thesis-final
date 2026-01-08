#!/bin/bash
# MCP Server Connection Test Script
# For remote testers to verify connectivity before using Claude Desktop

echo "🧪 MCP Server Connection Test"
echo "================================"
echo ""
echo "Server: https://leowiki-mcp.stream"
echo "Date: $(date)"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Test 1: Basic connectivity
echo "Test 1: Basic Connectivity"
echo "----------------------------"
if curl -s -o /dev/null -w "%{http_code}" https://leowiki-mcp.stream/health | grep -q "200"; then
    echo -e "${GREEN}✅ PASS${NC} - Server is reachable"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ FAIL${NC} - Cannot reach server"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 2: Health Check
echo "Test 2: Health Check Endpoint"
echo "--------------------------------"
HEALTH_RESPONSE=$(curl -s https://leowiki-mcp.stream/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✅ PASS${NC} - Health check successful"
    echo "Response: $HEALTH_RESPONSE"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ FAIL${NC} - Health check failed"
    echo "Response: $HEALTH_RESPONSE"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 3: TLS Certificate
echo "Test 3: TLS Certificate"
echo "-------------------------"
CERT_INFO=$(echo | openssl s_client -connect leowiki-mcp.stream:443 -servername leowiki-mcp.stream 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ PASS${NC} - TLS certificate valid"
    echo "$CERT_INFO"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ FAIL${NC} - TLS certificate issue"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 4: OAuth Discovery
echo "Test 4: OAuth Discovery Endpoint"
echo "-----------------------------------"
OAUTH_RESPONSE=$(curl -s https://leowiki-mcp.stream/.well-known/oauth-protected-resource)
if echo "$OAUTH_RESPONSE" | grep -q "authorization_servers"; then
    echo -e "${GREEN}✅ PASS${NC} - OAuth discovery working"
    echo "$OAUTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$OAUTH_RESPONSE"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ FAIL${NC} - OAuth discovery failed"
    echo "Response: $OAUTH_RESPONSE"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 5: Authentication Required
echo "Test 5: Protected Endpoints (Should be 401)"
echo "----------------------------------------------"
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://leowiki-mcp.stream/mcp)
if [ "$STATUS_CODE" = "401" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Authentication correctly required (401 Unauthorized)"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}⚠️ WARNING${NC} - Expected 401, got $STATUS_CODE"
    echo "This might mean authentication is disabled or there's an issue"
fi
echo ""

# Test 6: API Documentation
echo "Test 6: API Documentation"
echo "---------------------------"
if curl -s https://leowiki-mcp.stream/docs | grep -q "swagger"; then
    echo -e "${GREEN}✅ PASS${NC} - API docs accessible at https://leowiki-mcp.stream/docs"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ FAIL${NC} - API docs not accessible"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 7: Scalekit Authorization Server
echo "Test 7: Scalekit Authorization Server"
echo "----------------------------------------"
if curl -s -o /dev/null -w "%{http_code}" https://mcpeduauth.scalekit.dev | grep -q "200\|301\|302"; then
    echo -e "${GREEN}✅ PASS${NC} - Scalekit auth server reachable"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ FAIL${NC} - Cannot reach Scalekit auth server"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 8: Network Latency
echo "Test 8: Network Latency"
echo "-------------------------"
PING_TIME=$(curl -s -o /dev/null -w "%{time_total}" https://leowiki-mcp.stream/health)
echo "Response time: ${PING_TIME}s"
if (( $(echo "$PING_TIME < 3.0" | bc -l) )); then
    echo -e "${GREEN}✅ PASS${NC} - Good latency (< 3s)"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}⚠️ WARNING${NC} - High latency (> 3s)"
    echo "Connection might be slow from your location"
fi
echo ""

# Summary
echo "================================"
echo "📊 TEST SUMMARY"
echo "================================"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo ""
    echo "✅ You're ready to configure Claude Desktop!"
    echo "📖 See: QUICK_START_REMOTE_TESTING.md"
    echo ""
    exit 0
else
    echo -e "${RED}⚠️ SOME TESTS FAILED${NC}"
    echo ""
    echo "Please contact the administrator:"
    echo "  Email: imre.obermueller@gmail.com"
    echo ""
    exit 1
fi
