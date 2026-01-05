# 🎯 Comprehensive Refactoring Plan - MCP Diploma Thesis

**Date**: January 3, 2026  
**Author**: Obermüller Imre  
**Goal**: Transform working MCP server into professional thesis-quality system with RBAC

---

## 📊 Current Status Analysis

### ✅ **What You Have (WORKING on Raspberry Pi)**

**Core Infrastructure:**
- Complete MCP server with **dual protocol** (stdio + HTTP streaming)
- **26 tools** organized in 8 categories
- **Qdrant** vector database backend (working)
- **FastAPI** HTTP server with uvicorn
- **SSE streaming** fully functional (sse_bus.py, sse_routes.py)
- **Entity resolution** system (teachers, rooms, classes, courses)
- **Caddy** reverse proxy with Basic Auth
- **Docker** containerization ready

**Code Structure:**
```
backup/mcp_vector_server/
├── server/
│   ├── base.py                 # Base server class
│   ├── stdio_server.py         # Stdio protocol
│   ├── http_server.py          # HTTP + SSE streaming ✅
│   ├── rpc.py                  # RPC handling
│   ├── sse_bus.py              # SSE event bus ✅
│   ├── sse_routes.py           # SSE endpoints ✅
│   ├── visibility.py           # Tool visibility filtering (basic)
│   └── api_key_middleware.py   # API key auth
├── tools/                      # 26 working tools ✅
├── utils/
│   ├── oauth.py                # JWT verification framework ✅
│   └── entity_resolver.py      # Entity resolution ✅
├── config/
│   └── server_config.py        # Pydantic settings ✅
└── backends/
    └── qdrant.py               # Working Qdrant integration ✅
```

**Authentication Framework:**
- `utils/oauth.py` - JWT verification with JWKS
- `server/api_key_middleware.py` - API key checking
- `config/server_config.py` - OAuth settings configured
- **Currently using**: Caddy Basic Auth (username/password)

---

## 🎓 **What's Missing for Thesis**

### 1. **RBAC (Role-Based Access Control)** - MAIN CONTRIBUTION ⭐
- [ ] User database with roles (student/teacher/admin)
- [ ] Role claim in JWT tokens
- [ ] Document-level visibility filtering (`visibility: "student"|"teacher"|"all"`)
- [ ] Query-time filtering based on user role
- [ ] RBAC middleware for all MCP tools

### 2. **User Management System**
- [ ] SQLite/PostgreSQL user database
- [ ] User CRUD operations
- [ ] Password hashing (bcrypt)
- [ ] User registration endpoint
- [ ] User management scripts

### 3. **Authentication Decision** - NEED TO DECIDE
**Option A: Caddy + Simple OAuth Server**
- Keep Caddy (already working)
- Add lightweight OAuth server for JWT generation
- Pros: Simple, you control everything
- Cons: You build OAuth yourself

**Option B: Scalekit Integration**
- Professional OAuth provider
- Enterprise-ready
- Pros: Professional, secure, maintained
- Cons: External dependency, learning curve

### 4. **Automated Data Pipeline**
- [ ] File watcher for `/data/incoming/`
- [ ] JSON parser with validation
- [ ] Automatic embedding generation
- [ ] Qdrant insertion with visibility metadata
- [ ] Colleague can upload via SCP

### 5. **Professional Documentation**
- [ ] English docstrings for all functions
- [ ] Clean code comments
- [ ] Remove German comments
- [ ] API documentation
- [ ] Architecture documentation

### 6. **Code Cleanup**
- [ ] Remove unused/broken code
- [ ] Fix duplicate SSE endpoints in http_server.py (lines 66-125)
- [ ] Remove `.broken` files
- [ ] Standardize naming conventions
- [ ] Type hints everywhere

---

## 🚀 Refactoring Strategy

### **Phase 1: Setup & Preparation** (Week 1)

#### Day 1-2: Project Structure
**Goal**: Create clean refactored structure alongside backup

