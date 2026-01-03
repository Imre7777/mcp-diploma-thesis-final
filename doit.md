cd "C:\Users\imreo\Documents\MCP_diploma_thesis_final"

# Initialize git repository
git init

# Create .gitignore
@"
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/
*.egg
venv/
env/

# Environment files
.env
.env.local
*.env.bak*

# Data directories
data/incoming/*
data/processed/*
data/failed/*
data/backups/*
data/qdrant_storage/
data/oauth_db/

# Backup folder (reference only, not needed in repo)
backup/

# Logs
*.log
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Docker volumes
volumes/
*.db
*.sqlite
*.sqlite3

# Large files
*.zip
*.tar.gz
"@ | Out-File -FilePath .gitignore -Encoding utf8

# Configure git (if not already done)
git config user.name "Obermüller Imre"
git config user.email "imre.obermueller@gmail.com"

# Stage all files
git add .

# Initial commit
git commit -m "Initial commit: Project documentation and architecture

- Complete system architecture with RBAC
- Custom OAuth server design  
- MCP Streaming protocol
- Role-based data filtering (student/teacher)
- Automated data pipeline
- Comprehensive English documentation
- Deployment guide for Raspberry Pi
"

# Add remote
git remote add origin https://github.com/Imre7777/mcp-diploma-thesis-final.git

# Rename branch to main
git branch -M main

# Push to GitHub
git push -u origin main