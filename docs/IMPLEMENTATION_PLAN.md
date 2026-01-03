# Implementation Plan - MCP Educational Server

## Comprehensive Step-by-Step Development Guide

**Project**: MCP Server with RBAC and Streaming  
**Timeline**: 5 Weeks  
**Author**: Obermüller Imre

---

## 📅 Week 1: Foundation & Infrastructure

### Day 1-2: Project Setup

#### Tasks:
1. **Create Project Structure**
   ```bash
   mkdir -p MCP_diploma_thesis_final/{src/{auth,database,rbac,tools,streaming,server,utils,config},data/{incoming,processed,failed,backups},scripts,tests,docs}
   cd MCP_diploma_thesis_final
   ```

2. **Initialize Git Repository**
   ```bash
   git init
   git remote add origin <NEW_REPO_URL>
   ```

3. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```

4. **Create requirements.txt**
   ```txt
   # Core Framework
   fastapi==0.109.0
   uvicorn[standard]==0.27.0
   pydantic==2.5.3
   pydantic-settings==2.1.0
   
   # MCP SDK
   mcp==0.9.0
   
   # Database
   qdrant-client==1.7.0
   
   # Authentication
   pyjwt==2.8.0
   passlib[bcrypt]==1.7.4
   python-multipart==0.0.6
   
   # Embeddings
   sentence-transformers==2.3.1
   
   # File Watching
   watchdog==4.0.0
   
   # HTTP Client
   httpx==0.26.0
   
   # Utilities
   python-dotenv==1.0.0
   pyyaml==6.0.1
   
   # Testing
   pytest==7.4.4
   pytest-asyncio==0.23.3
   pytest-cov==4.1.0
   httpx==0.26.0
   ```

5. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

6. **Create .env.example**
   ```env
   # Server Configuration
   MCP_SERVER_HOST=0.0.0.0
   MCP_SERVER_PORT=8000
   OAUTH_SERVER_PORT=8001
   
   # Qdrant Configuration
   QDRANT_HOST=localhost
   QDRANT_PORT=6333
   QDRANT_COLLECTION=educational_content
   
   # JWT Configuration
   JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
   JWT_ALGORITHM=HS256
   JWT_EXPIRATION_HOURS=1
   JWT_REFRESH_EXPIRATION_DAYS=7
   
   # Embedding Model
   EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   
   # File Watching
   DATA_INCOMING_DIR=/data/incoming
   DATA_PROCESSED_DIR=/data/processed
   DATA_FAILED_DIR=/data/failed
   
   # Logging
   LOG_LEVEL=INFO
   LOG_FILE=/var/log/mcp_server.log
   ```

---

### Day 3-4: Docker Setup

#### Create docker-compose.yml:
```yaml
version: '3.8'

services:
  # Qdrant Vector Database
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./data/qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__API_KEY=${QDRANT_API_KEY:-}
    restart: unless-stopped
    networks:
      - mcp_network

  # Custom OAuth Server
  oauth-server:
    build:
      context: .
      dockerfile: Dockerfile.oauth
    container_name: oauth-server
    ports:
      - "8001:8001"
    volumes:
      - ./src:/app/src
      - ./data/oauth_db:/app/data
    environment:
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - DATABASE_URL=sqlite:///./data/users.db
    depends_on:
      - qdrant
    restart: unless-stopped
    networks:
      - mcp_network

  # MCP Server
  mcp-server:
    build:
      context: .
      dockerfile: Dockerfile.mcp
    container_name: mcp-server
    ports:
      - "8000:8000"
    volumes:
      - ./src:/app/src
      - ./data:/app/data
    environment:
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
      - OAUTH_SERVER_URL=http://oauth-server:8001
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      - qdrant
      - oauth-server
    restart: unless-stopped
    networks:
      - mcp_network

  # File Watcher (Data Pipeline)
  data-watcher:
    build:
      context: .
      dockerfile: Dockerfile.watcher
    container_name: data-watcher
    volumes:
      - ./data/incoming:/data/incoming
      - ./data/processed:/data/processed
      - ./data/failed:/data/failed
    environment:
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
    depends_on:
      - qdrant
    restart: unless-stopped
    networks:
      - mcp_network

  # Caddy Reverse Proxy
  caddy:
    image: caddy:2-alpine
    container_name: caddy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - ./data/caddy_data:/data
      - ./data/caddy_config:/config
    depends_on:
      - mcp-server
      - oauth-server
    restart: unless-stopped
    networks:
      - mcp_network

