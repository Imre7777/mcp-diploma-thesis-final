# 🚀 Deployment to Raspberry Pi

**Domain**: https://leowiki-mcp.stream  
**Target**: Raspberry Pi (ARM64)  
**Date**: January 6, 2026

---

## 📋 **PREREQUISITES**

### **On Raspberry Pi:**

```bash
# Check system
uname -a  # Should show: Linux raspberrypi ... aarch64

# Install Docker & Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
sudo systemctl enable docker
sudo systemctl start docker

# Verify
docker --version
docker-compose --version
```

### **DNS Configuration:**

Ensure `leowiki-mcp.stream` points to your Raspberry Pi's public IP:

```bash
# Check current DNS
dig leowiki-mcp.stream +short

# Should return your Raspberry Pi's IP
```

---

## 📦 **DEPLOYMENT STEPS**

### **Step 1: Transfer Files to Raspberry Pi**

```bash
# On your local machine
cd C:\Users\imreo\Documents\MCP_diploma_thesis_final

# Option A: Git (recommended)
git push origin week-4-deployment

# Then on Raspberry Pi:
ssh pi@leowiki-mcp.stream
cd /home/pi
git clone https://github.com/Imre7777/mcp-diploma-thesis-final.git
cd mcp-diploma-thesis-final
git checkout week-4-deployment

# Option B: SCP (if no git)
scp -r . pi@leowiki-mcp.stream:/home/pi/mcp-thesis/
```

### **Step 2: Configure Environment Variables**

```bash
# On Raspberry Pi
cd /home/pi/mcp-diploma-thesis-final  # or /home/pi/mcp-thesis

# Copy environment template
cp .env.production .env

# Edit with your values
nano .env
```

**Required values in `.env`:**

```bash
# MUST SET THIS!
OPENAI_API_KEY=sk-proj-your-actual-key-here

# Optional: Enable OAuth
ENABLE_AUTH=false  # Set to 'true' for production with OAuth
SCALEKIT_CLIENT_ID=your-client-id
SCALEKIT_CLIENT_SECRET=your-client-secret
```

### **Step 3: Deploy!**

```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

**The script will:**
1. ✅ Check .env file
2. ✅ Stop old containers
3. ✅ Pull Docker images
4. ✅ Build MCP server
5. ✅ Create data directories
6. ✅ Start all services
7. ✅ Verify health checks
8. ✅ Show logs

---

## 🔍 **VERIFICATION**

### **Check Services:**

```bash
# View running containers
docker-compose ps

# Should show:
# mcp-qdrant   qdrant/qdrant:latest       Up (healthy)
# mcp-server   mcp-server:latest          Up (healthy)
# mcp-caddy    caddy:2-alpine             Up
```

### **Check Endpoints:**

```bash
# Health Check
curl https://leowiki-mcp.stream/health

# Expected: {"status":"healthy","qdrant":"connected",...}

# API Documentation
curl https://leowiki-mcp.stream/docs

# OAuth Metadata
curl https://leowiki-mcp.stream/.well-known/oauth-protected-resource

# MCP Endpoint (SSE)
curl https://leowiki-mcp.stream/mcp/
```

### **Check Logs:**

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f mcp-server
docker-compose logs -f qdrant
docker-compose logs -f caddy
```

### **Check SSL Certificate:**

```bash
# List Caddy certificates
docker-compose exec caddy caddy list-certificates

# Should show: leowiki-mcp.stream (Let's Encrypt)
```

---

## 📊 **DATA MIGRATION**

### **Option 1: Migrate Existing Qdrant Data**

If you have existing Qdrant data on local machine:

```bash
# On local machine, backup Qdrant data
docker run --rm -v qdrant_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/qdrant_backup.tar.gz -C /data .

# Transfer to Raspberry Pi
scp qdrant_backup.tar.gz pi@leowiki-mcp.stream:/home/pi/

# On Raspberry Pi, restore data
cd /home/pi/mcp-diploma-thesis-final
docker-compose down
docker run --rm -v mcp_diploma_thesis_final_qdrant_data:/data \
  -v /home/pi:/backup alpine tar xzf /backup/qdrant_backup.tar.gz -C /data
docker-compose up -d
```

### **Option 2: Re-Ingest Data**

If you prefer fresh ingestion:

```bash
# Copy JSONL files to Raspberry Pi
scp data/jsonl/*.jsonl pi@leowiki-mcp.stream:/home/pi/mcp-thesis/data/incoming/

# On Raspberry Pi, ingestion happens automatically via watchdog
# Or run manual ingestion:
docker-compose exec mcp-server python scripts/ingest_full_data.py
```

---

## 🔧 **TROUBLESHOOTING**

### **Issue: Services not starting**

```bash
# Check logs
docker-compose logs

# Restart specific service
docker-compose restart mcp-server

# Full restart
docker-compose down
docker-compose up -d
```

### **Issue: SSL Certificate not issued**

```bash
# Check Caddy logs
docker-compose logs caddy

# Verify DNS is correct
dig leowiki-mcp.stream +short

# Check port 80 and 443 are open
sudo netstat -tlnp | grep -E ':(80|443)'

# Manually trigger certificate renewal
docker-compose exec caddy caddy reload --config /etc/caddy/Caddyfile
```

