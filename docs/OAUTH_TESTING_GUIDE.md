# OAuth Flow Testing Guide

## 🚀 Quick Start

Your MCP Educational Server is running on **http://localhost:8000**

---

## 📋 Test Steps

### **Step 1: Test Health Endpoint** ✅
Open in browser or use curl:
```
http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "server": "mcp-educational-server",
  "initialized": true,
  "rbac_enabled": true,
  "authentication": "required"
}
```

---

### **Step 2: Test OAuth Login** 🔐

Open in browser:
```
http://localhost:8000/auth/login
```

**What happens:**
1. Your browser visits `/auth/login`
2. Server generates a `state` parameter for CSRF protection
3. Server redirects you to Scalekit authorization page
4. You'll see Scalekit's login page

**Expected redirect URL:**
```
https://mcpeduauth.scalekit.dev/authorize?
  response_type=code&
  client_id=skc_35934031996379566&
  redirect_uri=http://localhost:8000/auth/callback&
  state=<random-value>&
  scope=openid+profile+email
```

---

### **Step 3: Scalekit Configuration Required** ⚠️

Before you can test the full flow, you need to configure Scalekit:

#### In Scalekit Dashboard:

1. **Navigate to your MCP Server:**
   - Go to "MCP Servers" → "MCP Educational Server"

2. **Set Redirect URI:**
   - Add: `http://localhost:8000/auth/callback`
   - This tells Scalekit where to send users after login

3. **Set Initiate Login URI:**
   - Add: `http://localhost:8000/auth/login`
   - This is where users start the login process

4. **Create Test Connection:**
   - Go to "Connections" → "Add Connection"
   - Choose a provider (e.g., "Test SSO" or "Email/Password")
   - Enable for your organization

5. **Create Test Users with Roles:**
   - Student: `student@test.com` with role `student`
   - Teacher: `teacher@test.com` with role `teacher`
   - Admin: `admin@test.com` with role `admin`

---

### **Step 4: Test Full OAuth Flow** 🎯

Once Scalekit is configured:

1. **Start OAuth Flow:**
   ```
   http://localhost:8000/auth/login
   ```

2. **Login with Test User:**
   - Enter credentials on Scalekit page
   - Grant permissions if asked

3. **Receive Access Token:**
   - After successful login, you'll be redirected to `/auth/callback`
   - Server exchanges auth code for access token
   - You'll receive a JSON response:
   ```json
   {
     "access_token": "eyJhbGc...",
     "token_type": "Bearer",
     "expires_in": 3600,
     "refresh_token": "...",
     "id_token": "...",
     "scope": "openid profile email"
   }
   ```

4. **Copy the Access Token!** 📋

---

### **Step 5: Test Authenticated Endpoints** 🔒

Use the access token to access protected endpoints:

#### Get User Info:
```bash
curl -H "Authorization: Bearer <your-access-token>" \
  http://localhost:8000/auth/user
```

Expected response:
```json
{
  "user_id": "user_123",
  "email": "student@test.com",
  "name": "Student",
  "role": "student",
  "org_id": "org_456",
  "authenticated": true
}
```

#### Access API Docs:
Open in browser (with token in header - you'll need a browser extension):
```
http://localhost:8000/docs
```

---

### **Step 6: Test RBAC (Role-Based Access Control)** 👥

Test with different user roles to see RBAC in action:

#### Student Token:
- Can only see `access_level: student` content
- Limited access

#### Teacher Token:
- Can see `access_level: student` + `teacher` content
- Elevated access

#### Admin Token:
- Can see ALL content (student + teacher + admin)
- Full access

---

## 🐛 Troubleshooting

### **Issue: "Invalid redirect_uri" error**
**Solution:** Add `http://localhost:8000/auth/callback` to Scalekit allowed redirect URIs

### **Issue: "Unauthorized" (401)**
**Solution:** Make sure you're including the Bearer token in the Authorization header

### **Issue: "Token expired"**
**Solution:** Tokens expire after 1 hour. Go through OAuth flow again to get a new token

### **Issue: "Can't reach Scalekit"**
**Solution:** Check that `SCALEKIT_ENV_URL` in `.env` is correct

---

## 📊 Server Logs

Watch the server logs for debugging:
- Location: `terminals/8.txt`
- Shows all HTTP requests
- Shows authentication attempts
- Shows errors

Example log entries:
```
INFO - Redirecting to Scalekit login: state=abc123...
INFO - OAuth authentication successful!
INFO - Token validated successfully: user=student@test.com, role=student
```

---

## 🎯 Success Criteria

Your OAuth integration is working if:
- ✅ `/health` returns 200 OK
- ✅ `/auth/login` redirects to Scalekit
- ✅ After login, you get an access token
- ✅ `/auth/user` returns user info with Bearer token
- ✅ Different roles see different content (RBAC)

---

## 📝 Notes

- **Development Mode:** Currently returning tokens as JSON
- **Production:** Should use HTTP-only cookies or redirect to frontend
- **Token Storage:** Store securely, never in localStorage!
- **Token Refresh:** Implement refresh token flow for production

---

## 🚀 Next Steps

After successful OAuth testing:
1. ✅ Test RBAC with different roles
2. ✅ Test token expiration handling
3. ✅ Test concurrent authenticated requests
4. 📝 Document any issues
5. 🎉 Move to Week 3: Performance testing!
