#!/bin/bash
# Enable OAuth Authentication for MCP Educational Server
# This script updates the .env file to enable OAuth

set -e

ENV_FILE=".env"
ENV_EXAMPLE="env.example"

echo "🔐 Enabling OAuth Authentication for MCP Educational Server"
echo "==========================================================="
echo ""

# Check if .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  .env file not found. Creating from env.example..."
    if [ -f "$ENV_EXAMPLE" ]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        echo "✅ Created .env from env.example"
    else
        echo "❌ Error: Neither .env nor env.example found!"
        exit 1
    fi
fi

# Backup .env
echo "📦 Creating backup: .env.backup"
cp "$ENV_FILE" "$ENV_FILE.backup"

# Update ENABLE_AUTH to true
if grep -q "^ENABLE_AUTH=" "$ENV_FILE"; then
    # ENABLE_AUTH exists, update it
    sed -i 's/^ENABLE_AUTH=.*/ENABLE_AUTH=true/' "$ENV_FILE"
    echo "✅ Updated ENABLE_AUTH=true in .env"
else
    # ENABLE_AUTH doesn't exist, add it
    echo "" >> "$ENV_FILE"
    echo "# Authentication" >> "$ENV_FILE"
    echo "ENABLE_AUTH=true" >> "$ENV_FILE"
    echo "✅ Added ENABLE_AUTH=true to .env"
fi

echo ""
echo "✅ OAuth is now ENABLED!"
echo ""
echo "📋 Next steps:"
echo "   1. Verify Scalekit credentials in .env:"
echo "      - SCALEKIT_ENV_URL"
echo "      - SCALEKIT_CLIENT_ID"
echo "      - SCALEKIT_CLIENT_SECRET"
echo ""
echo "   2. Restart the MCP server:"
echo "      docker-compose restart mcp-server"
echo ""
echo "   3. Check logs:"
echo "      docker-compose logs -f mcp-server"
echo ""
echo "🔐 Users will now need to authenticate via Scalekit OAuth!"
