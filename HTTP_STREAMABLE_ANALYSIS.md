# 🌊 HTTP Streamable Implementation Analysis

**Date**: January 3, 2026  
**Priority**: VERY HIGH ⭐⭐⭐  
**Status**: NEEDS IMPLEMENTATION

---

## 🎯 Executive Summary

Your current MCP server uses an **older SSE implementation** that doesn't fully comply with the **new MCP HTTP Streamable specification**. This needs to be updated for your thesis to be current and professional.

### Current vs. New Standard

| Aspect | Current Implementation | New Standard (HTTP Streamable) |
|--------|----------------------|--------------------------------|
| Endpoint | `/mcp` (POST, JSON only) + `/sse` (separate) | `/http-mcp` (single endpoint) |
| POST Response | Always JSON | JSON OR SSE (based on Accept header) |
| SSE | Global event bus (broadcast) | Per-request SSE stream |
| Accept Header | Not checked | Must accept `application/json, text/event-stream` |
| GET Endpoint | N/A | Optional: SSE stream or 405 |
| Compliance | Partial (older spec) | **Full (new spec)** ✅ |

---

## 📊 Analysis of Current Implementation

### What You Have (Working but Outdated)

**File: `backup/mcp_vector_server/server/http_server.py`**

```python
# Current implementation (lines 66-125)
# THREE duplicate SSE implementations! 😱

# Version 1: Using sse-starlette (lines 82-100)
@app.get("/sse")
async def sse_endpoint(request: Request):
    async def gen():
        yield {"event": "hello", "data": "leowiki-mcp"}
        while True:
            if await request.is_disconnected():
                break
            yield {"event": "ping", "data": "ok"}
            await asyncio.sleep(15)
    return EventSourceResponse(gen())

# Version 2: Using StreamingResponse (lines 109-121)
@app.get("/sse")
async def sse(request: Request):
    async def gen():
        yield ":ok\n\n"
        while True:
            if await request.is_disconnected():
                break
            yield ":keepalive\n\n"
            await asyncio.sleep(15)
    return StreamingResponse(gen(), media_type="text/event-stream")

# Version 3: Global SSE bus in sse_bus.py
# Broadcasts to all connected clients
```

**Problems:**
1. ❌ Three duplicate SSE implementations (confusing!)
2. ❌ `/mcp` always returns JSON (no per-request SSE)
3. ❌ `/sse` is a global broadcast (not per-request)
4. ❌ Doesn't check `Accept` header
5. ❌ Not compliant with new MCP HTTP Streamable spec

---

## 🆕 New MCP HTTP Streamable Specification

### Key Requirements

Based on your previous analysis (from `mcp_streamable_doc.md`):

1. **Single Unified Endpoint**: `/http-mcp` (or similar name)

2. **POST Method**:
   - **Request**: Must include `Accept: application/json, text/event-stream`
   - **Response**: Server chooses JSON OR SSE based on:
     - Response size
     - Streaming needs
     - Client preferences
   - **Status Codes**:
     - `200 OK` - JSON response
     - `200 OK` - SSE stream started
     - `202 Accepted` - No response (async operation)
     - `406 Not Acceptable` - Missing/invalid Accept header

3. **GET Method** (Optional):
   - Return SSE stream for monitoring
   - OR return `405 Method Not Allowed`

4. **SSE Format**:
```
data: {"jsonrpc": "2.0", "id": 1, "result": {...}}

data: {"jsonrpc": "2.0", "id": 1, "result": {...}}

data: {"jsonrpc": "2.0", "id": 1, "result": {...}}
```

5. **Per-Request Streaming**:
   - Each POST can return its own SSE stream
   - NOT a global broadcast
   - Stream closes when response is complete

---

## 🏗️ Implementation Plan

### Phase 1: Extract RPC Handler (Clean Separation)

**File: `src/server/rpc_handler.py` (NEW)**

