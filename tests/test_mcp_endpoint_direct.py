"""
Direct test of /mcp endpoint for HTTP-Streamable mode.
"""
import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000"

async def test_mcp_direct():
    """Test the /mcp endpoint directly."""
    print("\n" + "="*80)
    print("Testing /mcp Endpoint (HTTP-Streamable for Raspberry Pi)")
    print("="*80 + "\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: GET /mcp (should return MCP server info or 405)
        print("[1/4] Testing GET /mcp...")
        try:
            response = await client.get(f"{BASE_URL}/mcp")
            print(f"  Status: {response.status_code}")
            print(f"  Headers: {dict(response.headers)}")
            if response.status_code == 200:
                print(f"  Body: {response.text[:500]}")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Test 2: GET /mcp/ (with trailing slash)
        print("\n[2/4] Testing GET /mcp/...")
        try:
            response = await client.get(f"{BASE_URL}/mcp/")
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print(f"  Body: {response.text[:500]}")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Test 3: POST /mcp with MCP protocol message
        print("\n[3/4] Testing POST /mcp (MCP tools/list)...")
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
            
            response = await client.post(
                f"{BASE_URL}/mcp",
                json=request,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"  [SUCCESS] Response: {json.dumps(result, indent=2)[:800]}")
            else:
                print(f"  Body: {response.text[:300]}")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Test 4: POST /mcp/ with trailing slash
        print("\n[4/4] Testing POST /mcp/ (with trailing slash)...")
        try:
            response = await client.post(
                f"{BASE_URL}/mcp/",
                json=request,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"  [SUCCESS] Response: {json.dumps(result, indent=2)[:800]}")
            else:
                print(f"  Body: {response.text[:300]}")
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n" + "="*80)
    print("Test Complete")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_mcp_direct())
