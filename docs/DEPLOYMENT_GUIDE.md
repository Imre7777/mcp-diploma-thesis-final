# Deployment Guide - MCP Educational Server

## Production Deployment on Raspberry Pi

**Target**: Remote Raspberry Pi Server  
**Access**: Students and Teachers via HTTPS  
**Authentication**: Custom OAuth with Role-Based Access Control

---

## 📋 Prerequisites

### Hardware Requirements
- **Raspberry Pi 4** (4GB+ RAM recommended)
- **64GB+ SD Card** (Class 10 or better)
- **Stable Internet Connection**
- **Static IP Address** or **Dynamic DNS**

### Software Requirements
- **Raspberry Pi OS** (64-bit, Bullseye or newer)
- **Docker** & **Docker Compose**
- **Git**
- **Python 3.11+**

---

## 🚀 Step 1: Raspberry Pi Initial Setup

### 1.1 Install Raspberry Pi OS

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y git curl vim htop
```

### 1.2 Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install -y docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 1.3 Configure Static IP (Optional but Recommended)

Edit `/etc/dhcpcd.conf`:
```bash
sudo nano /etc/dhcpcd.conf
```

Add:
```conf
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8 8.8.4.4
```

Restart networking:
```bash
sudo systemctl restart dhcpcd
```

---

## 🔧 Step 2: Clone and Setup Project

### 2.1 Clone Repository

```bash
cd /home/pi
git clone <YOUR_NEW_REPO_URL> mcp-thesis
cd mcp-thesis
```

### 2.2 Create Environment File

```bash
cp .env.example .env
nano .env
```

Configure:
```env
# Domain (use your domain or IP)
DOMAIN=your-domain.com
EMAIL=your-email@example.com

# JWT Secret (GENERATE A STRONG SECRET!)
JWT_SECRET_KEY=<GENERATE_RANDOM_SECRET>

# Qdrant API Key (optional, for security)
QDRANT_API_KEY=<OPTIONAL_KEY>
```

**Generate JWT Secret:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2.3 Create Data Directories

```bash
mkdir -p data/{incoming,processed,failed,backups,qdrant_storage,oauth_db,caddy_data,caddy_config}
chmod 755 data/incoming  # Allow SCP uploads
```

---

## 🐳 Step 3: Build and Start Services

### 3.1 Build Docker Images

```bash
docker-compose build
```

### 3.2 Start Services

```bash
docker-compose up -d
```

### 3.3 Verify All Containers Running

```bash
docker-compose ps
```

Expected output:
```
NAME            STATUS          PORTS
caddy           Up              0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
oauth-server    Up              0.0.0.0:8001->8001/tcp
mcp-server      Up              0.0.0.0:8000->8000/tcp
qdrant          Up              0.0.0.0:6333->6333/tcp
data-watcher    Up
```

---

## 👥 Step 4: Initialize Users

### 4.1 Create Initial Admin User

```bash
python3 scripts/setup_users.py --create-admin
```

Enter:
- Username: `admin`
- Email: `admin@yourdomain.com`
- Password: `<STRONG_PASSWORD>`
- Role: `teacher` (admins are teachers)

### 4.2 Create Test Student

```bash
python3 scripts/setup_users.py --create-user \
    --username student1 \
    --email student1@example.com \
    --role student \
    --password test123
```

### 4.3 Create Test Teacher

```bash
python3 scripts/setup_users.py --create-user \
    --username teacher1 \
    --email teacher1@example.com \
    --role teacher \
    --password test123
