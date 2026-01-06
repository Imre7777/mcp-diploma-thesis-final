# 🚀 LIVE DEPLOYMENT COMMANDS

**Target**: raspi-docker.local  
**User**: imreo  
**Domain**: https://leowiki-mcp.stream

---

## STEP 1: SSH VERBINDEN

```bash
ssh imreo@raspi-docker.local
# Password: leowiki1234
```

---

## STEP 2: SYSTEM ÜBERPRÜFEN

```bash
# Check Docker
docker --version
docker-compose --version

# Check system
uname -a
df -h

# Check if old deployment exists
ls -la /home/imreo/ | grep mcp
```

---

## STEP 3: REPOSITORY KLONEN

```bash
# Navigate to home
cd /home/imreo

# Clone repository (or update if exists)
if [ -d "mcp-diploma-thesis-final" ]; then
    echo "Repository exists, updating..."
    cd mcp-diploma-thesis-final
    git fetch origin
    git checkout week-4-deployment
    git pull origin week-4-deployment
else
    echo "Cloning repository..."
    git clone https://github.com/Imre7777/mcp-diploma-thesis-final.git
    cd mcp-diploma-thesis-final
    git checkout week-4-deployment
fi

# Verify
pwd
git branch
git log --oneline -5
```

---

## STEP 4: ENVIRONMENT KONFIGURIEREN

```bash
# Copy template
cp env.example .env

# Edit .env file
nano .env
```

### IN NANO EDITOR:

Ändere diese Zeile:
```bash
OPENAI_API_KEY=your-openai-api-key-here
```

Zu:
```bash
OPENAI_API_KEY=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
```

**Speichern**: `Ctrl+O`, `Enter`, `Ctrl+X`

---

## STEP 5: DEPLOYMENT STARTEN

```bash
# Make deploy script executable
chmod +x deploy.sh

# RUN DEPLOYMENT!
./deploy.sh
```

**Das Script wird:**
1. ✅ .env überprüfen
2. ✅ Alte Container stoppen
3. ✅ Docker Images pullen
4. ✅ MCP Server bauen
5. ✅ Services starten
6. ✅ Health Checks ausführen

---

## STEP 6: VERIFICATION

```bash
# Check containers
docker-compose ps

# Check logs
docker-compose logs --tail=50

# Check health
curl http://localhost:8000/health

# Check external HTTPS (if DNS configured)
curl https://leowiki-mcp.stream/health
```

---

## TROUBLESHOOTING

### If deploy.sh fails:

```bash
# Check Docker
sudo systemctl status docker

# Start Docker if needed
sudo systemctl start docker

# Try manual deployment
docker-compose down
docker-compose pull
docker-compose build --no-cache mcp-server
docker-compose up -d

# Check logs
docker-compose logs -f
```

### If port already in use:

```bash
# Find what's using port 8000
sudo netstat -tlnp | grep 8000

# Stop old services
docker-compose down
docker stop $(docker ps -aq) 2>/dev/null

# Try again
./deploy.sh
```

---

## STEP 7: DATA MIGRATION (Optional)

If you have existing Qdrant data:

```bash
# Check if data exists
ls -lh qdrant_data/ 2>/dev/null || echo "No existing data"

# If you need to import data later:
# We can do this after deployment is working
```

---

## QUICK REFERENCE

```bash
# View all logs
docker-compose logs -f

# Restart specific service
docker-compose restart mcp-server

# Stop all
docker-compose down

# Start all
docker-compose up -d

# Check status
docker-compose ps

# Shell into container
docker-compose exec mcp-server bash
```

---

## 🎯 SUCCESS INDICATORS

You'll know it worked when:

1. ✅ `docker-compose ps` shows all containers "Up (healthy)"
2. ✅ `curl http://localhost:8000/health` returns JSON
3. ✅ `curl https://leowiki-mcp.stream/health` works (if DNS ready)
4. ✅ Logs show "Starting HTTP server on http://0.0.0.0:8000"

---

## ⚠️ SECURITY NOTE

After deployment, change password:
```bash
passwd
# Enter new password
```

And/or setup SSH keys for passwordless login.

---

**READY TO START?**

Run STEP 1 first (SSH connection)!
