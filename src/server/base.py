"""
Base MCP Server Implementation

This module provides the base class for the MCP Educational Server with shared
functionality for initialization, dependency management, and tool registration.
"""

import asyncio
import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP

from src.backends import create_vector_backend
from src.config.server_config import ServerConfig
from src.utils.embeddings import create_embedding_service

logger = logging.getLogger(__name__)


class BaseMCPServer:
    """
    Base class for MCP Educational Server with shared functionality.
    
    This class provides:
    - Server initialization and lifecycle management
    - Vector database connection
    - Tool registration with RBAC support
    - Configuration management
    """

    def __init__(
        self,
        name: str = "mcp-educational-server",
        config: Optional[ServerConfig] = None
    ):
        """
        Initialize the base MCP server.

        Args:
            name: Name of the MCP server
            config: Server configuration (uses default if not provided)
        """
        self.name = name
        self.config = config or ServerConfig()
        self.mcp: Optional[FastMCP] = None
        self.db: Optional[any] = None
        self.embedding_service: Optional[any] = None
        self._shutdown_event = asyncio.Event()
        self._initialized = False
        
        logger.info(f"Initializing {self.name}...")

    async def initialize(self) -> None:
        """
        Initialize shared components.

        This method:
        1. Creates the FastMCP instance
        2. Initializes the vector database connection
        3. Registers all MCP tools with RBAC filters
        
        Must be called before starting the server.
        
        Raises:
            Exception: If initialization fails
        """
        if self._initialized:
            logger.warning("Server already initialized")
            return

        try:
            logger.info(f"Initializing {self.name}...")

            # Create FastMCP instance
            self.mcp = FastMCP(
                name=self.name,
                instructions=(
                    "Educational content search server with role-based access control. "
                    "Provides semantic search over educational materials with filtering "
                    "by access level (public, student, teacher, admin), content type, "
                    "freshness, and namespace."
                ),
            )

            # Create shared dependencies
            self._create_dependencies()

            # Register all tools (to be implemented in subclasses or via composition)
            await self._register_tools()

            self._initialized = True
            logger.info(f"{self.name} initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize {self.name}: {e}", exc_info=True)
            raise

    def _create_dependencies(self) -> None:
        """
        Create database and other service dependencies.
        
        Creates:
        - Vector database backend (Qdrant)
        - Embedding service (OpenAI or mock)
        """
        try:
            logger.info("Creating vector database backend...")
            self.db = create_vector_backend(
                name=self.config.vector_db_backend,
                url=self.config.vector_db_url,
                api_key=self.config.vector_db_api_key,
            )
            logger.info(f"Vector database backend created: {self.config.vector_db_backend}")
            
            logger.info("Creating embedding service...")
            self.embedding_service = create_embedding_service(
                model=self.config.embedding_model,
                dimensions=self.config.vector_dimensions,
                api_key=None,  # Will use OPENAI_API_KEY environment variable
            )
            if self.embedding_service.is_using_mock:
                logger.warning(
                    "⚠️  Using mock embeddings (no API key). "
                    "Set OPENAI_API_KEY environment variable for real search."
                )
            else:
                logger.info("✅ Embedding service ready (OpenAI API)")

        except Exception as e:
            logger.error(f"Failed to create dependencies: {e}", exc_info=True)
            raise

    async def _register_tools(self) -> None:
        """
        Register all MCP tools.
        
        Registers all available tools with RBAC filtering support.
        """
        try:
            from src.tools import register_all_tools
            
            logger.info("Registering MCP tools...")
            register_all_tools(self.mcp, self.db, self.embedding_service, self.config)
            logger.info("Tools registered successfully")
            
        except Exception as e:
            logger.error(f"Failed to register tools: {e}", exc_info=True)
            raise

    async def start(self) -> None:
        """
        Start the server.
        
        This method calls initialize() and prepares the server to handle requests.
        Subclasses should override this to add protocol-specific startup logic.
        """
        await self.initialize()

    async def stop(self) -> None:
        """
        Stop the server and clean up resources.
        """
        logger.info(f"Stopping {self.name}...")
        self._shutdown_event.set()
        await self.cleanup()

    async def cleanup(self) -> None:
        """
        Clean up server resources.
        
        Closes database connections and releases any held resources.
        """
        try:
            logger.info("Cleaning up server resources...")
            
            # Close database connection
            if self.db:
                try:
                    # Note: Qdrant client doesn't have explicit close in sync mode
                    # but we can set to None for cleanup
                    self.db = None
                    logger.info("Database connection cleaned up")
                except Exception as e:
                    logger.error(f"Error closing database: {e}")

            self._initialized = False
            logger.info("Server cleanup complete")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)
