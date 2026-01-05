"""
Main Entry Point for MCP Educational Server

This is the unified entry point for the MCP Educational Server,
supporting HTTP transport with optional future stdio transport support.

Usage:
    python main.py                    # Start HTTP server (default)
    python main.py --host 0.0.0.0     # Bind to all interfaces
    python main.py --port 8080        # Custom port
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(__file__).rsplit('\\', 1)[0])

from src.config.server_config import ServerConfig
from src.server import HTTPMCPServer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class ServerManager:
    """
    Manages the lifecycle of the MCP server.
    
    Handles:
    - Server initialization
    - Signal handling (SIGINT, SIGTERM)
    - Graceful shutdown
    """

    def __init__(self, config: ServerConfig):
        """
        Initialize the server manager.

        Args:
            config: Server configuration
        """
        self.config = config
        self.server: Optional[HTTPMCPServer] = None
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """
        Start the MCP server.
        
        This method:
        1. Creates the server instance
        2. Sets up signal handlers
        3. Starts the server
        4. Waits for shutdown signal
        """
        try:
            logger.info("=" * 70)
            logger.info("Starting MCP Educational Server")
            logger.info("=" * 70)
            logger.info(f"Configuration:")
            logger.info(f"  - Host: {self.config.http_host}")
            logger.info(f"  - Port: {self.config.http_port}")
            logger.info(f"  - Vector DB: {self.config.vector_db_url}")
            logger.info(f"  - Collection: {self.config.default_collection}")
            logger.info(f"  - RBAC Enabled: {self.config.enable_rbac}")
            logger.info("=" * 70)

            # Create server
            self.server = HTTPMCPServer(config=self.config)

            # Setup signal handlers
            self._setup_signal_handlers()

            # Start server (this will block until shutdown)
            await self.server.start()

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
            sys.exit(1)
        finally:
            await self.stop()

    async def stop(self) -> None:
        """
        Stop the server gracefully.
        """
        logger.info("Shutting down server...")
        self._shutdown_event.set()
        
        if self.server:
            await self.server.stop()
        
        logger.info("Server stopped successfully")

    def _setup_signal_handlers(self) -> None:
        """
        Setup signal handlers for graceful shutdown.
        
        Handles SIGINT (Ctrl+C) and SIGTERM (Docker/systemd stop).
        """
        def signal_handler(signum, frame):
            """Handle shutdown signals."""
            logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """
    Main async entry point.
    """
    # Load configuration from environment
    try:
        config = ServerConfig()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Create and start server manager
    manager = ServerManager(config)
    await manager.start()


if __name__ == "__main__":
    # Run the server
    asyncio.run(main())
