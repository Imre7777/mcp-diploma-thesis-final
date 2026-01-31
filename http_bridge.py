#!/usr/bin/env python3
"""
HTTP-to-STDIO Bridge for MCP Servers
Allows Claude Desktop to connect to remote HTTP MCP servers

Usage in Claude Desktop config:
{
  "mcpServers": {
    "leowiki-mcp": {
      "command": "python",
      "args": ["path/to/http_bridge.py"],
      "env": {
        "MCP_SERVER_URL": "https://leowiki-mcp.stream/mcp"
      }
    }
  }
}

Author: HTL Leonding MCP Diploma Thesis
Date: January 2026
"""

import sys
import json
import os
import requests
from urllib.parse import urljoin

# Get MCP server URL from environment variable (with trailing slash for SSE)
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "https://leowiki-mcp.stream/mcp/").rstrip('/') + '/'

def log_error(message):
    """Log errors to stderr for Claude Desktop logs"""
    print(f"[HTTP Bridge Error] {message}", file=sys.stderr, flush=True)

def main():
    """
    Forward STDIO messages to HTTP MCP server and return responses.
    
    This bridge:
    1. Reads JSON-RPC messages from stdin (from Claude Desktop)
    2. Forwards them to the HTTP MCP server
    3. Returns responses to stdout (back to Claude Desktop)
    """
    log_error(f"HTTP Bridge starting... Connecting to: {MCP_SERVER_URL}")
    
    try:
        # Test server connectivity on startup
        response = requests.get(MCP_SERVER_URL.replace("/mcp", "/health"), timeout=5)
        log_error(f"Server health check: {response.status_code}")
    except Exception as e:
        log_error(f"Warning: Could not connect to server: {e}")
    
    # Process stdin line by line
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
            
        try:
            # Parse incoming JSON-RPC request
            request = json.loads(line)
            
            log_error(f"Forwarding request: {request.get('method', 'unknown')} (id: {request.get('id')})")
            
            # Forward to HTTP MCP server (with SSE support)
            response = requests.post(
                MCP_SERVER_URL,
                json=request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"  # SSE support
                },
                timeout=30,
                stream=True  # Enable streaming for SSE
            )
            
            # Check HTTP status
            if response.status_code != 200:
                log_error(f"HTTP error {response.status_code}: {response.text}")
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32000,
                        "message": f"HTTP {response.status_code}: {response.text[:100]}"
                    },
                    "id": request.get("id")
                }
                print(json.dumps(error_response), flush=True)
                continue
            
            # Parse SSE response (Server-Sent Events format)
            # Format: "event: message\ndata: {...}\n\n"
            response_text = response.text
            
            # Extract JSON from SSE format
            if "data: " in response_text:
                for line in response_text.split('\n'):
                    if line.startswith('data: '):
                        json_data = line[6:]  # Remove "data: " prefix
                        response_json = json.loads(json_data)
                        print(json.dumps(response_json), flush=True)
                        log_error(f"Response sent for id: {request.get('id')}")
                        break
            else:
                # Fallback to regular JSON
                response_json = response.json()
                print(json.dumps(response_json), flush=True)
                log_error(f"Response sent for id: {request.get('id')}")
            
        except json.JSONDecodeError as e:
            log_error(f"JSON decode error: {e}")
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                },
                "id": None
            }
            print(json.dumps(error_response), flush=True)
            
        except requests.RequestException as e:
            log_error(f"Network error: {e}")
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32000,
                    "message": f"Network error: {str(e)}"
                },
                "id": request.get("id") if 'request' in locals() else None
            }
            print(json.dumps(error_response), flush=True)
            
        except Exception as e:
            log_error(f"Unexpected error: {e}")
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                },
                "id": request.get("id") if 'request' in locals() else None
            }
            print(json.dumps(error_response), flush=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_error("Bridge interrupted by user")
        sys.exit(0)
    except Exception as e:
        log_error(f"Fatal error: {e}")
        sys.exit(1)
