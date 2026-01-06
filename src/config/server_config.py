"""
Unified server configuration for MCP Educational Content Server.

This module provides centralized configuration management using Pydantic settings,
supporting multiple transport protocols (stdio, HTTP, SSE) and integration with
Scalekit OAuth 2.1 for authentication and RBAC.
"""

import os
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get package directory for robust path resolution
PACKAGE_DIR = Path(__file__).resolve().parent.parent


class ServerConfig(BaseSettings):
    """
    Unified server configuration for MCP Educational Content Server.
    
    This configuration supports:
    - Multiple transport protocols (stdio, HTTP, both)
    - Scalekit OAuth 2.1 authentication
    - Qdrant vector database integration
    - Role-based access control (RBAC)
    - Performance and caching settings
    - Health monitoring and metrics
    """

    # ========================================================================
    # Transport Settings
    # ========================================================================
    transport: Literal["stdio", "http", "both"] = Field(
        "stdio",
        description="Transport protocol(s) to use: stdio for Claude Desktop, http for web API, both for dual mode"
    )

    # ========================================================================
    # HTTP Server Settings (used when transport includes "http")
    # ========================================================================
    http_host: str = Field(
        "0.0.0.0",
        description="HTTP server host address (0.0.0.0 = all interfaces)"
    )
    http_port: int = Field(
        8000,
        description="HTTP server port (default: 8000)"
    )
    http_enable_cors: bool = Field(
        True,
        description="Enable CORS for HTTP endpoints"
    )
    http_cors_origins: str = Field(
        "*",
        description="Allowed CORS origins (comma-separated)"
    )

    # ========================================================================
    # Vector Database Settings (Qdrant)
    # ========================================================================
    vector_db_backend: str = Field(
        "qdrant",
        description="Vector database backend (currently only qdrant supported)"
    )
    vector_db_url: str = Field(
        "http://localhost:6334",
        description="Qdrant connection URL (port 6334 for qdrant-mcp-edu container)"
    )
    vector_db_api_key: str | None = Field(
        None,
        description="Qdrant API key (optional, for Qdrant Cloud)"
    )

    # ========================================================================
    # Collection Settings
    # ========================================================================
    default_collection: str = Field(
        "educational_content",
        description="Default Qdrant collection name for educational content"
    )
    default_limit: int = Field(
        10,
        description="Default number of search results to return"
    )
    vector_dimensions: int = Field(
        3072,
        description="Embedding vector dimensions (text-embedding-3-large = 3072)"
    )

    # ========================================================================
    # Embedding Settings
    # ========================================================================
    embedding_provider: str = Field(
        "precomputed",
        description="Embedding provider (precomputed = use embeddings from JSONL data)"
    )
    embedding_model: str = Field(
        "text-embedding-3-large",
        description="Embedding model name (must match pre-computed embeddings!)"
    )
    openai_api_key: str | None = Field(
        None,
        description="OpenAI API key for generating query embeddings (required for semantic search)"
    )

    # ========================================================================
    # Performance Settings
    # ========================================================================
    max_concurrent_requests: int = Field(
        50,
        description="Maximum concurrent requests"
    )
    embedding_cache_size: int = Field(
        1000,
        description="Maximum number of cached embeddings (if generating on-the-fly)"
    )
    embedding_cache_ttl: int = Field(
        3600,
        description="Embedding cache TTL in seconds (1 hour default)"
    )

    # ========================================================================
    # Data Pipeline Settings (JSONL Ingestion)
    # ========================================================================
    data_dir: str = Field(
        "data",
        description="Base directory for data files"
    )
    incoming_dir: str = Field(
        "data/incoming",
        description="Directory for incoming JSONL files from colleague uploads"
    )
    processed_dir: str = Field(
        "data/processed",
        description="Directory for successfully processed JSONL files"
    )
    failed_dir: str = Field(
        "data/failed",
        description="Directory for failed JSONL files with errors"
    )
    backup_dir: str = Field(
        "data/backups",
        description="Directory for Qdrant backups"
    )
    watch_incoming: bool = Field(
        True,
        description="Enable file system watching for automatic JSONL ingestion"
    )
    batch_size: int = Field(
        100,
        description="Batch size for Qdrant upsert operations"
    )

    # ========================================================================
    # Logging Settings
    # ========================================================================
    log_level: str = Field(
        "INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_format: str = Field(
        "json",
        description="Log format (json for structured logs, console for human-readable)"
    )
    log_file: str | None = Field(
        None,
        description="Optional log file path (None = stdout only)"
    )

    # ========================================================================
    # Security & Rate Limiting
    # ========================================================================
    enable_rate_limiting: bool = Field(
        True,
        description="Enable rate limiting for API endpoints"
    )
    max_requests_per_minute: int = Field(
        100,
        description="Maximum requests per minute per client (per IP)"
    )
    enable_auth: bool = Field(
        True,
        description="Enable Scalekit OAuth authentication (disable for local testing only!)"
    )

    # ========================================================================
    # Scalekit OAuth 2.1 Settings (Authentication & RBAC)
    # Official Architecture: MCP Server as OAuth 2.1 Protected Resource
    # ========================================================================
    scalekit_env_url: str | None = Field(
        None,
        description="Scalekit environment URL (e.g., https://your-org.scalekit.com)"
    )
    scalekit_client_id: str | None = Field(
        None,
        description="Scalekit OAuth client ID"
    )
    scalekit_client_secret: str | None = Field(
        None,
        description="Scalekit OAuth client secret"
    )
    scalekit_mcp_server_id: str | None = Field(
        None,
        description="MCP Server ID from Scalekit dashboard (unique identifier for this MCP server)"
    )
    scalekit_expected_audience: str | None = Field(
        None,
        description="Expected audience for token validation (e.g., http://localhost:8000/)"
    )
    scalekit_protected_resource_metadata: str | None = Field(
        None,
        description="OAuth 2.1 Protected Resource metadata JSON (copy from Scalekit MCP Server dashboard, minified)"
    )
    scalekit_audience: str = Field(
        "mcp-educational-server",
        description="[DEPRECATED] Expected JWT audience (use scalekit_expected_audience instead)"
    )
    scalekit_jwks_url: str | None = Field(
        None,
        description="[DEPRECATED] Scalekit JWKS URL - use Scalekit SDK instead"
    )
    jwt_algorithm: str = Field(
        "RS256",
        description="[DEPRECATED] JWT algorithm - use Scalekit SDK instead"
    )
    jwt_leeway: int = Field(
        10,
        description="[DEPRECATED] JWT expiration leeway - use Scalekit SDK instead"
    )
    
    # ========================================================================
    # Server Identification (for OAuth discovery)
    # ========================================================================
    server_name: str = Field(
        "MCP Educational Server",
        description="Human-readable server name"
    )
    server_version: str = Field(
        "1.0.0",
        description="Server version"
    )
    server_port: int = Field(
        8000,
        description="Server port (used for OAuth discovery URL generation)"
    )

    # ========================================================================
    # RBAC Settings
    # ========================================================================
    default_user_role: str = Field(
        "student",
        description="Default role for authenticated users without explicit role (student, teacher, admin)"
    )
    enable_rbac: bool = Field(
        True,
        description="Enable role-based access control for content filtering"
    )

    # ========================================================================
    # Health & Monitoring
    # ========================================================================
    enable_health_monitoring: bool = Field(
        True,
        description="Enable health check endpoints"
    )
    health_check_interval: int = Field(
        60,
        description="Health check interval in seconds"
    )
    enable_metrics: bool = Field(
        True,
        description="Enable Prometheus-style metrics collection"
    )
    metrics_retention_hours: int = Field(
        24,
        description="Metrics retention period in hours"
    )

    # ========================================================================
    # Pydantic Configuration
    # ========================================================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
    )

    # ========================================================================
    # Validators
    # ========================================================================
    @field_validator("transport")
    @classmethod
    def validate_transport(cls, v: str) -> str:
        """Validate transport protocol."""
        valid_transports = ["stdio", "http", "both"]
        if v.lower() not in valid_transports:
            raise ValueError(f"Transport must be one of: {', '.join(valid_transports)}")
        return v.lower()

    @field_validator("vector_db_backend")
    @classmethod
    def validate_backend(cls, v: str) -> str:
        """Validate vector database backend."""
        valid_backends = ["qdrant"]  # Currently only Qdrant supported
        if v.lower() not in valid_backends:
            raise ValueError(f"Backend must be one of: {', '.join(valid_backends)}")
        return v.lower()

    @field_validator("embedding_provider")
    @classmethod
    def validate_embedding_provider(cls, v: str) -> str:
        """Validate embedding provider."""
        valid_providers = ["precomputed", "openai", "sentence-transformers"]
        if v.lower() not in valid_providers:
            raise ValueError(f"Embedding provider must be one of: {', '.join(valid_providers)}")
        return v.lower()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {', '.join(valid_levels)}")
        return v.upper()

    @field_validator("default_user_role")
    @classmethod
    def validate_default_role(cls, v: str) -> str:
        """Validate default user role."""
        valid_roles = ["student", "teacher", "admin"]
        if v.lower() not in valid_roles:
            raise ValueError(f"Default role must be one of: {', '.join(valid_roles)}")
        return v.lower()

    @field_validator("default_limit", "max_concurrent_requests", "embedding_cache_size", "batch_size")
    @classmethod
    def validate_positive_integers(cls, v: int) -> int:
        """Validate positive integers."""
        if v <= 0:
            raise ValueError("Value must be positive")
        return v

    @field_validator("vector_dimensions")
    @classmethod
    def validate_vector_dimensions(cls, v: int) -> int:
        """Validate vector dimensions match text-embedding-3-large."""
        if v != 3072:
            raise ValueError("Vector dimensions must be 3072 for text-embedding-3-large model")
        return v

    # ========================================================================
    # Helper Methods
    # ========================================================================
    def is_http_enabled(self) -> bool:
        """Check if HTTP transport is enabled."""
        return self.transport in ["http", "both"]

    def is_stdio_enabled(self) -> bool:
        """Check if stdio transport is enabled."""
        return self.transport in ["stdio", "both"]

    def get_server_name(self, transport_type: str = "http") -> str:
        """
        Get server name for specific transport type.
        
        Args:
            transport_type: Transport type (stdio, http)
            
        Returns:
            Server name string
        """
        base_name = "mcp-educational-server"
        if transport_type == "stdio":
            return f"{base_name}-stdio"
        elif transport_type == "http":
            return f"{base_name}-http"
        return base_name

    def get_cors_origins(self) -> list[str]:
        """
        Get list of allowed CORS origins.
        
        Returns:
            List of origin URLs (or ["*"] for all origins)
        """
        if self.http_cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.http_cors_origins.split(",")]

    def validate_scalekit_config(self) -> bool:
        """
        Validate that Scalekit configuration is complete.
        
        Returns:
            True if Scalekit is properly configured, False otherwise
        """
        if not self.enable_auth:
            return True  # Auth disabled, no validation needed
        
        required_fields = [
            self.scalekit_env_url,
            self.scalekit_client_id,
            self.scalekit_client_secret,
            self.scalekit_jwks_url,
        ]
        
        return all(field is not None for field in required_fields)

    def get_absolute_path(self, relative_path: str) -> Path:
        """
        Convert relative path to absolute path.
        
        Args:
            relative_path: Relative path string
            
        Returns:
            Absolute Path object
        """
        path = Path(relative_path)
        if path.is_absolute():
            return path
        return (PACKAGE_DIR / path).resolve()