**Tasks:**
1. Copy working code from `/backup/` to `/src/`
2. Clean directory structure:
```
src/
├── auth/                       # NEW - RBAC & user management
│   ├── __init__.py
│   ├── user_db.py             # User database (SQLite)
│   ├── jwt_manager.py         # JWT creation/validation
│   ├── rbac.py                # RBAC filtering logic
│   └── models.py              # User/Role Pydantic models
├── server/                     # FROM BACKUP (cleaned)
│   ├── base.py                # Keep as-is
│   ├── stdio_server.py        # Keep as-is
│   ├── http_server.py         # Clean up duplicate SSE
│   ├── rpc.py                 # Keep as-is
│   └── middleware.py          # NEW - RBAC middleware
├── tools/                      # FROM BACKUP (document)
│   ├── __init__.py            # Keep all 26 tools
│   ├── vector_tools.py        # Add RBAC filtering
│   └── ...                    # Document all tools
├── database/                   # FROM BACKUP
│   ├── qdrant_client.py       # Keep as-is
│   └── embeddings.py          # Keep as-is
├── pipeline/                   # NEW - Data pipeline
│   ├── file_watcher.py        # File monitoring
│   ├── data_loader.py         # JSON parser
│   └── processor.py           # Embedding + insertion
├── config/                     # FROM BACKUP (enhance)
│   └── settings.py            # Add RBAC settings
└── utils/                      # FROM BACKUP (clean)
    ├── oauth.py               # Keep & enhance
    ├── entity_resolver.py     # Keep as-is
    └── validation.py          # Keep as-is
```

3. Create `requirements.txt` from backup + new dependencies:
```txt
# Existing (from backup)
fastapi==0.109.0
uvicorn[standard]==0.27.0
qdrant-client==1.7.0
sentence-transformers==2.3.1
pydantic==2.5.3
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0  # Already there for JWT
sse-starlette==2.0.0              # Already there for SSE

# New for RBAC
passlib[bcrypt]==1.7.4            # Password hashing
python-multipart==0.0.6           # Form data
aiosqlite==0.19.0                 # Async SQLite

# New for data pipeline
watchdog==4.0.0                   # File monitoring
```

4. Create `.env.example`:
```env
# Existing Vector DB settings
VECTOR_DB_BACKEND=qdrant
VECTOR_DB_URL=http://localhost:6333
DEFAULT_COLLECTION=educational_content

# Existing Embedding settings
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=your_key_here
EMBEDDING_MODEL=text-embedding-3-small

# NEW - Authentication
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=1

# NEW - RBAC
ENABLE_RBAC=true
DEFAULT_ROLE=student

# NEW - Data Pipeline
DATA_INCOMING_DIR=./data/incoming
DATA_PROCESSED_DIR=./data/processed
DATA_FAILED_DIR=./data/failed

# Server
TRANSPORT=http
HTTP_HOST=0.0.0.0
HTTP_PORT=8080
```

**Deliverable**: Clean project structure with all working code copied and organized

---

#### Day 3-4: Code Cleanup & Documentation
**Goal**: Professional code quality

**Tasks:**
1. **Clean http_server.py**:
   - Remove duplicate SSE endpoints (lines 66-125 have 3 duplicate implementations!)
   - Keep only one clean SSE implementation
   - Add English docstrings

2. **Document all tools**:
   - Add English docstrings to all 26 tools
   - Document parameters with types
   - Document return values
   - Example:
```python
async def vector_search(
    query: str,
    collection: str = "educational_content",
    limit: int = 10
) -> List[Dict]:
    """
    Perform semantic vector similarity search.
    
    This tool searches the vector database using semantic similarity
    to find the most relevant documents based on the query text.
    
    Args:
        query: Search query text to embed and search for
        collection: Vector database collection name
        limit: Maximum number of results to return
        
    Returns:
        List of search results with scores and metadata
        
    Example:
        >>> results = await vector_search("Python programming", limit=5)
        >>> print(results[0]["title"])
        "Introduction to Python"
    """
```

3. **Remove broken files**:
   - Delete `__init__.py.broken.1756915741`
   - Remove any other `.broken` files

4. **Translate comments**:
   - Find all German comments: `# Alles andere mit Basic Auth`
   - Translate to English: `# Everything else requires Basic Auth`

**Deliverable**: Professional, well-documented codebase

---

### **Phase 2: RBAC Implementation** (Week 2) ⭐ THESIS CORE

#### Day 1-3: User Management & Database
**Goal**: User database with roles