```python
"""
RPC Request Handler

Centralized handler for MCP RPC requests.
Used by both legacy /mcp endpoint and new /http-mcp endpoint.
"""

from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
import logging

logger = logging.getLogger(__name__)


async def handle_rpc_request(payload: Dict[str, Any], request: Request) -> Optional[Dict[str, Any]]:
    """
    Handle MCP RPC request (JSON-RPC 2.0).
    
    This is the core RPC dispatcher used by all MCP endpoints.
    
    Args:
        payload: JSON-RPC request payload
        request: FastAPI request object (for auth, etc.)
        
    Returns:
        JSON-RPC response dict, or None for notifications
        
    Raises:
        HTTPException: For invalid requests
        
    Example:
        Request:
        {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "vector_search",
                "arguments": {"query": "Python", "limit": 5}
            },
            "id": 1
        }
        
        Response:
        {
            "jsonrpc": "2.0",
            "result": {
                "content": [{"type": "text", "text": "[...]"}]
            },
            "id": 1
        }
    """
    try:
        # Validate JSON-RPC structure
        if payload.get("jsonrpc") != "2.0":
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON-RPC version (must be 2.0)"
            )
        
        method = payload.get("method")
        if not method:
            raise HTTPException(
                status_code=400,
                detail="Missing 'method' in request"
            )
        
        params = payload.get("params", {})
        request_id = payload.get("id")
        
        # Dispatch to appropriate handler
        if method == "tools/list":
            result = await handle_tools_list(params, request)
        elif method == "tools/call":
            result = await handle_tools_call(params, request)
        elif method == "resources/list":
            result = await handle_resources_list(params, request)
        elif method == "prompts/list":
            result = await handle_prompts_list(params, request)
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown method: {method}"
            )
        
        # If notification (no id), return None
        if request_id is None:
            return None
        
        # Build response
        response = {
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"RPC handler error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_tools_call(params: Dict, request: Request) -> Dict:
    """
    Handle tools/call method.
    
    This is where RBAC filtering happens!
    """
    # Extract user role from JWT (RBAC)
    from server.middleware import RBACMiddleware
    role = await RBACMiddleware.extract_user_role(request)
    
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    # Get tool function
    from tools import get_tool
    tool_func = get_tool(tool_name)
    
    if not tool_func:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
    
    # Add request and role to arguments (for RBAC)
    arguments["request"] = request
    arguments["user_role"] = role
    
    # Execute tool
    result = await tool_func(**arguments)
    
    # Wrap result in MCP format
    return {
        "content": [
            {"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}
        ]
    }


# ... other handlers (handle_tools_list, etc.)
```

---

### Phase 2: Keep Legacy Endpoint (Backward Compatibility)

**File: `src/server/legacy_endpoints.py` (NEW)**

```python
"""
Legacy MCP Endpoints

Maintains backward compatibility with older MCP clients.
These endpoints use the old SSE broadcast model.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
import asyncio

from .rpc_handler import handle_rpc_request
from .sse_bus import sse_bus

router = APIRouter()


@router.post("/mcp")
async def mcp_legacy_post(request: Request):
    """
    Legacy MCP endpoint (always returns JSON).
    
    This endpoint is kept for backward compatibility.
    Also publishes responses to the global SSE bus.
    """
    payload = await request.json()
    
    # Use shared RPC handler
    response = await handle_rpc_request(payload, request)
    
    if response is None:
        # Notification (no response expected)
        return Response(status_code=204)
    
    # Publish to SSE bus for legacy clients listening on /sse
    asyncio.create_task(sse_bus.publish(response, event="message"))
    
    return JSONResponse(response)


@router.get("/sse")
async def sse_legacy_get(request: Request):
    """
    Legacy SSE endpoint (global broadcast).
    
    This is a global event bus that broadcasts to all connected clients.
    Kept for backward compatibility with mcp-remote.
    """
    from starlette.responses import StreamingResponse
    
    async def event_generator():
        # Send initial comment
        yield ":ok\n\n"
        
        # Subscribe to SSE bus
        queue = await sse_bus.subscribe()
        
        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                
                # Wait for message with timeout (for heartbeats)
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield ":keepalive\n\n"
        finally:
            await sse_bus.unsubscribe(queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
```