```

---

## 🌐 Step 5: Network Configuration

### 5.1 Router Port Forwarding

Configure your router to forward external traffic to Raspberry Pi:

| External Port | Internal IP | Internal Port | Protocol |
|---------------|-------------|---------------|----------|
| 80            | 192.168.1.100 | 80          | TCP      |
| 443           | 192.168.1.100 | 443         | TCP      |

### 5.2 Domain Configuration (if using custom domain)

Point your domain's A record to your **public IP address**:

```
Type: A
Name: @
Value: <YOUR_PUBLIC_IP>
TTL: 3600
```

Optional subdomain:
```
Type: A
Name: mcp
Value: <YOUR_PUBLIC_IP>
TTL: 3600
```

### 5.3 Firewall Configuration

```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow SSH (if using SSH)
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
```

---

## 📊 Step 6: Load Initial Data

### 6.1 Prepare Sample Data

Create `sample_data.json`:
```json
{
  "documents": [
    {
      "id": "doc_001",
      "title": "Welcome to Python Programming",
      "content": "Python is a versatile and beginner-friendly programming language...",
      "visibility": "all",
      "metadata": {
        "subject": "Computer Science",
        "difficulty": "beginner",
        "created_date": "2026-01-03"
      }
    },
    {
      "id": "doc_002",
      "title": "Assignment 1: Variables and Data Types",
      "content": "Complete the following exercises on Python variables...",
      "visibility": "student",
      "metadata": {
        "subject": "Computer Science",
        "type": "assignment",
        "due_date": "2026-01-10"
      }
    },
    {
      "id": "doc_003",
      "title": "Assignment 1 - Answer Key",
      "content": "Solutions to Assignment 1...",
      "visibility": "teacher",
      "metadata": {
        "subject": "Computer Science",
        "type": "solution",
        "confidential": true
      }
    }
  ]
}
```

### 6.2 Upload Data via SCP (from Colleague's Machine)

```bash
# From colleague's computer:
scp sample_data.json pi@<RASPBERRY_PI_IP>:/home/pi/mcp-thesis/data/incoming/
```

### 6.3 Monitor Data Loading

```bash
# Watch data-watcher logs
docker-compose logs -f data-watcher
```

You should see:
```
INFO: Detected new file: sample_data.json
INFO: Parsing and validating...
INFO: Generating embeddings...
INFO: Inserting 3 documents into Qdrant...
INFO: Successfully loaded 3 documents
INFO: Moved to processed/sample_data.json
```

---

## 🧪 Step 7: Testing

### 7.1 Test Health Endpoint

```bash
curl http://localhost/health
```

Expected:
```json
{"status": "ok", "version": "2.0.0"}
```

### 7.2 Test OAuth Login

```bash
curl -X POST http://localhost/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=student1&password=test123"
```

Expected:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "...",
    "username": "student1",
    "role": "student",
    ...
  }
}
```

### 7.3 Test MCP Search (as Student)

```bash
TOKEN="<ACCESS_TOKEN_FROM_ABOVE>"

curl -X POST http://localhost/mcp/tools/vector_search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Python programming", "limit": 5}'
```

Expected (student sees only student+all content):
```json
{
  "results": [
    {"id": "doc_001", "title": "Welcome to Python Programming", ...},
    {"id": "doc_002", "title": "Assignment 1: Variables...", ...}
  ],
  "total": 2,
  "filtered_by_role": "student"
}
```

**Note**: `doc_003` (teacher-only) should NOT appear!

### 7.4 Test MCP Search (as Teacher)

```bash
# Login as teacher
curl -X POST http://localhost/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=teacher1&password=test123"

TOKEN="<TEACHER_ACCESS_TOKEN>"

curl -X POST http://localhost/mcp/tools/vector_search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Python programming", "limit": 5}'
```

Expected (teacher sees ALL content):
```json
{
  "results": [
    {"id": "doc_001", "title": "Welcome to Python Programming", ...},
    {"id": "doc_002", "title": "Assignment 1: Variables...", ...},
    {"id": "doc_003", "title": "Assignment 1 - Answer Key", ...}
  ],
  "total": 3,
  "filtered_by_role": "teacher"
}
```

---

## 📈 Step 8: Monitoring & Maintenance

### 8.1 View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f mcp-server
docker-compose logs -f oauth-server
docker-compose logs -f data-watcher
```

### 8.2 Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart mcp-server
```

### 8.3 Backup Qdrant Data

```bash
# Manual backup
./scripts/backup_qdrant.sh

# Or use Docker volume backup
docker run --rm -v mcp-thesis_qdrant_storage:/data \
  -v $(pwd)/data/backups:/backup \
  alpine tar czf /backup/qdrant-$(date +%Y%m%d).tar.gz /data
```

### 8.4 Monitor System Resources

```bash
# CPU, RAM, Disk
htop

# Docker stats
docker stats
```

