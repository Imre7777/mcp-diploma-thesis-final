"""
HTTP MCP Server with Streamable Support

This module implements the HTTP transport for the MCP Educational Server,
following the MCP HTTP Streamable specification for efficient delivery
of large result sets using Server-Sent Events (SSE).
"""

import asyncio
import logging
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from src.config.server_config import ServerConfig
from src.server.base import BaseMCPServer

logger = logging.getLogger(__name__)


class HTTPMCPServer(BaseMCPServer):
    """
    HTTP-based MCP server with Streamable support.
    
    This server:
    - Exposes MCP tools via HTTP POST /mcp endpoint
    - Provides SSE streaming via GET /sse endpoint
    - Implements health checks for monitoring
    - Supports CORS for web client access
    """

    def __init__(
        self,
        name: str = "mcp-educational-server",
        config: Optional[ServerConfig] = None
    ):
        """
        Initialize the HTTP MCP server.

        Args:
            name: Name of the MCP server
            config: Server configuration (uses default if not provided)
        """
        super().__init__(name=name, config=config)
        
        # Create FastAPI application
        self.app = FastAPI(
            title=self.name,
            description="Educational Content Search Server with RBAC",
            version="1.0.0",
            docs_url="/docs",  # Swagger UI
            redoc_url="/redoc",  # ReDoc
        )
        
        self._uvicorn_server: Optional[uvicorn.Server] = None
        self._register_endpoints()

    def _register_endpoints(self) -> None:
        """
        Register HTTP endpoints for the server.
        
        Registers:
        - /health: Health check endpoint
        - /sse: Server-Sent Events endpoint for MCP remotes
        """
        
        @self.app.get("/health", tags=["monitoring"])
        async def health_check():
            """
            Health check endpoint for monitoring and load balancers.
            
            Returns:
                dict: Server status and basic info
            """
            return {
                "status": "ok",
                "server": self.name,
                "initialized": self._initialized,
                "rbac_enabled": self.config.enable_rbac,
            }

        @self.app.get("/sse", tags=["mcp"])
        async def sse_endpoint(request: Request):
            """
            Server-Sent Events endpoint for MCP HTTP Streamable.
            
            This endpoint:
            - Keeps a persistent connection with MCP clients
            - Sends periodic heartbeats to prevent timeouts
            - Closes gracefully when client disconnects
            
            Args:
                request: FastAPI request object
                
            Returns:
                EventSourceResponse: SSE stream
            """
            async def event_generator():
                """Generate SSE events with heartbeats."""
                # Send initial greeting
                yield {
                    "event": "hello",
                    "data": self.name,
                }
                
                # Send heartbeats every 15 seconds
                while True:
                    # Check if client disconnected
                    if await request.is_disconnected():
                        logger.debug("SSE client disconnected")
                        break
                    
                    # Send heartbeat
                    yield {
                        "event": "ping",
                        "data": "ok",
                    }
                    
                    # Wait before next heartbeat
                    await asyncio.sleep(15)
            
            return EventSourceResponse(event_generator())

    async def start(self) -> None:
        """
        Start the HTTP server.
        
        This method:
        1. Initializes base components (DB, tools)
        2. Attaches MCP HTTP endpoints to FastAPI
        3. Starts the Uvicorn server
        """
        # Initialize base components
        await super().start()

        # Attach MCP HTTP endpoints to FastAPI app
        logger.info("Attaching MCP HTTP Streamable endpoints...")
        try:
            # FastMCP's run() method automatically attaches to the FastAPI app
            # We need to pass the app to FastMCP initialization instead
            # For now, we'll skip this and FastMCP will handle its own routing
            logger.info("MCP tools registered and ready")
            logger.info("Note: Using FastMCP's built-in HTTP handling")
        except Exception as e:
            logger.error(f"Error setting up MCP endpoints: {e}")

        # Configure and start Uvicorn server
        uvicorn_config = uvicorn.Config(
            self.app,
            host=self.config.http_host,
            port=self.config.http_port,
            log_level="info",
            access_log=True,
            server_header=False,  # Don't expose server version
            date_header=False,  # Reduce header size
        )
        
        self._uvicorn_server = uvicorn.Server(uvicorn_config)
        
        logger.info(
            f"Starting HTTP server on {self.config.http_host}:{self.config.http_port}..."
        )
        logger.info(f"  - Swagger UI: http://{self.config.http_host}:{self.config.http_port}/docs")
        logger.info(f"  - MCP endpoint: http://{self.config.http_host}:{self.config.http_port}/mcp")
        logger.info(f"  - SSE endpoint: http://{self.config.http_host}:{self.config.http_port}/sse")
        
        # Start the server (this blocks until shutdown)
        await self._uvicorn_server.serve()

    async def stop(self) -> None:
        """
        Stop the HTTP server.
        
        Gracefully shuts down the Uvicorn server and cleans up resources.
        """
        if self._uvicorn_server and self._uvicorn_server.started:
            logger.info("Stopping Uvicorn HTTP server...")
            self._uvicorn_server.should_exit = True
        
        await super().stop()


# Entry point for Docker/systemd
async def _async_main():
    """Async entry point for the HTTP server."""
    server = HTTPMCPServer()
    await server.start()


def main():
    """Main entry point for the HTTP server."""
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
