#!/bin/bash
# UFW Firewall Setup for MCP Educational Server
# Raspberry Pi Security Hardening

set -e

echo "🔒 Setting up UFW Firewall for MCP Educational Server"
echo "======================================================"
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    echo "   Usage: sudo ./scripts/setup_firewall.sh"
    exit 1
fi

# Check if UFW is installed
if ! command -v ufw &> /dev/null; then
    echo "📦 UFW not installed. Installing..."
    apt-get update
    apt-get install -y ufw
    echo "✅ UFW installed"
    echo ""
fi

echo "🔧 Configuring UFW rules..."
echo ""

# Reset UFW to default (clean slate)
echo "Resetting UFW to defaults..."
ufw --force reset

# Default policies
echo "Setting default policies..."
ufw default deny incoming
ufw default allow outgoing
echo "✅ Default policies set"
echo ""

# Allow SSH (critical - don't lock yourself out!)
echo "Allowing SSH (port 22)..."
ufw allow 22/tcp comment 'SSH access'
echo "✅ SSH allowed"
echo ""

# Allow HTTP (port 80) - for Let's Encrypt and HTTP->HTTPS redirect
echo "Allowing HTTP (port 80)..."
ufw allow 80/tcp comment 'HTTP (Caddy)'
echo "✅ HTTP allowed"
echo ""

# Allow HTTPS (port 443) - main application access
echo "Allowing HTTPS (port 443)..."
ufw allow 443/tcp comment 'HTTPS (Caddy)'
ufw allow 443/udp comment 'HTTP/3 (Caddy)'
echo "✅ HTTPS allowed"
echo ""

# Explicitly DENY Qdrant ports (extra safety)
echo "Explicitly denying Qdrant ports..."
ufw deny 6333/tcp comment 'Qdrant HTTP - BLOCKED'
ufw deny 6334/tcp comment 'Qdrant gRPC - BLOCKED'
echo "✅ Qdrant ports blocked"
echo ""

# Explicitly DENY MCP Server port (extra safety)
echo "Explicitly denying direct MCP Server access..."
ufw deny 8000/tcp comment 'MCP Server - BLOCKED (use HTTPS)'
echo "✅ MCP Server port blocked"
echo ""

# Enable UFW
echo "Enabling UFW..."
ufw --force enable
echo "✅ UFW enabled"
echo ""

# Show status
echo "======================================================"
echo "🔒 Firewall Configuration Complete"
echo "======================================================"
echo ""
ufw status verbose
echo ""

echo "📋 Summary:"
echo "  ✅ SSH (22)         - ALLOWED"
echo "  ✅ HTTP (80)        - ALLOWED (Caddy)"
echo "  ✅ HTTPS (443)      - ALLOWED (Caddy)"
echo "  ❌ Qdrant (6333)    - BLOCKED"
echo "  ❌ Qdrant (6334)    - BLOCKED"
echo "  ❌ MCP Server (8000) - BLOCKED"
echo ""
echo "🔐 Security Status:"
echo "  - Only Caddy (HTTPS) is accessible from internet"
echo "  - Qdrant is ONLY accessible from Docker containers"
echo "  - MCP Server is ONLY accessible via Caddy reverse proxy"
echo ""
echo "✅ Firewall setup complete!"
echo ""

# Save rules
echo "💾 Saving UFW rules..."
ufw status numbered > /home/imreo/mcp-diploma-thesis-final/firewall_rules.txt
echo "✅ Rules saved to: /home/imreo/mcp-diploma-thesis-final/firewall_rules.txt"
echo ""
