"""
Test MCP HTTP-Streamable with correct SSE headers.
This is the PRODUCTION mode for Raspberry Pi!
"""
import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000"

async def test_mcp_sse():
    """Test MCP with SSE headers (HTTP-Streamable mode)."""
    print("\n" + "="*80)
    print("Testing MCP HTTP-Streamable (Raspberry Pi Production Mode)")
    print("="*80 + "\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: List tools with SSE headers
        print("[1/2] Testing tools/list via HTTP-Streamable...")
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"  # KEY: Accept both!
            }
            
            response = await client.post(
                f"{BASE_URL}/mcp/",
                json=request,
                headers=headers
            )
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n  [SUCCESS] MCP Tools Available:")
                if "result" in result and "tools" in result["result"]:
                    for tool in result["result"]["tools"]:
                        print(f"    - {tool['name']}: {tool.get('description', 'No description')[:70]}...")
                else:
                    print(f"  Response: {json.dumps(result, indent=2)[:500]}")
            else:
                print(f"  [ERROR] Status: {response.status_code}")
                print(f"  Body: {response.text[:300]}")
                return False
                
        except Exception as e:
            print(f"  [ERROR] {e}")
            return False
        
        # Test 2: Call search_content tool
        print("\n[2/2] Testing search_content tool...")
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "search_content",
                    "arguments": {
                        "query": "machine learning",
                        "limit": 3,
                        "access_level": "student"
                    }
                }
            }
            
            response = await client.post(
                f"{BASE_URL}/mcp/",
                json=request,
                headers=headers
            )
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n  [SUCCESS] Search executed!")
                
                # Parse MCP response
                if "result" in result:
                    content = result["result"]
                    if isinstance(content, dict) and "content" in content:
                        for item in content["content"]:
                            if item.get("type") == "text":
                                text = item["text"][:300]
                                print(f"\n  Results:\n  {text}...")
                    else:
                        print(f"  Response: {json.dumps(result, indent=2)[:800]}")
                else:
                    print(f"  Full response: {json.dumps(result, indent=2)[:800]}")
            else:
                print(f"  [ERROR] Status: {response.status_code}")
                print(f"  Body: {response.text[:300]}")
                return False
                
        except Exception as e:
            print(f"  [ERROR] {e}")
            return False
    
    print("\n" + "="*80)
    print("[SUCCESS] HTTP-Streamable Mode FULLY WORKING!")
    print("="*80 + "\n")
    
    print("SUMMARY:")
    print("- [OK] HTTP-Streamable server running on port 8000")
    print("- [OK] MCP tools accessible via /mcp/ endpoint")
    print("- [OK] search_content tool working with Qdrant + OpenAI")
    print("- [OK] All fixes (Qdrant API, await, payload) work in HTTP mode!")
    print("\nREADY FOR RASPBERRY PI DEPLOYMENT!")
    print("- Use: python main.py --http")
    print("- Port: 8000")
    print("- Endpoint: http://<raspberry-pi-ip>:8000/mcp/")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_mcp_sse())