---

### Phase 3: New HTTP Streamable Endpoint (Compliant)

**File: `src/server/streamable_http.py` (NEW)** ⭐

```python
"""
MCP HTTP Streamable Endpoint

Implements the new MCP HTTP Streamable specification.
Supports both JSON and SSE responses based on Accept header.

Specification:
- Single endpoint for POST and GET
- POST returns JSON OR SSE based on Accept header
- Per-request SSE streams (not global broadcast)
- Compliant with MCP HTTP Streamable spec
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, Response, StreamingResponse
import asyncio
import json
import logging

from .rpc_handler import handle_rpc_request

logger = logging.getLogger(__name__)

router = APIRouter()

# Endpoint path (configurable)
HTTP_MCP_ENDPOINT = "/http-mcp"


@router.post(HTTP_MCP_ENDPOINT)
async def http_mcp_post(request: Request):
    """
    MCP HTTP Streamable POST endpoint.
    
    This endpoint complies with the new MCP HTTP Streamable specification.
    It can return either JSON or SSE based on the Accept header and response size.
    
    Request Headers:
        Accept: application/json, text/event-stream (REQUIRED)
        Authorization: Bearer <JWT> (REQUIRED for RBAC)
        
    Response:
        - JSON response (200 OK) for small/simple results
        - SSE stream (200 OK) for large/streamed results
        - 202 Accepted for notifications (no response)
        - 406 Not Acceptable for invalid Accept header
        
    Example:
        POST /http-mcp
        Accept: application/json, text/event-stream
        Authorization: Bearer eyJ...
        
        {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "vector_search",
                "arguments": {"query": "Python", "limit": 50}
            },
            "id": 1
        }
        
        Response (SSE if large):
        data: {"jsonrpc":"2.0","id":1,"result":{"content":[...]}}
        
        OR Response (JSON if small):
        {"jsonrpc":"2.0","id":1,"result":{"content":[...]}}
    """
    # 1. Validate Accept header
    accept_header = request.headers.get("accept", "")
    
    if not accept_header:
        raise HTTPException(
            status_code=406,
            detail="Missing Accept header. Must include: application/json, text/event-stream"
        )
    
    accepts_json = "application/json" in accept_header
    accepts_sse = "text/event-stream" in accept_header
    
    if not (accepts_json and accepts_sse):
        raise HTTPException(
            status_code=406,
            detail="Accept header must include both: application/json, text/event-stream"
        )
    
    # 2. Parse request
    try:
        payload = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    
    # 3. Handle RPC request
    response = await handle_rpc_request(payload, request)
    
    if response is None:
        # Notification (no response expected)
        return Response(status_code=202)
    
    # 4. Decide: JSON or SSE?
    # Decision criteria:
    # - Small responses (< 10KB): JSON
    # - Large responses (>= 10KB): SSE
    # - Streaming tools: Always SSE
    
    response_size = len(json.dumps(response))
    use_sse = response_size >= 10_000  # 10KB threshold
    
    # Check if this is a streaming tool
    method = payload.get("method")
    tool_name = payload.get("params", {}).get("name", "")
    streaming_tools = ["vector_search", "faceted_search", "scroll"]
    
    if tool_name in streaming_tools:
        use_sse = True
    
    # 5. Return response
    if use_sse:
        # Return SSE stream
        logger.info(f"Returning SSE stream for request {payload.get('id')}")
        return await stream_sse_response(response, request)
    else:
        # Return JSON
        logger.info(f"Returning JSON for request {payload.get('id')}")
        return JSONResponse(response)


async def stream_sse_response(response: dict, request: Request) -> StreamingResponse:
    """
    Stream a single response as SSE.
    
    This is a per-request SSE stream (not a global broadcast).
    The stream closes after sending the response.
    
    Args:
        response: JSON-RPC response dict
        request: FastAPI request (to detect disconnect)
        
    Returns:
        StreamingResponse with text/event-stream
    """
    async def event_generator():
        # Check if client disconnected
        if await request.is_disconnected():
            return
        
        # Send response as SSE event
        data = json.dumps(response, ensure_ascii=False)
        yield f"data: {data}\n\n"
        
        # Stream is complete (close connection)
        # Client should see connection close after receiving the event
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "close"  # Close after sending
        }
    )


@router.get(HTTP_MCP_ENDPOINT)
async def http_mcp_get(request: Request):
    """
    MCP HTTP Streamable GET endpoint (optional).
    
    Options:
    1. Return 405 Method Not Allowed (simple)
    2. Return monitoring SSE stream (advanced)
    
    We choose option 1 for simplicity.
    """
    raise HTTPException(
        status_code=405,
        detail="Method Not Allowed. Use POST for MCP requests."
    )
```