### **Issue: Qdrant connection failed**

```bash
# Check Qdrant is running
docker-compose ps qdrant

# Check Qdrant health
curl http://localhost:6333/healthz

# View Qdrant logs
docker-compose logs qdrant

# Restart Qdrant
docker-compose restart qdrant
```

### **Issue: MCP Server errors**

```bash
# View detailed logs
docker-compose logs -f mcp-server

# Check environment variables
docker-compose exec mcp-server env | grep -E 'OPENAI|QDRANT|SCALEKIT'

# Restart MCP server
docker-compose restart mcp-server
```

---

## 🔄 **UPDATING THE DEPLOYMENT**

### **Update Code:**

```bash
# Pull latest changes
git pull origin week-4-deployment

# Rebuild and restart
docker-compose down
docker-compose build --no-cache mcp-server
docker-compose up -d
```

### **Update Docker Images:**

```bash
# Pull latest base images
docker-compose pull

# Rebuild
docker-compose up -d --build
```

---

## 🛑 **STOPPING THE SERVER**

```bash
# Stop all services (keep data)
docker-compose down

# Stop and remove volumes (WARNING: deletes data!)
docker-compose down -v
```

---

## 📈 **MONITORING**

### **Resource Usage:**

```bash
# Docker stats
docker stats

# System resources
htop  # or: top

# Disk usage
df -h
docker system df
```

### **Health Monitoring:**

```bash
# Automated health check script
watch -n 30 'curl -s https://leowiki-mcp.stream/health | jq'

# Set up cron job for monitoring
crontab -e
# Add: */5 * * * * curl -f https://leowiki-mcp.stream/health || echo "Server down!" | mail -s "MCP Alert" your@email.com
```

---

## 🔐 **SECURITY**

### **Firewall Configuration:**

```bash
# Allow only necessary ports
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # SSH
sudo ufw enable
```

### **Regular Updates:**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Update Docker images monthly
docker-compose pull
docker-compose up -d
```

### **Backup Strategy:**

```bash
# Backup script (save as /home/pi/backup-mcp.sh)
#!/bin/bash
BACKUP_DIR="/home/pi/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup Qdrant data
docker run --rm \
  -v mcp_diploma_thesis_final_qdrant_data:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/qdrant_$DATE.tar.gz -C /data .

# Backup .env
cp /home/pi/mcp-diploma-thesis-final/.env $BACKUP_DIR/env_$DATE

# Keep only last 7 backups
find $BACKUP_DIR -name "qdrant_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"

# Schedule daily backups
# crontab -e
# Add: 0 2 * * * /home/pi/backup-mcp.sh
```

---

## 📱 **MOBILE ACCESS**

### **Tailscale (Optional):**

For secure remote access without exposing ports:

```bash
# Install Tailscale on Raspberry Pi
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Get Tailscale IP
tailscale ip -4

# Access via Tailscale network
curl http://100.x.x.x:8000/health
```

---

## 🎓 **TESTING AFTER DEPLOYMENT**

### **Test from External Network:**

```bash
# Test HTTPS
curl -I https://leowiki-mcp.stream

# Test Health
curl https://leowiki-mcp.stream/health

# Test MCP Endpoint
curl -H "Accept: text/event-stream" https://leowiki-mcp.stream/mcp/

# Test Search (if auth disabled)
curl -X POST https://leowiki-mcp.stream/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"HTL Informatik","limit":5}'
```

### **Test with MCP Inspector:**

```bash
# On your local machine
npx -y @modelcontextprotocol/inspector \
  https://leowiki-mcp.stream/mcp/
```

---

## 📞 **SUPPORT**

### **Common Issues:**

| Issue | Solution |
|-------|----------|
| 502 Bad Gateway | Check if mcp-server is running: `docker-compose ps` |
| SSL Error | Wait 1-2 minutes for Let's Encrypt, check `docker-compose logs caddy` |
| Connection Refused | Check firewall: `sudo ufw status` |
| Qdrant not found | Verify service: `docker-compose ps qdrant` |

### **Logs Location:**

- **MCP Server**: `docker-compose logs mcp-server`
- **Qdrant**: `docker-compose logs qdrant`
- **Caddy**: `docker-compose logs caddy`
- **Caddy Access**: Inside container at `/data/access.log`

---

## ✅ **DEPLOYMENT CHECKLIST**

Before going live:

- [ ] DNS points to Raspberry Pi IP
- [ ] `.env` file configured with real API keys
- [ ] Port 80 and 443 accessible from internet
- [ ] `deploy.sh` executed successfully
- [ ] All containers healthy: `docker-compose ps`
- [ ] HTTPS working: `curl https://leowiki-mcp.stream/health`
- [ ] SSL certificate issued: `docker-compose exec caddy caddy list-certificates`
- [ ] Data loaded in Qdrant: Check collection points
- [ ] MCP endpoint accessible: Test with MCP Inspector
- [ ] Backups configured: Set up cron job

---

**🎉 Your MCP Educational Server is now live at:**

```
https://leowiki-mcp.stream
```

**Next**: Test with Claude Desktop or MCP Inspector!
