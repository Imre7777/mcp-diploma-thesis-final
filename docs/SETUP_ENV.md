# Environment Setup Instructions

## Create Your .env File

**IMPORTANT**: Create a `.env` file in the project root with your actual credentials:

```bash
# Copy the example file
copy .env.example .env

# OR create manually with these values:
```

```env
# Scalekit OAuth Configuration
SCALEKIT_ENV_URL=https://mcpeduauth.scalekit.dev
SCALEKIT_CLIENT_ID=skc_106606852871095042
SCALEKIT_CLIENT_SECRET=test_7HcNL41bPsdBkq2F2VDHbuWvMGkrT6aESiqkZdfI5avRSjb0Rf6z3ie2xFoeIcic

# OAuth Settings
OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback
OAUTH_SCOPES=openid profile email

# OpenAI API
OPENAI_API_KEY=your-actual-openai-api-key

# Server Configuration
HTTP_HOST=0.0.0.0
HTTP_PORT=8000
VECTOR_DB_URL=http://localhost:6334
DEFAULT_COLLECTION=educational_content
ENABLE_RBAC=True
DEFAULT_USER_ROLE=public

# Security (generate a secure key!)
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Session settings
SESSION_COOKIE_NAME=mcp_session
SESSION_MAX_AGE=86400

# Development
DEBUG=True
LOG_LEVEL=INFO
```

## Next Steps

1. ✅ Create `.env` file with your credentials
2. ✅ Replace `your-actual-openai-api-key` with real OpenAI key
3. ✅ Generate secure JWT_SECRET_KEY
4. ✅ In Scalekit dashboard, set redirect URI: `http://localhost:8000/auth/callback`
5. ✅ In Scalekit dashboard, create roles: public, student, teacher, admin

Then we'll implement the OAuth middleware!