**Files to create:**

1. **`src/auth/models.py`**:
```python
"""
User and Role Data Models

Defines the data structures for authentication and authorization.
"""

from enum import Enum
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserRole(str, Enum):
    """
    User roles for role-based access control.
    
    - STUDENT: Can only see student and public content
    - TEACHER: Can see all content including solutions
    - ADMIN: Full system access
    """
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class User(BaseModel):
    """User model with role information."""
    id: str
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.STUDENT


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User
```

2. **`src/auth/user_db.py`**:
```python
"""
User Database Management

Handles CRUD operations for user authentication and authorization.
Uses SQLite for simplicity (can upgrade to PostgreSQL later).
"""

import sqlite3
import uuid
from datetime import datetime
from typing import Optional
from passlib.context import CryptContext

from .models import User, UserCreate, UserRole

# Password hashing with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserDatabase:
    """Manages user data in SQLite database."""
    
    def __init__(self, db_path: str = "./data/users.db"):
        """
        Initialize user database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Create users table if it doesn't exist."""
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
        """
        Create a new user with hashed password.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user object
            
        Raises:
            sqlite3.IntegrityError: If username or email already exists
        """
        user_id = str(uuid.uuid4())
        hashed_password = pwd_context.hash(user_data.password)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO users (id, username, email, hashed_password, role)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id,
                user_data.username,
                user_data.email,
                hashed_password,
                user_data.role.value
            ))
            
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
    
    def verify_password(self, username: str, password: str) -> bool:
        """
        Verify user password.
        
        Args:
            username: Username to verify
            password: Plain text password to check
            
        Returns:
            True if password is correct, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT hashed_password FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            
            if not row:
                return False
            
            return pwd_context.verify(password, row[0])
        finally:
            conn.close()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve user by username.
        
        Args:
            username: Username to look up
            
        Returns:
            User object if found, None otherwise
        """
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
```

3. **`src/auth/jwt_manager.py`**:
```python
"""
JWT Token Management

Handles creation and validation of JWT tokens with role claims.
"""

import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional

from config.settings import settings
from .models import User, UserRole


class JWTManager:
    """Manages JWT token lifecycle."""
    
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.expiration_hours = settings.jwt_expiration_hours
    
    def create_token(self, user: User) -> str:
        """
        Create JWT access token with role claim.
        
        Args:
            user: User object
            
        Returns:
            JWT token string
        """
        now = datetime.utcnow()
        expires = now + timedelta(hours=self.expiration_hours)
        
        # IMPORTANT: Include role in token claims!
        payload = {
            "sub": user.id,
            "username": user.username,
            "role": user.role.value,  # ⭐ RBAC: Role in token
            "exp": expires,
            "iat": now,
            "type": "access"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Optional[Dict]:
        """
        Decode and validate JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload if valid, None otherwise
        """
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
        """
        Extract user role from JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            UserRole if valid, None otherwise
        """
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

**Deliverable**: User management system with JWT tokens containing role claims

---

#### Day 4-5: RBAC Filtering Logic
**Goal**: Implement role-based query filtering

**File to create: `src/auth/rbac.py`**:

```python
"""
Role-Based Access Control (RBAC)

Core filtering logic for educational content access control.

VISIBILITY RULES:
- "all": Visible to everyone (students AND teachers)
- "student": Visible to students AND teachers
- "teacher": Visible ONLY to teachers (e.g., solutions, answer keys)
"""

from typing import Dict, List, Any, Optional
from .models import UserRole
import logging

logger = logging.getLogger(__name__)


