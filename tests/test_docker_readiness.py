"""
Docker Deployment Readiness Check

This script verifies that all components are ready for Docker Compose deployment:
- Environment variables configured
- Qdrant running and accessible
- Data loaded correctly
- OAuth/Scalekit configured
- Dependencies installed
- Server functionality working
"""

import sys
from pathlib import Path
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Force UTF-8 encoding for Windows console
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from qdrant_client import QdrantClient
from src.config.server_config import ServerConfig
from src.backends.qdrant import QdrantBackend
from src.utils.embeddings import EmbeddingService


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_environment_variables():
    """Check if all required environment variables are set."""
    print_section("1. ENVIRONMENT VARIABLES CHECK")
    
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API key for embeddings",
        "VECTOR_DB_URL": "Qdrant database URL",
        "DEFAULT_COLLECTION": "Default Qdrant collection name",
    }
    
    optional_vars = {
        "SCALEKIT_ENV_URL": "Scalekit environment URL",
        "SCALEKIT_CLIENT_ID": "Scalekit client ID",
        "SCALEKIT_CLIENT_SECRET": "Scalekit client secret",
        "ENABLE_AUTH": "Enable OAuth authentication",
        "ENABLE_RBAC": "Enable role-based access control",
        "LOG_LEVEL": "Logging level",
    }
    
    issues = []
    
    # Check required variables
    print("\n✓ Required Variables:")
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            masked_value = value[:10] + "..." if len(value) > 10 else value
            print(f"  ✅ {var}: {masked_value} ({description})")
        else:
            print(f"  ❌ {var}: NOT SET ({description})")
            issues.append(f"Missing required variable: {var}")
    
    # Check optional variables
    print("\n✓ Optional Variables:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            if "SECRET" in var or "KEY" in var:
                masked_value = "***" + value[-4:] if len(value) > 4 else "***"
            else:
                masked_value = value
            print(f"  ✅ {var}: {masked_value} ({description})")
        else:
            print(f"  ⚠️  {var}: NOT SET ({description})")
    
    # Load from ServerConfig
    print("\n✓ ServerConfig loaded:")
    try:
        config = ServerConfig()
        print(f"  ✅ Server Port: {config.server_port}")
        print(f"  ✅ Vector DB URL: {config.vector_db_url}")
        print(f"  ✅ Collection: {config.default_collection}")
        print(f"  ✅ RBAC Enabled: {config.enable_rbac}")
        print(f"  ✅ Auth Enabled: {config.enable_auth}")
        print(f"  ✅ Log Level: {config.log_level}")
    except Exception as e:
        print(f"  ❌ Failed to load ServerConfig: {e}")
        issues.append(f"ServerConfig error: {e}")
    
    return len(issues) == 0, issues


def check_qdrant():
    """Check if Qdrant is running and accessible."""
    print_section("2. QDRANT DATABASE CHECK")
    
    issues = []
    
    print("\n✓ Connection:")
    try:
        config = ServerConfig()
        client = QdrantClient(url=config.vector_db_url)
        print(f"  ✅ Connected to Qdrant at {config.vector_db_url}")
    except Exception as e:
        print(f"  ❌ Failed to connect to Qdrant: {e}")
        issues.append(f"Qdrant connection failed: {e}")
        return False, issues
    
    print("\n✓ Collections:")
    try:
        collections = client.get_collections()
        if not collections.collections:
            print("  ⚠️  No collections found")
            issues.append("No collections in Qdrant")
        else:
            for coll in collections.collections:
                info = client.get_collection(coll.name)
                print(f"  ✅ {coll.name}: {info.points_count} points")
    except Exception as e:
        print(f"  ❌ Failed to get collections: {e}")
        issues.append(f"Collection check failed: {e}")
        return False, issues
    
    print("\n✓ Default Collection:")
    try:
        coll_info = client.get_collection(config.default_collection)
        print(f"  ✅ Collection: {config.default_collection}")
        print(f"  ✅ Points: {coll_info.points_count}")
        print(f"  ✅ Vector Size: {coll_info.config.params.vectors.size}")
        print(f"  ✅ Distance: {coll_info.config.params.vectors.distance}")
        
        if coll_info.points_count == 0:
            issues.append("Default collection is empty!")
    except Exception as e:
        print(f"  ❌ Default collection '{config.default_collection}' not found: {e}")
        issues.append(f"Default collection error: {e}")
        return False, issues
    
    return len(issues) == 0, issues


def check_oauth_scalekit():
    """Check OAuth/Scalekit configuration."""
    print_section("3. OAUTH / SCALEKIT CHECK")
    
    issues = []
    config = ServerConfig()
    
    print("\n✓ Configuration:")
    print(f"  Auth Enabled: {config.enable_auth}")
    
    if not config.enable_auth:
        print("  ℹ️  OAuth is DISABLED (ENABLE_AUTH=False)")
        print("  ℹ️  This is OK for local development")
        return True, []
    
    # Check Scalekit environment variables
    required_oauth = {
        "SCALEKIT_ENV_URL": config.scalekit_env_url,
        "SCALEKIT_CLIENT_ID": config.scalekit_client_id,
        "SCALEKIT_CLIENT_SECRET": config.scalekit_client_secret,
    }
    
    for var, value in required_oauth.items():
        if value:
            if "SECRET" in var:
                masked = "***" + value[-4:] if len(value) > 4 else "***"
            else:
                masked = value
            print(f"  ✅ {var}: {masked}")
        else:
            print(f"  ❌ {var}: NOT SET")
            issues.append(f"Missing OAuth variable: {var}")
    
    # Check if Scalekit SDK is installed
    print("\n✓ Dependencies:")
    try:
        import scalekit
        print(f"  ✅ Scalekit SDK installed: v{scalekit.__version__}")
    except ImportError:
        print("  ❌ Scalekit SDK not installed")
        issues.append("Scalekit SDK missing")
    
    # Test OAuth metadata endpoint
    print("\n✓ OAuth Metadata:")
    try:
        from src.server.oauth_metadata import create_oauth_metadata
        metadata = create_oauth_metadata(config)
        print(f"  ✅ Resource: {metadata.get('resource', 'N/A')}")
        print(f"  ✅ Authorization Servers: {len(metadata.get('authorization_servers', []))}")
        print(f"  ✅ Scopes: {len(metadata.get('scopes_supported', []))}")
    except Exception as e:
        print(f"  ⚠️  OAuth metadata error: {e}")
    
    return len(issues) == 0, issues


def check_dependencies():
    """Check if all Python dependencies are installed."""
    print_section("4. PYTHON DEPENDENCIES CHECK")
    
    required_packages = [
        ("fastmcp", "FastMCP library"),
        ("fastapi", "FastAPI web framework"),
        ("uvicorn", "ASGI server"),
        ("qdrant_client", "Qdrant client"),
        ("openai", "OpenAI API client"),
        ("pydantic", "Data validation"),
        ("dotenv", "Environment variables (python-dotenv)"),
        ("httpx", "HTTP client"),
        ("scalekit", "Scalekit SDK (optional)"),
    ]
    
    issues = []
    
    for package, description in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✅ {package}: Installed ({description})")
        except ImportError:
            if package == "scalekit":
                print(f"  ⚠️  {package}: Not installed ({description})")
            else:
                print(f"  ❌ {package}: NOT INSTALLED ({description})")
                issues.append(f"Missing package: {package}")
    
    return len(issues) == 0, issues


def check_search_functionality():
    """Check if search functionality works."""
    print_section("5. SEARCH FUNCTIONALITY CHECK")
    
    issues = []
    
    print("\n✓ Backend Initialization:")
    try:
        config = ServerConfig()
        backend = QdrantBackend(
            url=config.vector_db_url,
            api_key=config.vector_db_api_key
        )
        print("  ✅ QdrantBackend initialized")
    except Exception as e:
        print(f"  ❌ Failed to initialize backend: {e}")
        issues.append(f"Backend init failed: {e}")
        return False, issues
    
    print("\n✓ Embedding Service:")
    try:
        embedding_service = EmbeddingService(
            api_key=config.openai_api_key,
            model=config.embedding_model
        )
        print(f"  ✅ Embedding model: {config.embedding_model}")
    except Exception as e:
        print(f"  ❌ Failed to initialize embedding service: {e}")
        issues.append(f"Embedding service failed: {e}")
        return False, issues
    
    print("\n✓ Test Search:")
    try:
        # Create test query embedding
        query = "HTL Informatik"
        query_embedding = embedding_service.embed_query(query)
        print(f"  ✅ Query embedding created: {len(query_embedding)} dimensions")
        
        # Search
        results = backend.search(
            query_vector=query_embedding,
            collection=config.default_collection,
            limit=3,
            with_payload=True
        )
        
        print(f"  ✅ Search successful: {len(results)} results")
        
        if results:
            print("\n  Sample result:")
            print(f"    - ID: {results[0].id}")
            print(f"    - Score: {results[0].score:.4f}")
            print(f"    - Access Level: {results[0].payload.get('access_level', 'N/A')}")
            text_preview = results[0].payload.get('text', '')[:80]
            print(f"    - Text: {text_preview}...")
        else:
            print("  ⚠️  No results returned (collection might be empty)")
    except Exception as e:
        print(f"  ❌ Search failed: {e}")
        issues.append(f"Search error: {e}")
        return False, issues
    
    return len(issues) == 0, issues


def check_server_files():
    """Check if all required server files exist."""
    print_section("6. PROJECT FILES CHECK")
    
    required_files = [
        ("main.py", "Main entry point"),
        ("requirements.txt", "Python dependencies"),
        (".env", "Environment variables (should exist but not be committed)"),
        ("src/config/server_config.py", "Server configuration"),
        ("src/backends/qdrant.py", "Qdrant backend"),
        ("src/server/http_server.py", "HTTP server"),
        ("src/tools/search_tools.py", "Search tools"),
        ("src/pipeline/jsonl_ingestion.py", "JSONL ingestion pipeline"),
    ]
    
    issues = []
    
    for file_path, description in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"  ✅ {file_path}: {description}")
        else:
            print(f"  ❌ {file_path}: MISSING ({description})")
            issues.append(f"Missing file: {file_path}")
    
    return len(issues) == 0, issues


