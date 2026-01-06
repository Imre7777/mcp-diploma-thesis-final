#!/bin/bash

# MCP Educational Server - Deployment Script
# Domain: https://leowiki-mcp.stream
# Target: Raspberry Pi

set -e  # Exit on error

echo "========================================"
echo "MCP Educational Server - Deployment"
echo "Domain: https://leowiki-mcp.stream"
echo "========================================"

# Check if running on Raspberry Pi
if [ -f /proc/device-tree/model ]; then
    MODEL=$(cat /proc/device-tree/model)
    echo "Detected: $MODEL"
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo ""
    echo "❌ ERROR: .env file not found!"
    echo ""
    echo "Please create .env file from template:"
    echo "  cp .env.production .env"
    echo "  nano .env  # Edit with your values"
    echo ""
    exit 1
fi

# Check if OPENAI_API_KEY is set
if grep -q "your-openai-api-key-here" .env; then
    echo ""
    echo "⚠️  WARNING: OPENAI_API_KEY still has default value!"
    echo "Please update .env with your actual API key."
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Stop existing containers
echo ""
echo "🛑 Stopping existing containers..."
docker-compose down || true

# Pull latest images
echo ""
echo "📥 Pulling Docker images..."
docker-compose pull

# Build MCP server image
echo ""
echo "🔨 Building MCP server..."
docker-compose build --no-cache mcp-server

# Create data directories if they don't exist
echo ""
echo "📁 Creating data directories..."
mkdir -p data/incoming
mkdir -p data/processed
mkdir -p data/failed
mkdir -p data/jsonl
mkdir -p data/statistics

# Set correct permissions
chmod 755 data/incoming
chmod 755 data/processed
chmod 755 data/failed

# Check if Qdrant data needs to be migrated
if [ -d "qdrant_data" ]; then
    echo ""
    echo "ℹ️  Qdrant data directory found"
    echo "Data will be preserved in Docker volume"
fi

# Start services
echo ""
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
docker-compose ps

# Check Qdrant
echo ""
echo "🔍 Checking Qdrant..."
QDRANT_HEALTH=$(curl -s http://localhost:6333/healthz || echo "failed")
if [ "$QDRANT_HEALTH" = "ok" ]; then
    echo "  ✅ Qdrant is healthy"
else
    echo "  ❌ Qdrant health check failed"
fi

# Check MCP Server
echo ""
echo "🔍 Checking MCP Server..."
MCP_HEALTH=$(curl -s http://localhost:8000/health || echo "failed")
if echo "$MCP_HEALTH" | grep -q "healthy"; then
    echo "  ✅ MCP Server is healthy"
else
    echo "  ❌ MCP Server health check failed"
fi

# Show logs
echo ""
echo "📋 Recent logs (last 20 lines):"
docker-compose logs --tail=20

# Show Caddy status
echo ""
echo "🔐 Caddy SSL Status:"
docker-compose exec -T caddy caddy list-certificates || echo "  ⏳ Certificates not yet issued (this is normal on first run)"

echo ""
echo "========================================"
echo "✅ Deployment Complete!"
echo "========================================"
echo ""
echo "Your MCP server is now running at:"
echo "  🌐 https://leowiki-mcp.stream"
echo ""
echo "Endpoints:"
echo "  📖 API Docs:     https://leowiki-mcp.stream/docs"
echo "  ❤️  Health:       https://leowiki-mcp.stream/health"
echo "  🔌 MCP Endpoint: https://leowiki-mcp.stream/mcp/"
echo "  🔐 OAuth:        https://leowiki-mcp.stream/.well-known/oauth-protected-resource"
echo ""
echo "Useful commands:"
echo "  📊 View logs:      docker-compose logs -f"
echo "  🔄 Restart:        docker-compose restart"
echo "  🛑 Stop:           docker-compose down"
echo "  🗑️  Clean volumes:  docker-compose down -v"
echo ""
echo "Monitor health:"
echo "  curl https://leowiki-mcp.stream/health"
echo ""