class RBACFilter:
    """Implements role-based filtering for vector search results."""
    
    @staticmethod
    def build_qdrant_filter(role: UserRole) -> Optional[Dict[str, Any]]:
        """
        Build Qdrant filter based on user role.
        
        Args:
            role: User role (student, teacher, admin)
            
        Returns:
            Qdrant filter dict or None (no filter for teachers)
            
        Examples:
            Student filter:
            {
                "must": [{
                    "key": "visibility",
                    "match": {"any": ["student", "all"]}
                }]
            }
            
            Teacher filter: None (see everything)
        """
        if role == UserRole.STUDENT:
            # Students can only see "student" and "all" content
            return {
                "must": [{
                    "key": "visibility",
                    "match": {"any": ["student", "all"]}
                }]
            }
        elif role in (UserRole.TEACHER, UserRole.ADMIN):
            # Teachers and admins see everything - no filter
            return None
        else:
            # Unknown role: restrict to public only
            logger.warning(f"Unknown role: {role}, restricting to 'all' only")
            return {
                "must": [{
                    "key": "visibility",
                    "match": {"value": "all"}
                }]
            }
    
    @staticmethod
    def filter_results(results: List[Dict], role: UserRole) -> List[Dict]:
        """
        Post-query filtering of results (safety layer).
        
        This is a safety layer in case Qdrant filter didn't work.
        Should normally not filter anything if Qdrant filter works correctly.
        
        Args:
            results: Search results from Qdrant
            role: User role
            
        Returns:
            Filtered results
        """
        if role in (UserRole.TEACHER, UserRole.ADMIN):
            # Teachers see everything
            return results
        
        # Students: filter out teacher-only content
        filtered = []
        for result in results:
            visibility = result.get("payload", {}).get("visibility", "all")
            
            if visibility in ("student", "all"):
                filtered.append(result)
            else:
                logger.info(
                    f"Filtered out teacher-only content for student: {result.get('id')}"
                )
        
        return filtered
    
    @staticmethod
    def log_access(user_id: str, role: UserRole, query: str, result_count: int):
        """
        Log access attempts for audit trail.
        
        Args:
            user_id: User ID
            role: User role
            query: Search query
            result_count: Number of results returned
        """
        logger.info(
            f"RBAC Access: user={user_id}, role={role.value}, "
            f"query='{query[:50]}...', results={result_count}"
        )
```

**Deliverable**: RBAC filtering logic that restricts student access

---

#### Day 6-7: Integration with Existing Server
**Goal**: Add RBAC middleware to MCP server

**File to create: `src/server/middleware.py`**:

```python
"""
RBAC Middleware for MCP Server

Extracts user role from JWT and applies filtering to all MCP tools.
"""

from fastapi import Request, HTTPException
from typing import Optional

from auth.jwt_manager import jwt_manager
from auth.models import UserRole
from auth.rbac import RBACFilter


class RBACMiddleware:
    """Middleware to enforce role-based access control."""
    
    @staticmethod
    async def extract_user_role(request: Request) -> UserRole:
        """
        Extract user role from JWT token in request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            User role
            
        Raises:
            HTTPException: If token is missing or invalid
        """
        # Get Authorization header
        auth_header = request.headers.get("Authorization", "")
        
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Missing or invalid Authorization header"
            )
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        # Extract role from token
        role = jwt_manager.extract_role(token)
        
        if not role:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
        
        return role
    
    @staticmethod
    def add_rbac_to_query(query_params: dict, role: UserRole) -> dict:
        """
        Add RBAC filter to Qdrant query parameters.
        
        Args:
            query_params: Original query parameters
            role: User role
            
        Returns:
            Query parameters with RBAC filter added
        """
        rbac_filter = RBACFilter.build_qdrant_filter(role)
        
        if rbac_filter:
            # Merge with existing filter if present
            existing_filter = query_params.get("query_filter")
            if existing_filter:
                # Combine filters with AND logic
                query_params["query_filter"] = {
                    "must": [
                        *existing_filter.get("must", []),
                        *rbac_filter.get("must", [])
                    ]
                }
            else:
                query_params["query_filter"] = rbac_filter
        
        return query_params
```

**Modify existing: `src/tools/vector_tools.py`**:

```python
# Add at the top of vector_search function
async def vector_search(
    query: str,
    collection: str = "educational_content",
    limit: int = 10,
    request: Request = None  # NEW: Add request parameter
) -> List[Dict]:
    """
    Perform semantic vector similarity search with RBAC.
    ...
    """
    # Extract user role from JWT token
    role = await RBACMiddleware.extract_user_role(request)
    
    # Build query parameters
    query_params = {
        "collection": collection,
        "query_vector": embedding,
        "limit": limit
    }
    
    # ⭐ ADD RBAC FILTER
    query_params = RBACMiddleware.add_rbac_to_query(query_params, role)
    
    # Execute search
    results = await qdrant_client.search(**query_params)
    
    # Safety layer: post-filter results
    results = RBACFilter.filter_results(results, role)
    
    # Log access for audit trail
    RBACFilter.log_access(
        user_id=request.user.id,
        role=role,
        query=query,
        result_count=len(results)
    )
    
    return results
