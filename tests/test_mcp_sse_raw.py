"""
Test MCP HTTP-Streamable and show raw response.
"""
import httpx
import asyncio

BASE_URL = "http://localhost:8000"

async def test_mcp_raw():
    """Test MCP and show raw response."""
    print("\n" + "="*80)
    print("Testing MCP HTTP-Streamable - Raw Response")
    print("="*80 + "\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        
        response = await client.post(
            f"{BASE_URL}/mcp/",
            json=request,
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"\nRaw Response ({len(response.content)} bytes):")
        print("-" * 80)
        print(response.text[:2000])
        print("-" * 80)

if __name__ == "__main__":
    asyncio.run(test_mcp_raw())
