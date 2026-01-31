#!/usr/bin/env python3
"""
Test script to simulate Claude Desktop connecting to MCP server
"""
import requests
import json

MCP_URL = "https://leowiki-mcp.stream/mcp/"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream"
}

def test_mcp_connection():
    print("=" * 60)
    print("Testing MCP Server Connection")
    print("URL:", MCP_URL)
    print("=" * 60)
    
    # Test 1: Initialize
    print("\n1. Testing initialize...")
    init_request = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {"listChanged": True}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        },
        "id": 1
    }
    
    response = requests.post(MCP_URL, json=init_request, headers=HEADERS)
    if response.status_code == 200:
        print("   ✅ Initialize successful")
        data = response.text
        if "data: " in data:
            json_data = data.split("data: ")[1].strip()
            result = json.loads(json_data)
            server_info = result.get("result", {}).get("serverInfo", {})
            print(f"   Server: {server_info.get('name')} v{server_info.get('version')}")
    else:
        print(f"   ❌ Initialize failed: {response.status_code}")
        return False
    
    # Test 2: List Tools
    print("\n2. Testing tools/list...")
    tools_request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 2
    }
    
    response = requests.post(MCP_URL, json=tools_request, headers=HEADERS)
    if response.status_code == 200:
        print("   ✅ Tools list successful")
        data = response.text
        if "data: " in data:
            json_data = data.split("data: ")[1].strip()
            result = json.loads(json_data)
            tools = result.get("result", {}).get("tools", [])
            print(f"   Found {len(tools)} tools:")
            for tool in tools:
                print(f"      - {tool['name']}: {tool['description']}")
    else:
        print(f"   ❌ Tools list failed: {response.status_code}")
        return False
    
    # Test 3: Call a tool
    print("\n3. Testing tool call (health_check)...")
    call_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "health_check",
            "arguments": {}
        },
        "id": 3
    }
    
    response = requests.post(MCP_URL, json=call_request, headers=HEADERS)
    if response.status_code == 200:
        print("   ✅ Tool call successful")
        data = response.text
        if "data: " in data:
            json_data = data.split("data: ")[1].strip()
            result = json.loads(json_data)
            print("   Response received")
    else:
        print(f"   ❌ Tool call failed: {response.status_code}")
        return False
    
    # Test 4: Test search_content (if database has data)
    print("\n4. Testing tool call (search_content)...")
    search_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "search_content",
            "arguments": {
                "query": "test",
                "limit": 3
            }
        },
        "id": 4
    }
    
    response = requests.post(MCP_URL, json=search_request, headers=HEADERS)
    if response.status_code == 200:
        print("   ✅ Search tool call successful")
        data = response.text
        if "data: " in data:
            json_data = data.split("data: ")[1].strip()
            result = json.loads(json_data)
            print("   Search response received")
    else:
        print(f"   ❌ Search tool call failed: {response.status_code}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nYour colleague can now add this in Claude Desktop:")
    print("   Settings → Connectors → Add custom connector")
    print(f"   URL: {MCP_URL.rstrip('/')}")
    print("\n" + "=" * 60)
    return True

if __name__ == "__main__":
    try:
        test_mcp_connection()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