def check_data_directories():
    """Check if data directory structure is correct."""
    print_section("7. DATA DIRECTORIES CHECK")
    
    data_dirs = {
        "data": "Main data directory",
        "data/incoming": "Incoming JSONL files",
        "data/processed": "Processed files",
        "data/failed": "Failed files",
        "data/jsonl": "Source JSONL files",
        "data/statistics": "Statistics",
    }
    
    issues = []
    
    for dir_path, description in data_dirs.items():
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            files = list(path.glob("*"))
            print(f"  ✅ {dir_path}: {len(files)} files ({description})")
        else:
            print(f"  ❌ {dir_path}: MISSING ({description})")
            issues.append(f"Missing directory: {dir_path}")
    
    return len(issues) == 0, issues


def main():
    """Run all readiness checks."""
    print("\n" + "=" * 70)
    print("  🐳 DOCKER DEPLOYMENT READINESS CHECK")
    print("=" * 70)
    print("\nChecking if all components are ready for Docker Compose deployment...\n")
    
    all_checks = []
    
    # Run all checks
    checks = [
        ("Environment Variables", check_environment_variables),
        ("Qdrant Database", check_qdrant),
        ("OAuth/Scalekit", check_oauth_scalekit),
        ("Python Dependencies", check_dependencies),
        ("Search Functionality", check_search_functionality),
        ("Project Files", check_server_files),
        ("Data Directories", check_data_directories),
    ]
    
    for check_name, check_func in checks:
        try:
            success, issues = check_func()
            all_checks.append((check_name, success, issues))
        except Exception as e:
            print(f"\n❌ Unexpected error in {check_name}: {e}")
            all_checks.append((check_name, False, [str(e)]))
    
    # Summary
    print_section("📊 READINESS SUMMARY")
    
    passed = 0
    failed = 0
    warnings = 0
    
    for check_name, success, issues in all_checks:
        if success:
            print(f"  ✅ {check_name}: PASSED")
            passed += 1
        else:
            if issues:
                print(f"  ❌ {check_name}: FAILED")
                for issue in issues:
                    print(f"      - {issue}")
                failed += 1
            else:
                print(f"  ⚠️  {check_name}: WARNINGS")
                warnings += 1
    
    print("\n" + "=" * 70)
    print(f"  TOTAL: {passed} passed, {failed} failed, {warnings} warnings")
    print("=" * 70)
    
    if failed == 0:
        print("\n🎉 ALL CHECKS PASSED! Ready for Docker Compose deployment!")
        print("\nNext steps:")
        print("  1. Create Dockerfile for MCP server")
        print("  2. Create docker-compose.yml")
        print("  3. Configure volumes and networks")
        print("  4. Test Docker deployment")
        return True
    else:
        print("\n❌ SOME CHECKS FAILED! Please fix issues before deploying.")
        print("\nPlease resolve the issues listed above before proceeding.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
