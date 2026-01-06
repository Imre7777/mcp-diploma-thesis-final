# 🐳 MCP Educational Server - Docker Deployment

**Production Ready Docker Compose Setup**

Domain: https://leowiki-mcp.stream  
Platform: Raspberry Pi (ARM64)  
Date: January 6, 2026

---

## 🚀 **QUICK START**

### **On Raspberry Pi:**

```bash
# 1. Clone repository
git clone https://github.com/Imre7777/mcp-diploma-thesis-final.git
cd mcp-diploma-thesis-final
git checkout week-4-deployment

# 2. Configure environment
cp .env.production .env
nano .env  # Add your OPENAI_API_KEY

# 3. Deploy!
chmod +x deploy.sh
./deploy.sh
```

**That's it!** Your server is now live at https://leowiki-mcp.stream

---

## 📦 **WHAT'S INCLUDED**

### **Services:**

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| **qdrant** | qdrant/qdrant:latest | 6334, 6333 | Vector database |
| **mcp-server** | Custom (Python 3.13) | 8000 | MCP Educational Server |
| **caddy** | caddy:2-alpine | 80, 443 | Reverse proxy + HTTPS |

### **Features:**

- ✅ **HTTPS** with automatic Let's Encrypt certificates
- ✅ **Health Checks** for all services
- ✅ **Persistent Data** (Qdrant volumes)
- ✅ **Auto-Restart** on failure
- ✅ **Security Headers** (HSTS, XSS protection, etc.)
- ✅ **Compression** (gzip, zstd)
- ✅ **Rate Limiting** (100 requests/minute per IP)
- ✅ **Logging** (JSON format, rotating logs)

---

## 🏗️ **ARCHITECTURE**

```
Internet
    ↓
  :443 HTTPS
    ↓
┌─────────────┐
│   Caddy     │ ← Reverse Proxy + TLS
│  (Alpine)   │    Let's Encrypt certificates
└──────┬──────┘
       │ :8000
       ↓
┌─────────────┐
│ MCP Server  │ ← FastMCP + FastAPI
│ (Python3.13)│    Semantic Search + RBAC
└──────┬──────┘
       │ :6334
       ↓
┌─────────────┐
│   Qdrant    │ ← Vector Database
│  (Latest)   │    757 documents loaded
└─────────────┘
```

---

## 📁 **FILE STRUCTURE**

```
mcp-diploma-thesis-final/
├── docker-compose.yml      # Multi-container orchestration
├── Dockerfile              # MCP Server container
├── Caddyfile              # Reverse proxy config (HTTPS)
├── .dockerignore          # Build optimization
├── deploy.sh              # Automated deployment script
├── .env.production        # Environment template
├── main.py                # MCP Server entry point
├── requirements.txt       # Python dependencies
├── src/                   # Source code
│   ├── auth/             # OAuth & Scalekit
│   ├── backends/         # Qdrant backend
│   ├── config/           # Server configuration
│   ├── middleware/       # Auth middleware
│   ├── pipeline/         # JSONL ingestion
│   ├── server/           # HTTP & STDIO server
│   ├── tools/            # MCP tools
│   └── utils/            # Utilities
├── data/                  # Data directories
│   ├── incoming/         # Upload JSONL files here
│   ├── processed/        # Successfully ingested
│   ├── failed/           # Failed ingestion
│   ├── jsonl/            # Source data
│   └── statistics/       # Embedding stats
└── docs/                  # Documentation
```

---

## 🔧 **CONFIGURATION**

### **Environment Variables (.env):**

```bash
# Required
OPENAI_API_KEY=sk-proj-your-key-here

# Optional (OAuth)
ENABLE_AUTH=false  # Set to 'true' for OAuth
SCALEKIT_ENV_URL=https://mcpeduauth.scalekit.dev
SCALEKIT_CLIENT_ID=your-client-id
SCALEKIT_CLIENT_SECRET=your-client-secret
```

### **Docker Compose Override (Optional):**

Create `docker-compose.override.yml` for local customization:

```yaml
version: '3.8'

services:
  mcp-server:
    volumes:
      # Mount local code for development
      - ./src:/app/src:ro
    environment:
      - LOG_LEVEL=DEBUG
```

---

## 🎯 **ENDPOINTS**

| Endpoint | Purpose | Example |
|----------|---------|---------|
| `/health` | Health check | `curl https://leowiki-mcp.stream/health` |
| `/docs` | API documentation | `https://leowiki-mcp.stream/docs` |
| `/mcp/` | MCP endpoint (SSE) | MCP Inspector connection |
| `/.well-known/oauth-protected-resource` | OAuth metadata | Scalekit integration |
| `/api/*` | API endpoints | Internal use |