---

### Phase 4: Integration

**File: `src/server/http_server.py` (UPDATED)**

```python
"""
HTTP MCP Server

Updated to support:
1. Legacy endpoints (/mcp, /sse) - backward compatibility
2. New HTTP Streamable endpoint (/http-mcp) - new standard
"""

import asyncio
import logging
from fastapi import FastAPI
import uvicorn

from config.server_config import ServerConfig
from server.base import BaseMCPServer

# Import endpoint routers
from .legacy_endpoints import router as legacy_router
from .streamable_http import router as streamable_router

logger = logging.getLogger(__name__)


class HTTPMCPServer(BaseMCPServer):
    def __init__(self, config: ServerConfig | None = None):
        super().__init__(name="leowiki-vector-server", config=config or ServerConfig())
        self.app = FastAPI(
            title="MCP Educational Server",
            description="Model Context Protocol server with RBAC",
            version="2.0.0"
        )
        self._uvicorn_server: uvicorn.Server | None = None
        
        # Register routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Register all endpoint routers."""
        
        # 1. Legacy endpoints (backward compatibility)
        self.app.include_router(
            legacy_router,
            tags=["Legacy"]
        )
        
        # 2. NEW: HTTP Streamable endpoint ⭐
        self.app.include_router(
            streamable_router,
            tags=["HTTP Streamable"]
        )
        
        # 3. Health check
        @self.app.get("/health")
        async def health():
            """Health check endpoint."""
            return {
                "status": "ok",
                "version": "2.0.0",
                "endpoints": {
                    "legacy": ["/mcp", "/sse"],
                    "streamable": ["/http-mcp"]
                }
            }
    
    async def start(self) -> None:
        """Start HTTP server."""
        # Initialize base components (DB, embeddings, tools)
        await super().start()
        
        # Start uvicorn
        config = uvicorn.Config(
            self.app,
            host=self.config.http_host,
            port=self.config.http_port,
            log_level="info",
        )
        self._uvicorn_server = uvicorn.Server(config)
        logger.info("Starting HTTP MCP server with HTTP Streamable support...")
        await self._uvicorn_server.serve()
    
    async def stop(self) -> None:
        """Stop HTTP server."""
        await super().stop()
        if self._uvicorn_server and self._uvicorn_server.started:
            logger.info("Stopping HTTP server...")
            self._uvicorn_server.should_exit = True
```

---

### Phase 5: Update Caddyfile

**File: `Caddyfile` (UPDATED)**

```caddyfile
leowiki-mcp.stream {
    tls imre.obermueller@gmail.com
    
    # OAuth endpoints (public)
    handle /oauth/* {
        reverse_proxy http://leowiki-mcp:8000
    }
    
    # NEW: HTTP Streamable endpoint (requires JWT)
    @httpMcp {
        path /http-mcp*
        header Authorization Bearer*
    }
    
    handle @httpMcp {
        header Cache-Control "no-cache"
        header X-Accel-Buffering "no"
        reverse_proxy http://leowiki-mcp:8080
    }
    
    # Legacy MCP endpoints (backward compatibility)
    @legacy {
        path /mcp* /sse*
        header Authorization Bearer*
    }
    
    handle @legacy {
        header Cache-Control "no-cache"
        header X-Accel-Buffering "no"
        reverse_proxy http://leowiki-mcp:8080
    }
    
    # Health check (public)
    handle /health {
        reverse_proxy http://leowiki-mcp:8080
    }
    
    # Redirect to login if no token
    handle {
        redir /oauth/login
    }
    
    log {
        output file /var/log/caddy/access.log
    }
}
```