networks:
  mcp_network:
    driver: bridge

volumes:
  qdrant_storage:
  oauth_db:
  caddy_data:
  caddy_config:
```

#### Create Caddyfile:
```caddyfile
# Main domain configuration
{$DOMAIN:localhost} {
    # OAuth login endpoint
    handle /oauth/* {
        reverse_proxy oauth-server:8001
    }

    # MCP Server endpoints
    handle /mcp/* {
        # JWT validation
        @authenticated {
            header Authorization Bearer*
        }
        
        handle @authenticated {
            reverse_proxy mcp-server:8000
        }
        
        handle {
            redir /oauth/login
        }
    }

    # Health check (public)
    handle /health {
        reverse_proxy mcp-server:8000
    }

    # Rate limiting
    rate_limit {
        zone dynamic {
            key {remote_host}
            events 100
            window 1m
        }
    }

    # TLS
    tls {$EMAIL:admin@example.com}

    # Security headers
    header {
        X-Frame-Options "DENY"
        X-Content-Type-Options "nosniff"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
    }

    # Logging
    log {
        output file /var/log/caddy/access.log
    }
}
```

#### Create Dockerfiles:

**Dockerfile.mcp:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Expose port
EXPOSE 8000

# Run server
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Dockerfile.oauth:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

EXPOSE 8001

CMD ["python", "-m", "uvicorn", "src.oauth_server:app", "--host", "0.0.0.0", "--port", "8001"]
```

**Dockerfile.watcher:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY scripts/watch_and_load.py ./

CMD ["python", "watch_and_load.py"]
```

---

### Day 5-7: Core Configuration

#### Create src/config/settings.py:
```python
"""
Configuration Management
All settings loaded from environment variables or .env file
"""

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Server Configuration
    mcp_server_host: str = "0.0.0.0"
    mcp_server_port: int = 8000
    oauth_server_port: int = 8001
    
    # Qdrant Configuration
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "educational_content"
    qdrant_api_key: Optional[str] = None
    
    # JWT Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 1
    jwt_refresh_expiration_days: int = 7
    
    # Embedding Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    
    # File Paths
    data_incoming_dir: str = "./data/incoming"
    data_processed_dir: str = "./data/processed"
    data_failed_dir: str = "./data/failed"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "/var/log/mcp_server.log"
    
    # OAuth Database
    database_url: str = "sqlite:///./data/users.db"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
```

---

## 📅 Week 2: Authentication & OAuth Server

### Day 1-2: User Database & Models

#### Create src/auth/models.py:
```python
"""
User and Role Data Models
Defines database schema for authentication
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserRole(str, Enum):
    """User roles for RBAC"""
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"

class User(BaseModel):
    """User model"""
    id: str
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None

class UserCreate(BaseModel):
    """User creation schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.STUDENT

class UserLogin(BaseModel):
    """Login request schema"""
    username: str
    password: str

class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User

class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str  # user_id
    username: str
    role: UserRole
    exp: datetime
    iat: datetime
```

#### Create src/database/user_db.py:
```python
"""
User Database Management
Handles CRUD operations for OAuth users
"""

import sqlite3
import uuid
from datetime import datetime
from typing import Optional, List
from passlib.context import CryptContext

from src.auth.models import User, UserCreate, UserRole
from src.config.settings import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserDatabase:
    """User database manager"""
    
    def __init__(self, db_url: str = settings.database_url):
        """Initialize database connection"""
        self.db_path = db_url.replace("sqlite:///", "")
        self._init_db()
    
    def _init_db(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                role TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        user_id = str(uuid.uuid4())
        hashed_password = pwd_context.hash(user_data.password)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO users (id, username, email, hashed_password, role)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, user_data.username, user_data.email, 
                  hashed_password, user_data.role.value))
            
            conn.commit()
            
            return User(
                id=user_id,
                username=user_data.username,
                email=user_data.email,
                role=user_data.role,
                is_active=True,
                created_at=datetime.now()
            )
        finally:
            conn.close()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Retrieve user by username"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, username, email, role, is_active, created_at, last_login
                FROM users WHERE username = ?
            """, (username,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return User(
                id=row[0],
                username=row[1],
                email=row[2],
                role=UserRole(row[3]),
                is_active=bool(row[4]),
                created_at=datetime.fromisoformat(row[5]),
                last_login=datetime.fromisoformat(row[6]) if row[6] else None
            )
        finally:
            conn.close()
    
    def verify_password(self, username: str, password: str) -> bool:
        """Verify user password"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT hashed_password FROM users WHERE username = ?
            """, (username,))
            
            row = cursor.fetchone()
            if not row:
                return False
            
            return pwd_context.verify(password, row[0])
        finally:
            conn.close()
    
    def update_last_login(self, username: str):
        """Update user's last login timestamp"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE users SET last_login = CURRENT_TIMESTAMP
                WHERE username = ?
            """, (username,))
            conn.commit()
        finally:
            conn.close()
```

---

### Day 3-5: JWT Management & OAuth Endpoints

#### Create src/auth/jwt_manager.py:
```python
"""
JWT Token Management
Handles creation, validation, and refresh of JWT tokens
"""

import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional

from src.config.settings import settings
from src.auth.models import User, TokenPayload, UserRole

class JWTManager:
    """JWT token manager"""
    
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_hours = settings.jwt_expiration_hours
        self.refresh_token_expire_days = settings.jwt_refresh_expiration_days
    
    def create_access_token(self, user: User) -> str:
        """Create JWT access token"""
        now = datetime.utcnow()
        expires = now + timedelta(hours=self.access_token_expire_hours)
        
        payload = {
            "sub": user.id,
            "username": user.username,
            "role": user.role.value,
            "exp": expires,
            "iat": now,
            "type": "access"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token"""
        now = datetime.utcnow()
        expires = now + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "sub": user.id,
            "type": "refresh",
            "exp": expires,
            "iat": now
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Optional[Dict]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def extract_role(self, token: str) -> Optional[UserRole]:
        """Extract user role from JWT token"""
        payload = self.decode_token(token)
        if not payload:
            return None
        
        role_str = payload.get("role")
        try:
            return UserRole(role_str)
        except ValueError:
            return None

# Global JWT manager instance
jwt_manager = JWTManager()
```

#### Create src/oauth_server.py:
```python
"""
Custom OAuth Server
Handles user authentication and JWT token generation
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware

from src.auth.models import UserCreate, UserLogin, TokenResponse, User
from src.auth.jwt_manager import jwt_manager
from src.database.user_db import UserDatabase
from src.config.settings import settings

# Initialize FastAPI app
app = FastAPI(
    title="MCP OAuth Server",
    description="Authentication server for MCP Educational System",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/oauth/token")

# Database
user_db = UserDatabase()

@app.post("/oauth/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """
    Register a new user
    
    Args:
        user_data: User registration data
    
    Returns:
        Created user object
    
    Raises:
        HTTPException: If username/email already exists
    """
    try:
        user = user_db.create_user(user_data)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User registration failed: {str(e)}"
        )

@app.post("/oauth/token", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    User login - returns JWT tokens
    
    Args:
        form_data: OAuth2 form data (username, password)
    
    Returns:
        Access token, refresh token, and user data
    
    Raises:
        HTTPException: If credentials are invalid
    """
    # Verify credentials
    if not user_db.verify_password(form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user
    user = user_db.get_user_by_username(form_data.username)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Update last login
    user_db.update_last_login(form_data.username)
    
    # Generate tokens
    access_token = jwt_manager.create_access_token(user)
    refresh_token = jwt_manager.create_refresh_token(user)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_expiration_hours * 3600,
        user=user
    )

@app.post("/oauth/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """
    Refresh access token using refresh token
    
    Args:
        refresh_token: Valid refresh token
    
    Returns:
        New access token and refresh token
    
    Raises:
        HTTPException: If refresh token is invalid
    """
    payload = jwt_manager.decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    # Get user from database (implement get_user_by_id)
    # ... generate new tokens
    
    raise HTTPException(status_code=501, detail="Not implemented yet")

@app.get("/oauth/verify")
async def verify_token(token: str = Depends(oauth2_scheme)):
    """
    Verify JWT token validity
    
    Args:
        token: JWT access token
    
    Returns:
        Token payload if valid
    
    Raises:
        HTTPException: If token is invalid
    """
    payload = jwt_manager.decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return {"valid": True, "payload": payload}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "oauth-server"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.oauth_server_port)
```

---

**(Continue with Week 3-5 in next sections...)**

**Week 3**: RBAC, MCP Tools, Streaming Implementation  
**Week 4**: Data Pipeline, File Watcher, Qdrant Integration  
**Week 5**: Testing, Deployment, Documentation

Would you like me to continue with the remaining weeks?
