#!/bin/bash
# Tailscale Installation & Setup für Raspberry Pi
# MCP Educational Server - Data Upload via Tailscale

set -e

echo "🌐 Tailscale Setup für MCP Educational Server"
echo "=============================================="
echo ""

# Check if running on Raspberry Pi / Linux
if [ ! -f /etc/os-release ]; then
    echo "❌ Error: /etc/os-release not found. Is this Linux?"
    exit 1
fi

# Check if Tailscale is already installed
if command -v tailscale &> /dev/null; then
    echo "✅ Tailscale is already installed"
    TAILSCALE_VERSION=$(tailscale version | head -n 1)
    echo "   Version: $TAILSCALE_VERSION"
    echo ""
else
    echo "📦 Installing Tailscale..."
    curl -fsSL https://tailscale.com/install.sh | sh
    echo "✅ Tailscale installed successfully!"
    echo ""
fi

# Check if Tailscale is running
if sudo tailscale status &> /dev/null; then
    echo "✅ Tailscale is already running"
    echo ""
    echo "📊 Current Status:"
    sudo tailscale status
    echo ""
    echo "🌐 Tailscale IPs:"
    echo "   IPv4: $(tailscale ip -4 2>/dev/null || echo 'Not connected')"
    echo "   IPv6: $(tailscale ip -6 2>/dev/null || echo 'Not connected')"
    echo ""
else
    echo "🚀 Starting Tailscale..."
    echo ""
    echo "⚠️  WICHTIG: Ein Browser-Link wird angezeigt!"
    echo "   → Öffnen Sie den Link und authentifizieren Sie sich"
    echo "   → Verwenden Sie den GLEICHEN Account wie Ihr Kollege!"
    echo ""
    read -p "Drücken Sie Enter um fortzufahren..." 
    echo ""
    
    sudo tailscale up
    
    echo ""
    echo "✅ Tailscale gestartet!"
    echo ""
fi

# Get Tailscale information
echo "📋 Tailscale Informationen:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TAILSCALE_IP4=$(tailscale ip -4 2>/dev/null || echo "N/A")
TAILSCALE_IP6=$(tailscale ip -6 2>/dev/null || echo "N/A")
HOSTNAME=$(hostname)

echo ""
echo "🖥️  Hostname: $HOSTNAME"
echo "🌐 Tailscale IPv4: $TAILSCALE_IP4"
echo "🌐 Tailscale IPv6: $TAILSCALE_IP6"
echo ""

# Check if data directories exist
DATA_DIR="/home/imreo/mcp-diploma-thesis-final/data/incoming"

if [ -d "$DATA_DIR" ]; then
    echo "✅ Data directory exists: $DATA_DIR"
    ls -ld "$DATA_DIR"
    echo ""
else
    echo "⚠️  Warning: Data directory not found: $DATA_DIR"
    echo "   Creating directory..."
    mkdir -p "$DATA_DIR"
    chmod 775 "$DATA_DIR"
    echo "✅ Created: $DATA_DIR"
    echo ""
fi

# Generate colleague upload command
echo "📤 Upload-Befehl für Kollegen:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Option 1 (mit Tailscale IP):"
echo "  scp datei.jsonl imreo@$TAILSCALE_IP4:$DATA_DIR/"
echo ""
echo "Option 2 (mit Hostname - nach Magic DNS Setup):"
echo "  scp datei.jsonl imreo@$HOSTNAME:$DATA_DIR/"
echo ""

# SSH key info
echo "🔑 SSH-Key Setup (empfohlen für passwortlosen Upload):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Kollege generiert SSH-Key:"
echo "  ssh-keygen -t ed25519 -C \"colleague@email.com\""
echo ""
echo "Kollege sendet Public Key an Sie."
echo ""
echo "Sie fügen Public Key hinzu:"
echo "  nano ~/.ssh/authorized_keys"
echo "  # → Public key einfügen und speichern"
echo ""

# Next steps
echo "📋 Nächste Schritte:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. ✅ Tailscale ist installiert und läuft"
echo ""
echo "2. 📧 Senden Sie Ihrem Kollegen:"
echo "   - Tailscale IP: $TAILSCALE_IP4"
echo "   - Upload-Befehl (siehe oben)"
echo "   - Dokumentation: docs/COLLEAGUE_TAILSCALE_GUIDE.md"
echo ""
echo "3. 🧪 Test-Upload durchführen:"
echo "   - Kollege erstellt test.jsonl"
echo "   - Kollege führt SCP-Befehl aus"
echo "   - Sie überprüfen: ls -lh $DATA_DIR/"
echo ""
echo "4. 🔄 Automatic Ingestion einrichten:"
echo "   - Option A: Manuell nach Upload"
echo "   - Option B: Watchdog Service (empfohlen)"
echo ""
echo "✅ Tailscale Setup abgeschlossen!"
echo ""

# Save info to file
INFO_FILE="/home/imreo/mcp-diploma-thesis-final/TAILSCALE_INFO.txt"
cat > "$INFO_FILE" << EOF
Tailscale Setup Information
===========================
Date: $(date)
Hostname: $HOSTNAME
Tailscale IPv4: $TAILSCALE_IP4
Tailscale IPv6: $TAILSCALE_IP6

Upload Command for Colleague:
scp file.jsonl imreo@$TAILSCALE_IP4:$DATA_DIR/

SSH Key Setup:
1. Colleague generates key: ssh-keygen -t ed25519
2. Colleague sends public key to you
3. Add to: ~/.ssh/authorized_keys

Data Directory: $DATA_DIR
EOF

echo "💾 Informationen gespeichert in: $INFO_FILE"
echo ""
