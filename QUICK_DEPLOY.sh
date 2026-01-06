#!/bin/bash
# Quick deployment commands - Copy/paste into SSH session

# STEP 1: Navigate and clone/update repo
cd /home/imreo
if [ -d "mcp-diploma-thesis-final" ]; then
    echo "📦 Updating existing repository..."
    cd mcp-diploma-thesis-final
    git fetch origin
    git checkout week-4-deployment
    git pull origin week-4-deployment
else
    echo "📥 Cloning repository..."
    git clone https://github.com/Imre7777/mcp-diploma-thesis-final.git
    cd mcp-diploma-thesis-final
    git checkout week-4-deployment
fi

# STEP 2: Setup environment
if [ ! -f .env ]; then
    echo "⚙️  Creating .env file..."
    cp env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your OPENAI_API_KEY!"
    echo "Run: nano .env"
    echo ""
    exit 1
fi

# STEP 3: Check .env has real API key
if grep -q "your-openai-api-key-here" .env; then
    echo "❌ ERROR: Please update OPENAI_API_KEY in .env"
    echo "Run: nano .env"
    exit 1
fi

# STEP 4: Deploy!
echo "🚀 Starting deployment..."
chmod +x deploy.sh
./deploy.sh

echo ""
echo "✅ Deployment script completed!"
echo ""
echo "Check status with:"
echo "  docker-compose ps"
echo "  docker-compose logs -f"
echo ""