---

## 🧪 Testing HTTP Streamable

### Test 1: POST with JSON response (small result)

```bash
curl -X POST http://localhost:8080/http-mcp \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "ping",
      "arguments": {}
    },
    "id": 1
  }'
```

Expected response (JSON):
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [{"type": "text", "text": "{\"status\": \"ok\"}"}]
  },
  "id": 1
}
```

### Test 2: POST with SSE response (large result)

```bash
curl -X POST http://localhost:8080/http-mcp \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "vector_search",
      "arguments": {"query": "Python", "limit": 50}
    },
    "id": 1
  }'
```

Expected response (SSE):
```
data: {"jsonrpc":"2.0","id":1,"result":{"content":[...]}}

[connection closes]
```

### Test 3: GET (should return 405)

```bash
curl -X GET http://localhost:8080/http-mcp
```

Expected:
```json
{
  "detail": "Method Not Allowed. Use POST for MCP requests."
}
```

---

## 📋 Implementation Checklist

### Phase 1: Preparation
- [ ] Extract RPC handler to `rpc_handler.py`
- [ ] Test that extraction doesn't break existing functionality
- [ ] Add comprehensive logging

### Phase 2: Legacy Endpoints
- [ ] Move `/mcp` and `/sse` to `legacy_endpoints.py`
- [ ] Ensure they still use global SSE bus
- [ ] Test backward compatibility

### Phase 3: HTTP Streamable
- [ ] Create `streamable_http.py` with new `/http-mcp` endpoint
- [ ] Implement Accept header validation
- [ ] Implement JSON/SSE decision logic
- [ ] Implement per-request SSE streaming
- [ ] Test with curl

### Phase 4: Integration
- [ ] Update `http_server.py` to register both routers
- [ ] Update health endpoint to show both endpoint types
- [ ] Update Caddyfile
- [ ] Test all endpoints

### Phase 5: Documentation
- [ ] Document new endpoint in README
- [ ] Add examples for clients
- [ ] Update API documentation

---

## 🎓 Thesis Benefits

Adding HTTP Streamable support provides:

1. **Modern Standard Compliance** ⭐
   - Your thesis uses the latest MCP specification
   - Demonstrates understanding of protocol evolution

2. **Performance Optimization**
   - Small responses: JSON (lower latency)
   - Large responses: SSE (progressive loading)

3. **Backward Compatibility**
   - Old clients still work with `/mcp` + `/sse`
   - New clients use `/http-mcp`
   - Smooth migration path

4. **Professional Quality**
   - Shows awareness of current standards
   - Production-ready implementation
   - Well-documented code

---

## ⏱️ Implementation Time

| Phase | Time Estimate |
|-------|---------------|
| Phase 1: Extract RPC handler | 2 hours |
| Phase 2: Legacy endpoints | 2 hours |
| Phase 3: HTTP Streamable | 4 hours |
| Phase 4: Integration | 2 hours |
| Phase 5: Testing | 2 hours |
| **Total** | **12 hours** (1.5 days) |

---

## 🚀 Priority

**Add this to Week 1 or 2** of the refactoring plan.

Recommended: **Week 1, Day 4-5** (after code cleanup, before RBAC implementation)

This ensures your server is standards-compliant before adding RBAC functionality.

---

## 📝 Summary

Your current server has:
- ✅ Working SSE (but old implementation)
- ✅ Global SSE bus
- ❌ Not compliant with new HTTP Streamable spec

You need to add:
- ⭐ New `/http-mcp` endpoint
- ⭐ Accept header validation
- ⭐ Per-request SSE streaming
- ⭐ JSON/SSE decision logic
- ⭐ Keep legacy endpoints for compatibility

**This is important for your thesis to be current and professional!** 🎓