---

## 🔒 Step 9: Security Hardening

### 9.1 Change Default Passwords

```bash
# Update admin password
python3 scripts/setup_users.py --update-password admin
```

### 9.2 Enable Firewall

```bash
sudo ufw status
sudo ufw enable
```

### 9.3 Setup Automatic Updates

```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 9.4 Setup Fail2Ban (Protect SSH)

```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 9.5 Regular Backups

Add to crontab:
```bash
crontab -e
```

Add:
```cron
# Daily Qdrant backup at 2 AM
0 2 * * * /home/pi/mcp-thesis/scripts/backup_qdrant.sh

# Weekly full backup
0 3 * * 0 tar czf /home/pi/backups/mcp-full-$(date +\%Y\%m\%d).tar.gz /home/pi/mcp-thesis
```

---

## 🛠️ Step 10: Systemd Service (Auto-Start on Boot)

### 10.1 Create Systemd Service File

```bash
sudo nano /etc/systemd/system/mcp-thesis.service
```

Content:
```ini
[Unit]
Description=MCP Thesis Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/pi/mcp-thesis
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
User=pi

[Install]
WantedBy=multi-user.target
```

### 10.2 Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable mcp-thesis.service
sudo systemctl start mcp-thesis.service
sudo systemctl status mcp-thesis.service
```

---

## 📝 Step 11: Colleague Data Upload Instructions

### For Your Colleague

**To upload new educational content:**

1. **Prepare JSON file** following the format:
```json
{
  "documents": [
    {
      "id": "unique_id",
      "title": "Document Title",
      "content": "Document content...",
      "visibility": "student" | "teacher" | "all",
      "metadata": {...}
    }
  ]
}
```

2. **Upload via SCP**:
```bash
scp your_data.json pi@<SERVER_IP>:/home/pi/mcp-thesis/data/incoming/
```

3. **Monitor processing**:
- File will be automatically detected
- Processed within 30 seconds
- Moved to `/data/processed/` when complete
- Check `/data/failed/` if there are errors

---

## 🚨 Troubleshooting

### Issue: Cannot access server externally

**Solution:**
1. Check port forwarding on router
2. Verify public IP: `curl ifconfig.me`
3. Check firewall: `sudo ufw status`
4. Test locally first: `curl http://localhost/health`

### Issue: JWT tokens not working

**Solution:**
1. Verify JWT_SECRET_KEY in `.env`
2. Restart OAuth server: `docker-compose restart oauth-server`
3. Check token expiration time

### Issue: Student can see teacher content

**Solution:**
1. Check Qdrant document visibility field
2. Verify RBAC filtering in code
3. Check JWT role claim: Decode token at jwt.io

### Issue: Data not loading from incoming/

**Solution:**
1. Check data-watcher logs: `docker-compose logs data-watcher`
2. Verify JSON format
3. Check file permissions: `ls -la data/incoming/`
4. Manually test parser: `python scripts/test_parser.py data/incoming/file.json`

### Issue: High memory usage

**Solution:**
1. Reduce Qdrant cache size in docker-compose.yml
2. Limit embedding model batch size
3. Use smaller embedding model (e.g., all-MiniLM-L6-v2)
4. Add swap space

---

## 📞 Support Contacts

- **Technical Issues**: [Your Email]
- **Access Requests**: [Admin Email]
- **Data Upload Issues**: [Data Manager Email]

---

## ✅ Deployment Checklist

- [ ] Raspberry Pi configured with static IP
- [ ] Docker and Docker Compose installed
- [ ] Project cloned and .env configured
- [ ] All Docker containers running
- [ ] Admin user created
- [ ] Test users created (student + teacher)
- [ ] Port forwarding configured
- [ ] Domain DNS configured (if applicable)
- [ ] SSL certificates obtained (via Caddy)
- [ ] Initial data loaded and tested
- [ ] RBAC tested (student vs teacher access)
- [ ] Backup scripts configured
- [ ] Systemd service enabled
- [ ] Monitoring setup
- [ ] Security hardening complete
- [ ] Documentation provided to users

---

**Deployment Complete! 🎉**

Your MCP Educational Server is now production-ready and accessible to students and teachers with proper role-based access control.