---

## 📊 **MONITORING**

### **View Logs:**

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f mcp-server
docker-compose logs -f qdrant
docker-compose logs -f caddy
```

### **Check Status:**

```bash
# Service health
docker-compose ps

# Resource usage
docker stats

# Disk usage
docker system df
```

### **Health Checks:**

```bash
# Local
curl http://localhost:8000/health

# Production
curl https://leowiki-mcp.stream/health
```

---

## 🔄 **MAINTENANCE**

### **Update Deployment:**

```bash
# Pull latest code
git pull origin week-4-deployment

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### **Backup Data:**

```bash
# Backup Qdrant data
docker run --rm \
  -v mcp_diploma_thesis_final_qdrant_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/qdrant_backup.tar.gz -C /data .
```

### **Restore Data:**

```bash
# Restore Qdrant data
docker-compose down
docker run --rm \
  -v mcp_diploma_thesis_final_qdrant_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/qdrant_backup.tar.gz -C /data
docker-compose up -d
```

---

## 🧪 **TESTING**

### **Local Testing (Before Deployment):**

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs -f

# Test search
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"HTL","limit":5}'

# Stop
docker-compose down
```

### **Production Testing:**

```bash
# Test HTTPS
curl -I https://leowiki-mcp.stream

# Test health
curl https://leowiki-mcp.stream/health

# Test MCP endpoint
curl -H "Accept: text/event-stream" \
  https://leowiki-mcp.stream/mcp/

# Test with MCP Inspector
npx -y @modelcontextprotocol/inspector \
  https://leowiki-mcp.stream/mcp/
```

---

## 🔒 **SECURITY**

### **What's Included:**

- ✅ HTTPS with Let's Encrypt
- ✅ Security headers (HSTS, XSS, etc.)
- ✅ Rate limiting (100 req/min per IP)
- ✅ No exposed credentials
- ✅ Minimal attack surface

### **Additional Recommendations:**

```bash
# Firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Regular updates
sudo apt update && sudo apt upgrade -y
docker-compose pull
docker-compose up -d

# Monitor logs
docker-compose logs -f | grep -i error
```

---

## 📚 **DOCUMENTATION**

- **Full Deployment Guide**: `docs/DEPLOYMENT_TO_RASPBERRY_PI.md`
- **Docker Readiness**: `docs/DOCKER_READINESS_REPORT.md`
- **Server Guide**: `docs/SERVER_RUNNING_GUIDE.md`
- **OAuth Setup**: `docs/SCALEKIT_SETUP.md`
- **Tailscale Setup**: `docs/TAILSCALE_SETUP.md`

---

## 🆘 **TROUBLESHOOTING**

### **Common Issues:**

| Problem | Solution |
|---------|----------|
| 502 Bad Gateway | `docker-compose restart mcp-server` |
| SSL Not Working | Wait 1-2 min, check `docker-compose logs caddy` |
| Qdrant Connection Failed | `docker-compose restart qdrant` |
| Out of Memory | Increase swap, check `docker stats` |

### **Get Help:**

```bash
# View all logs
docker-compose logs

# Interactive shell
docker-compose exec mcp-server bash

# Check environment
docker-compose exec mcp-server env
```

---

## 🎓 **FOR YOUR THESIS**

This Docker Compose setup demonstrates:

1. **Production-Ready Architecture** ✅
   - Multi-container orchestration
   - Health checks and auto-restart
   - HTTPS with automatic certificates

2. **Security Best Practices** ✅
   - TLS encryption
   - Security headers
   - Rate limiting
   - No hardcoded credentials

3. **Scalability** ✅
   - Easy to add more services
   - Volume-based persistence
   - Can scale horizontally

4. **Maintainability** ✅
   - One-command deployment
   - Automated backups
   - Clear documentation

---

## 🚀 **DEPLOYMENT CHECKLIST**

- [ ] DNS configured (leowiki-mcp.stream)
- [ ] `.env` file created with API keys
- [ ] Docker & Docker Compose installed
- [ ] Ports 80, 443 open
- [ ] Run `./deploy.sh`
- [ ] Verify HTTPS: `curl https://leowiki-mcp.stream/health`
- [ ] Test MCP endpoint with Inspector
- [ ] Set up backups (cron job)
- [ ] Configure monitoring

---

**🎉 Your MCP server is production-ready!**

```
https://leowiki-mcp.stream
```

For questions or issues, check the logs:
```bash
docker-compose logs -f
```
