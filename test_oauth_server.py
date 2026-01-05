"""
Test OAuth Server - Simplified startup for testing OAuth flow

This script starts the HTTP server with minimal configuration for testing OAuth.
"""

import sys
import asyncio
import logging

# Setup logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(__file__).rsplit('\\', 1)[0])

from src.config.server_config import ServerConfig
from src.server.http_server import HTTPMCPServer


async def main():
    """Start the HTTP server for OAuth testing."""
    try:
        logger.info("="*70)
        logger.info("🚀 Starting MCP Educational Server (OAuth Test Mode)")
        logger.info("="*70)
        
        # Load configuration
        config = ServerConfig()
        
        logger.info(f"Configuration loaded:")
        logger.info(f"  - Host: {config.http_host}")
        logger.info(f"  - Port: {config.http_port}")
        logger.info(f"  - Scalekit URL: {config.scalekit_env_url}")
        logger.info(f"  - Auth Enabled: {config.enable_auth}")
        logger.info(f"  - RBAC Enabled: {config.enable_rbac}")
        logger.info("="*70)
        
        # Create and start server
        server = HTTPMCPServer(config=config)
        
        logger.info("\n📋 Available Endpoints:")
        logger.info(f"  ✅ Health: http://localhost:{config.http_port}/health")
        logger.info(f"  ✅ OAuth Login: http://localhost:{config.http_port}/auth/login")
        logger.info(f"  ✅ OAuth Callback: http://localhost:{config.http_port}/auth/callback")
        logger.info(f"  ✅ OAuth Metadata: http://localhost:{config.http_port}/.well-known/oauth-protected-resource/mcp-edu-server")
        logger.info(f"  🔒 User Info: http://localhost:{config.http_port}/auth/user (requires token)")
        logger.info(f"  🔒 API Docs: http://localhost:{config.http_port}/docs")
        logger.info("")
        logger.info("🧪 To test OAuth flow:")
        logger.info(f"   1. Open browser: http://localhost:{config.http_port}/auth/login")
        logger.info("   2. You'll be redirected to Scalekit")
        logger.info("   3. After login, you'll get an access token")
        logger.info("")
        logger.info("Press Ctrl+C to stop the server")
        logger.info("="*70)
        
        await server.start()
        
    except KeyboardInterrupt:
        logger.info("\n\n👋 Server stopped by user")
    except Exception as e:
        logger.error(f"\n\n❌ Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
