# 🔧 Services Overview - MCP Educational Server

**Domain**: https://leowiki-mcp.stream  
**Date**: January 6, 2026

---

## 📊 **SERVICE TYPES**

### **1. Docker Services (in docker-compose.yml)** 🐳

These run as containers on Raspberry Pi:

| Service | Type | Status | Notes |
|---------|------|--------|-------|
| **qdrant** | Container | ✅ Included | Vector database |
| **mcp-server** | Container | ✅ Included | Main application |
| **caddy** | Container | ✅ Included | Reverse proxy + HTTPS |
| **data-ingestion** | Container | ⏭️ Optional | Watchdog for JSONL files |

### **2. External Services (Cloud)** ☁️

These are third-party services, NOT running on your Pi:

| Service | Type | Status | Notes |
|---------|------|--------|-------|
| **Scalekit** | OAuth Provider | ✅ Configured | https://mcpeduauth.scalekit.dev |
| **OpenAI** | API | ✅ Required | Embeddings via API key |
| **Let's Encrypt** | SSL Certs | ✅ Automatic | Via Caddy |

### **3. Host Services (on Raspberry Pi OS)** 🖥️

These run directly on Raspberry Pi, NOT in Docker:

| Service | Type | Status | Notes |
|---------|------|--------|-------|
| **Tailscale** | VPN | ⏭️ Optional | For secure remote access |
| **Docker** | Container Runtime | ✅ Required | Runs containers |
| **SSH** | Remote Access | ✅ Standard | For management |

---

## 🔍 **DETAILED BREAKDOWN**

### **1. SCALEKIT** ☁️

**Type**: External OAuth Provider  
**Location**: https://mcpeduauth.scalekit.dev  
**Purpose**: JWT token validation for authentication

#### **Status:**
✅ **Already configured!** (No additional setup needed)

#### **How it works:**
```
User → Your MCP Server → Scalekit API (validates JWT)
```

#### **Configuration:**
```bash
# In .env file (when ENABLE_AUTH=true)
SCALEKIT_ENV_URL=https://mcpeduauth.scalekit.dev
SCALEKIT_CLIENT_ID=skc_35934031996379566
SCALEKIT_CLIENT_SECRET=your-secret-here
```

#### **You DON'T need to:**
- ❌ Install Scalekit on your server
- ❌ Run Scalekit in Docker
- ❌ Host Scalekit yourself

#### **You ONLY need to:**
- ✅ Have a Scalekit account (you already do!)
- ✅ Set environment variables in `.env`
- ✅ Enable auth: `ENABLE_AUTH=true`

---

### **2. TAILSCALE** 🔐

**Type**: VPN Service (Host-level)  
**Location**: Runs on Raspberry Pi OS  
**Purpose**: Secure remote access for data uploads

#### **Status:**
⏭️ **Optional** (for Week 5)

#### **Why Tailscale:**
- 🔒 Secure VPN access without port forwarding
- 📤 Colleague can upload JSONL files securely
- 🌐 Works from anywhere

#### **Installation:**
```bash
# On Raspberry Pi (NOT in Docker!)
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Get Tailscale IP
tailscale ip -4
# Example: 100.101.102.103
```

#### **Usage:**
```bash
# Colleague uploads files via Tailscale
scp data.jsonl pi@100.101.102.103:/home/pi/mcp-diploma-thesis-final/data/incoming/
```

#### **Documentation:**
See: `docs/TAILSCALE_SETUP.md`

---

### **3. DATA INGESTION WATCHDOG** 🔄

**Type**: Optional Docker Service  
**Location**: Docker container  
**Purpose**: Automatically process JSONL files

#### **Status:**
⏭️ **Can be added** (optional for automation)

#### **Current Setup:**
Manual ingestion works:
```bash
# Copy file to incoming/
cp data.jsonl data/incoming/

# Run manual ingestion
docker-compose exec mcp-server python scripts/ingest_full_data.py
```

#### **Optional: Add to docker-compose.yml**

Would add:
```yaml
  data-ingestion:
    build: .
    container_name: mcp-data-ingestion
    command: python -m src.pipeline.watchdog
    volumes:
      - ./data:/app/data
    depends_on:
      - qdrant
```

**Question**: Do you want me to add this as an automated service?

---

## 🏗️ **COMPLETE ARCHITECTURE**