```

**Deliverable**: RBAC fully integrated with all search tools

---

### **Phase 3: Authentication System** (Week 3)

#### Decision Point: Caddy OAuth vs Scalekit

**Recommendation**: **Use Caddy + Simple OAuth Server** ✅

**Reasons:**
1. You already have Caddy working
2. Complete control over authentication
3. Simpler for thesis demonstration
4. No external dependencies
5. Easier to test RBAC locally

**File to create: `src/auth/oauth_server.py`**:

```python
"""
Simple OAuth Server for MCP

Provides authentication endpoints and JWT token generation.
Runs alongside MCP server (can be same FastAPI app or separate).
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from .models import UserCreate, TokenResponse, UserLogin
from .user_db import UserDatabase
from .jwt_manager import jwt_manager

# Initialize FastAPI app
oauth_app = FastAPI(
    title="MCP OAuth Server",
    description="Authentication for MCP Educational System"
)

# Database
user_db = UserDatabase()


@oauth_app.post("/oauth/register", response_model=User, status_code=201)
async def register_user(user_data: UserCreate):
    """
    Register a new user.
    
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
            detail=f"Registration failed: {str(e)}"
        )


@oauth_app.post("/oauth/token", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    User login - returns JWT token with role claim.
    
    Args:
        form_data: OAuth2 form (username, password)
        
    Returns:
        JWT access token
        
    Raises:
        HTTPException: If credentials invalid
    """
    # Verify password
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
    
    # Generate JWT token with role claim
    access_token = jwt_manager.create_token(user)
    
    return TokenResponse(
        access_token=access_token,
        expires_in=3600,  # 1 hour
        user=user
    )


@oauth_app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "oauth"}
```

**Update Caddyfile:**

```caddyfile
leowiki-mcp.stream {
    tls imre.obermueller@gmail.com
    
    # OAuth endpoints (public)
    handle /oauth/* {
        reverse_proxy http://leowiki-mcp:8000
    }
    
    # MCP endpoints (require JWT)
    @mcp {
        path /mcp* /sse*
        header Authorization Bearer*
    }
    
    handle @mcp {
        header Cache-Control "no-cache"
        header X-Accel-Buffering "no"
        reverse_proxy http://leowiki-mcp:8080
    }
    
    # Redirect to login if no token
    handle /mcp* /sse* {
        redir /oauth/login
    }
    
    # Health check (public)
    handle /health {
        reverse_proxy http://leowiki-mcp:8080
    }
    
    log {
        output file /var/log/caddy/access.log
    }
}
```

**Deliverable**: OAuth server generating JWT tokens with role claims

---

### **Phase 4: Data Pipeline** (Week 4)

#### Goal: Automated colleague upload system

**File to create: `scripts/watch_and_load.py`**:

```python
"""
Automated Data Pipeline

Watches /data/incoming/ for new JSON files from colleagues.
Automatically processes, embeds, and inserts into Qdrant with visibility metadata.
"""

import asyncio
import json
import logging
import shutil
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from database.qdrant_client import QdrantClient
from database.embeddings import EmbeddingProvider
from config.settings import settings

logger = logging.getLogger(__name__)


class DataFileHandler(FileSystemEventHandler):
    """Handles new file detection in incoming directory."""
    
    def __init__(self, processor):
        self.processor = processor
    
    def on_created(self, event):
        """Called when a new file is created."""
        if not event.is_directory and event.src_path.endswith(".json"):
            logger.info(f"New file detected: {event.src_path}")
            asyncio.run(self.processor.process_file(event.src_path))


class DataProcessor:
    """Processes educational content JSON files."""
    
    def __init__(self):
        self.qdrant = QdrantClient()
        self.embeddings = EmbeddingProvider()
        self.incoming_dir = Path(settings.data_incoming_dir)
        self.processed_dir = Path(settings.data_processed_dir)
        self.failed_dir = Path(settings.data_failed_dir)
    
    async def process_file(self, file_path: str):
        """
        Process a JSON file: parse, validate, embed, insert to Qdrant.
        
        Args:
            file_path: Path to JSON file
        """
        file_path = Path(file_path)
        
        try:
            logger.info(f"Processing file: {file_path.name}")
            
            # 1. Parse JSON
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 2. Validate structure
            documents = self._validate_structure(data)
            
            # 3. Process each document
            for doc in documents:
                await self._process_document(doc)
            
            # 4. Move to processed directory
            shutil.move(str(file_path), str(self.processed_dir / file_path.name))
            logger.info(f"Successfully processed: {file_path.name}")
            
        except Exception as e:
            logger.error(f"Failed to process {file_path.name}: {e}")
            shutil.move(str(file_path), str(self.failed_dir / file_path.name))
    
    def _validate_structure(self, data: dict) -> list:
        """
        Validate JSON structure.
        
        Expected format:
        {
            "documents": [
                {
                    "id": "doc_001",
                    "title": "...",
                    "content": "...",
                    "visibility": "student" | "teacher" | "all",
                    "metadata": {...}
                }
            ]
        }
        """
        if "documents" not in data:
            raise ValueError("Missing 'documents' key in JSON")
        
        documents = data["documents"]
        
        for doc in documents:
            # Required fields
            required = ["id", "title", "content", "visibility"]
            for field in required:
                if field not in doc:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate visibility
            if doc["visibility"] not in ("student", "teacher", "all"):
                raise ValueError(
                    f"Invalid visibility: {doc['visibility']}. "
                    f"Must be 'student', 'teacher', or 'all'"
                )
        
        return documents
    
    async def _process_document(self, doc: dict):
        """
        Process single document: generate embedding and insert to Qdrant.
        
        Args:
            doc: Document dictionary
        """
        # Generate embedding for content
        embedding = await self.embeddings.embed_text(doc["content"])
        
        # ⭐ Prepare payload with visibility metadata
        payload = {
            "id": doc["id"],
            "title": doc["title"],
            "content": doc["content"],
            "visibility": doc["visibility"],  # KEY FIELD for RBAC!
            "metadata": doc.get("metadata", {})
        }
        
        # Insert into Qdrant
        await self.qdrant.insert(
            collection="educational_content",
            id=doc["id"],
            vector=embedding,
            payload=payload
        )
        
        logger.info(
            f"Inserted document: {doc['id']} "
            f"(visibility: {doc['visibility']})"
        )


async def main():
    """Main entry point for file watcher."""
    processor = DataProcessor()
    
    # Setup file watcher
    event_handler = DataFileHandler(processor)
    observer = Observer()
    observer.schedule(
        event_handler,
        str(processor.incoming_dir),
        recursive=False
    )
    
    # Start watching
    observer.start()
    logger.info(f"Watching directory: {processor.incoming_dir}")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
```

**Instructions for colleague:**

Create file: `docs/COLLEAGUE_UPLOAD_INSTRUCTIONS.md`:

```markdown
# Data Upload Instructions for Colleagues

## How to Add Educational Content

### 1. Prepare JSON File

Create a JSON file with the following format:

```json
{
  "documents": [
    {
      "id": "doc_001",
      "title": "Introduction to Python",
      "content": "Python is a versatile programming language...",
      "visibility": "all",
      "metadata": {
        "subject": "Computer Science",
        "difficulty": "beginner",
        "created_date": "2026-01-03"
      }
    },
    {
      "id": "doc_002",
      "title": "Assignment 1 - Answer Key",
      "content": "Solutions to assignment 1...",
      "visibility": "teacher",
      "metadata": {
        "subject": "Computer Science",
        "confidential": true
      }
    }
  ]
}
```

### 2. Visibility Options

- **`"all"`**: Visible to everyone (students AND teachers)
- **`"student"`**: Visible to students AND teachers
- **`"teacher"`**: Visible ONLY to teachers (solutions, answer keys)

### 3. Upload via SCP

```bash
scp your_content.json pi@leowiki-mcp.stream:/data/incoming/
```

### 4. Automatic Processing

- File will be detected within 5 seconds
- Automatically embedded and inserted into database
- Moved to `/data/processed/` when complete
- Check `/data/failed/` if there are errors

### 5. Verify Upload

Check logs:
```bash
docker logs data-watcher -f
```

You should see:
```
INFO: New file detected: your_content.json
INFO: Processing file: your_content.json
INFO: Inserted document: doc_001 (visibility: all)
INFO: Successfully processed: your_content.json
```
```

**Deliverable**: Automated data pipeline working end-to-end

---

### **Phase 5: Testing & Deployment** (Week 5)

#### Critical Tests for RBAC

**File to create: `tests/test_rbac.py`**:

```python
"""
RBAC Integration Tests

These tests verify that role-based access control works correctly.
This is the CORE of your thesis contribution!
"""

import pytest
from auth.models import UserRole
from auth.rbac import RBACFilter


class TestRBACFiltering:
    """Test role-based filtering logic."""
    
    def test_student_filter_generation(self):
        """Test that student filter only allows student and all content."""
        filter_dict = RBACFilter.build_qdrant_filter(UserRole.STUDENT)
        
        assert filter_dict is not None
        assert "must" in filter_dict
        assert filter_dict["must"][0]["key"] == "visibility"
        assert "student" in filter_dict["must"][0]["match"]["any"]
        assert "all" in filter_dict["must"][0]["match"]["any"]
        assert "teacher" not in filter_dict["must"][0]["match"]["any"]
    
    def test_teacher_no_filter(self):
        """Test that teachers have no filter (see everything)."""
        filter_dict = RBACFilter.build_qdrant_filter(UserRole.TEACHER)
        
        assert filter_dict is None  # No filter!
    
    def test_student_cannot_see_teacher_content(self):
        """
        CRITICAL TEST: Students must NOT see teacher-only content.
        
        This is the main security requirement of your thesis!
        """
        # Simulate search results with mixed visibility
        results = [
            {"id": "doc_001", "payload": {"visibility": "all"}},
            {"id": "doc_002", "payload": {"visibility": "student"}},
            {"id": "doc_003", "payload": {"visibility": "teacher"}},  # Should be filtered!
        ]
        
        # Filter as student
        filtered = RBACFilter.filter_results(results, UserRole.STUDENT)
        
        # Verify teacher content is removed
        assert len(filtered) == 2
        assert "doc_001" in [r["id"] for r in filtered]
        assert "doc_002" in [r["id"] for r in filtered]
        assert "doc_003" not in [r["id"] for r in filtered]  # ⭐ MUST NOT APPEAR
    
    def test_teacher_sees_everything(self):
        """Test that teachers see all content types."""
        results = [
            {"id": "doc_001", "payload": {"visibility": "all"}},
            {"id": "doc_002", "payload": {"visibility": "student"}},
            {"id": "doc_003", "payload": {"visibility": "teacher"}},
        ]
        
        filtered = RBACFilter.filter_results(results, UserRole.TEACHER)
        
        # Teachers see all 3
        assert len(filtered) == 3


@pytest.mark.asyncio
class TestRBACIntegration:
    """Integration tests with actual MCP server."""
    
    async def test_student_search_integration(self, test_client):
        """Test student search doesn't return teacher content."""
        # Login as student
        response = test_client.post("/oauth/token", data={
            "username": "student1",
            "password": "password123"
        })
        student_token = response.json()["access_token"]
        
        # Search for content
        response = test_client.post(
            "/mcp",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "method": "tools/call",
                "params": {
                    "name": "vector_search",
                    "arguments": {"query": "programming", "limit": 10}
                }
            }
        )
        
        results = response.json()["result"]["content"][0]["text"]
        results = json.loads(results)
        
        # Verify NO teacher-only content in results
        for result in results:
            assert result["payload"]["visibility"] != "teacher"
    
    async def test_teacher_search_integration(self, test_client):
        """Test teacher search returns ALL content."""
        # Login as teacher
        response = test_client.post("/oauth/token", data={
            "username": "teacher1",
            "password": "password123"
        })
        teacher_token = response.json()["access_token"]
        
        # Search for content
        response = test_client.post(
            "/mcp",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={
                "method": "tools/call",
                "params": {
                    "name": "vector_search",
                    "arguments": {"query": "programming", "limit": 10}
                }
            }
        )
        
        results = response.json()["result"]["content"][0]["text"]
        results = json.loads(results)
        
        # Teachers should see teacher-only content
        visibilities = [r["payload"]["visibility"] for r in results]
        # Should include teacher content (if it exists in test data)
        assert len(results) > 0