```
┌─────────────────────────────────────────────────┐
│           RASPBERRY PI                           │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  Docker Compose (docker-compose.yml)     │  │
│  │                                           │  │
│  │  ┌─────────┐  ┌──────────┐  ┌────────┐  │  │
│  │  │ Qdrant  │  │   MCP    │  │ Caddy  │  │  │
│  │  │         │  │  Server  │  │ HTTPS  │  │  │
│  │  └────┬────┘  └────┬─────┘  └───┬────┘  │  │
│  │       │            │             │       │  │
│  └───────┼────────────┼─────────────┼───────┘  │
│          │            │             │          │
│  ┌───────┴────────────┴─────────────┴───────┐  │
│  │     Persistent Volumes                   │  │
│  │  - qdrant_data/                          │  │
│  │  - caddy_data/                           │  │
│  │  - data/incoming/                        │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  Host Services (Raspberry Pi OS)         │  │
│  │  - Tailscale (optional VPN)              │  │
│  │  - Docker Engine                         │  │
│  │  - SSH                                   │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                    │
                    │ HTTPS (:443)
                    ↓
┌─────────────────────────────────────────────────┐
│              EXTERNAL SERVICES                   │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Scalekit │  │  OpenAI  │  │ Let's Encrypt│  │
│  │  OAuth   │  │   API    │  │  SSL Certs   │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## 📋 **WHAT'S NEEDED FOR DEPLOYMENT**

### **Already Included in Docker Compose:** ✅

- ✅ Qdrant (vector database)
- ✅ MCP Server (main application)
- ✅ Caddy (HTTPS reverse proxy)

### **External Services (Already Set Up):** ✅

- ✅ Scalekit account (you have it)
- ✅ OpenAI API key (you have it)
- ✅ Domain DNS (leowiki-mcp.stream configured)

### **Optional Add-ons:**

- ⏭️ Tailscale (for secure uploads) - Week 5
- ⏭️ Data ingestion watchdog (automated processing) - Optional
- ⏭️ Monitoring (Prometheus/Grafana) - Optional

---

## 🎯 **RECOMMENDATION FOR NOW**

### **For Immediate Deployment:**

Use the **current docker-compose.yml** as-is:
```bash
./deploy.sh
```

This includes:
- ✅ Qdrant
- ✅ MCP Server
- ✅ Caddy (HTTPS)

### **For Week 5 (Later):**

Add:
1. **Tailscale** (on host, not Docker)
   - For secure colleague access
   - Install with: `curl -fsSL https://tailscale.com/install.sh | sh`

2. **Data Ingestion Watchdog** (optional Docker service)
   - Automatically process uploaded files
   - Can add to docker-compose.yml if needed

### **Scalekit & OpenAI:**

- ✅ Already integrated via environment variables
- ✅ No additional containers needed
- ✅ Just API calls from MCP Server

---

## 🤔 **DECISIONS TO MAKE**

### **Question 1: Data Ingestion**

Do you want **automatic file processing**?

**Option A: Manual** (current)
```bash
# Upload file manually
docker-compose exec mcp-server python scripts/ingest_full_data.py
```

**Option B: Automatic** (add watchdog service)
```yaml
# Add to docker-compose.yml
data-ingestion:
  build: .
  command: python -m src.pipeline.watchdog
```

### **Question 2: Tailscale**

Do you want **Tailscale for secure uploads** now?

**Option A: Add now**
- Install on Raspberry Pi host
- Document Tailscale IP
- Colleague can upload via VPN

**Option B: Add later** (Week 5)
- For now, use SCP over internet
- Or physical media transfer

---

## 📝 **WHAT I CAN ADD NOW**

If you want, I can:

1. ✅ **Add data-ingestion service** to docker-compose.yml
   - Automatic JSONL file processing
   - Watchdog monitors data/incoming/

2. ✅ **Add Tailscale setup** to deploy.sh
   - Automatic Tailscale installation
   - Configuration for colleague access

3. ✅ **Create monitoring service** (optional)
   - Health check dashboard
   - Log aggregation

**What would you like me to add?**

---

## 🚀 **CURRENT STATUS**

### **Ready for Production:** ✅

Your current `docker-compose.yml` has everything needed for:
- ✅ HTTPS public access (leowiki-mcp.stream)
- ✅ Vector database (Qdrant)
- ✅ MCP Server (semantic search + RBAC)
- ✅ Automatic SSL certificates
- ✅ OAuth ready (Scalekit via API)

### **Can Be Added Later:**

- ⏭️ Tailscale (VPN access)
- ⏭️ Watchdog (auto-ingestion)
- ⏭️ Monitoring (Prometheus/Grafana)

---

**Decision**: Deploy now with core services, or add optional services first?

My recommendation: **Deploy core now, add extras in Week 5!** 🚀