```

**Deliverable**: All tests passing, RBAC working correctly

---

## 📝 **Documentation Standards**

### Code Comments Template

```python
def function_name(param1: str, param2: int) -> Dict:
    """
    Short one-line description.
    
    Longer description explaining what this function does,
    why it exists, and any important implementation details.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When and why this exception is raised
        
    Example:
        >>> result = function_name("test", 5)
        >>> print(result)
        {"status": "ok"}
    """
```

---

## 🎯 **Final Checklist**

### Code Quality ✅
- [ ] All functions have English docstrings
- [ ] No German comments remain
- [ ] Type hints on all functions
- [ ] No unused imports
- [ ] No `.broken` files
- [ ] Clean git history

### RBAC Implementation ✅
- [ ] User database with roles
- [ ] JWT tokens with role claims
- [ ] Qdrant query filtering by role
- [ ] Post-query result filtering
- [ ] Audit logging
- [ ] Student cannot see teacher content ⭐

### Authentication ✅
- [ ] OAuth server working
- [ ] Login endpoint functional
- [ ] Registration endpoint functional
- [ ] JWT generation correct
- [ ] Token validation working
- [ ] Caddy integration complete

### Data Pipeline ✅
- [ ] File watcher running
- [ ] JSON validation working
- [ ] Embedding generation working
- [ ] Qdrant insertion successful
- [ ] Visibility metadata preserved
- [ ] Error handling robust

### Testing ✅
- [ ] RBAC tests passing
- [ ] Integration tests passing
- [ ] Manual testing complete
- [ ] Student/teacher scenarios verified

### Deployment ✅
- [ ] Docker containers building
- [ ] docker-compose working
- [ ] Caddy configuration correct
- [ ] TLS certificates working
- [ ] Accessible remotely
- [ ] All services healthy

### Documentation ✅
- [ ] README updated
- [ ] Architecture documented
- [ ] API documentation complete
- [ ] Colleague upload instructions
- [ ] Deployment guide updated
- [ ] Thesis documentation ready

---

## 🚀 **Getting Started**

### This Week (Week 1):

1. **Copy backup code to `/src/`**
   ```bash
   cd C:\Users\imreo\Documents\MCP_diploma_thesis_final
   
   # Copy server code
   cp -r backup/mcp_vector_server/server src/
   cp -r backup/mcp_vector_server/tools src/
   cp -r backup/mcp_vector_server/config src/
   cp -r backup/mcp_vector_server/backends src/database
   cp -r backup/mcp_vector_server/utils src/
   
   # Copy requirements
   cp backup/mcp_vector_server/requirements.txt .
   ```

2. **Clean up duplicate SSE code in http_server.py** (lines 66-125)

3. **Create user management skeleton**:
   ```bash
   mkdir src/auth
   touch src/auth/__init__.py
   touch src/auth/models.py
   touch src/auth/user_db.py
   touch src/auth/jwt_manager.py
   touch src/auth/rbac.py
   ```

4. **Create `.env` file** with settings

5. **Test that backup code still works** after copying

---

## 📊 **Time Estimate**

| Phase | Tasks | Time |
|-------|-------|------|
| Week 1 | Setup & Cleanup | 15-20 hours |
| Week 2 | RBAC Implementation | 20-25 hours |
| Week 3 | Authentication | 15-20 hours |
| Week 4 | Data Pipeline | 10-15 hours |
| Week 5 | Testing & Deployment | 15-20 hours |
| **Total** | **Complete System** | **75-100 hours** |

---

## ❓ **Next Steps & Questions**

### Immediate Actions:

1. **Confirm approach**: Does this refactoring plan make sense?

2. **Authentication decision**: Caddy + Simple OAuth (recommended) or Scalekit?

3. **Start Week 1**: Begin copying and cleaning up code?

4. **Timeline**: When do you need to finish? (Thesis deadline?)

---

**Let's start! Should I begin with Week 1, Day 1: Copying the code from backup to src/?** 🚀
