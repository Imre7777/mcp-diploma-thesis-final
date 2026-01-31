# 🔄 MCP Proxy Server - Vollständiger Implementierungsplan

## Für: LeoWiki MCP Multi-LLM Integration
## Stand: 08. Januar 2026

---

## 📋 Übersicht

Dieser Plan beschreibt die Entwicklung eines **MCP Proxy Servers**, der es ermöglicht, den Remote LeoWiki MCP Server mit OAuth 2.1 Authentifizierung in **allen gängigen LLM Desktop-Clients** zu nutzen (Claude Desktop, Cursor IDE, Cline, etc.).

### Problem ohne Proxy:
- ❌ Desktop-LLMs erwarten lokale MCP Server (stdio)
- ❌ Remote MCP Server mit OAuth 2.1 nicht direkt kompatibel
- ❌ Jeder Client müsste OAuth selbst implementieren

### Lösung mit Proxy:
- ✅ Proxy läuft lokal und spricht stdio (für LLMs)
- ✅ Proxy kommuniziert mit Remote Server via HTTPS + OAuth
- ✅ Einmalige OAuth-Authentifizierung, Token-Caching
- ✅ Funktioniert mit allen MCP-kompatiblen LLMs

---

## 🏗️ Architektur

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MULTI-LLM ARCHITEKTUR                         │
└─────────────────────────────────────────────────────────────────────┘

Desktop LLMs (stdio)              Proxy (lokal)          Remote Server
┌──────────────────┐              ┌──────────────┐      ┌─────────────┐
│                  │              │              │      │             │
│ Claude Desktop   │◄──stdio────►│              │      │  LeoWiki    │
│                  │              │              │      │  MCP Server │
└──────────────────┘              │              │      │             │
                                  │  MCP Proxy   │◄HTTP─┤ OAuth 2.1   │
┌──────────────────┐              │              │      │             │
│                  │              │  • stdio I/O │      │ ScaleKit    │
│ Cursor IDE       │◄──stdio────►│  • HTTP      │      │ Auth        │
│                  │              │  • OAuth     │      │             │
└──────────────────┘              │  • Cache     │      │ DokuWiki    │
                                  │              │      │ RAGFlow     │
┌──────────────────┐              └──────────────┘      └─────────────┘
│                  │                     │
│ Cline (VSCode)   │◄──stdio────────────┤
│                  │                     │
└──────────────────┘                     │
                                         │
┌──────────────────┐              ┌──────▼───────┐
│                  │              │              │
│ Andere LLMs...   │◄──stdio────►│ Token Cache  │
│                  │              │ (~/.leowiki) │
└──────────────────┘              └──────────────┘
```

---

## 🎯 Funktionsweise

### 1. **Initialer OAuth Flow (einmalig)**

```
User führt aus: leowiki-mcp-proxy auth

┌──────┐   1. Start Auth    ┌───────┐   2. Browser    ┌──────────┐
│ User │───────────────────►│ Proxy │────────────────►│ Browser  │
└──────┘                    └───────┘                 └──────────┘
                                │                           │
                                │                           │ 3. Login
                                │                           ▼
                                │                     ┌──────────┐
                                │    4. Callback      │ ScaleKit │
                                │◄────────────────────│   Auth   │
                                │                     └──────────┘
                                │
                                ▼ 5. Token speichern
                          ┌──────────┐
                          │  Cache   │
                          │ ~/.leowiki/
                          │  tokens   │
                          └──────────┘
```

### 2. **LLM Nutzung (automatisch)**

```
┌────────────┐    MCP Request     ┌───────┐    HTTP + Bearer    ┌────────┐
│   Claude   │────(stdio JSON)───►│ Proxy │────Token───────────►│ Remote │
│  Desktop   │                    │       │                     │  MCP   │
│            │◄──(stdio JSON)─────│       │◄────JSON───────────│ Server │
└────────────┘    MCP Response    └───────┘                     └────────┘
                                      │
                                      │ Token expired?
                                      ▼
                                  Refresh Token
                                  automatisch
```

---

## 📦 Projekt-Struktur

```
leowiki-mcp-proxy/
├── src/
│   ├── proxy/
│   │   ├── server.js           # Haupt-Proxy Server (stdio Handler)
│   │   ├── http_client.js      # HTTP Client für Remote MCP
│   │   └── protocol.js         # MCP Protocol Implementation
│   ├── auth/
│   │   ├── oauth_flow.js       # OAuth 2.1 Authorization Flow
│   │   ├── pkce.js             # PKCE Helper Functions
│   │   ├── token_manager.js    # Token Storage & Refresh
│   │   └── browser.js          # Browser Launch für Auth
│   ├── cache/
│   │   ├── token_cache.js      # Persistente Token-Speicherung
│   │   └── session_cache.js    # Session Management
│   ├── cli/
│   │   ├── auth_command.js     # CLI: leowiki-mcp-proxy auth
│   │   ├── status_command.js   # CLI: leowiki-mcp-proxy status
│   │   └── logout_command.js   # CLI: leowiki-mcp-proxy logout
│   ├── config/
│   │   └── settings.js         # Konfiguration laden
│   └── index.js                # Entry Point
├── bin/
│   └── leowiki-mcp-proxy       # Executable für npm -g
├── test/
│   ├── auth.test.js
│   ├── proxy.test.js
│   └── integration.test.js
├── config/
│   └── default.json            # Default Konfiguration
├── package.json
├── README.md
└── .env.example
```

---

## 🔧 Phase 1: Projekt Setup

### 1.1 Projekt initialisieren

```bash
mkdir leowiki-mcp-proxy
cd leowiki-mcp-proxy
npm init -y
```

### 1.2 Dependencies installieren

```json
{
  "name": "leowiki-mcp-proxy",
  "version": "1.0.0",
  "description": "Local MCP proxy for LeoWiki remote server with OAuth 2.1",
  "main": "src/index.js",
  "bin": {
    "leowiki-mcp-proxy": "./bin/leowiki-mcp-proxy"
  },
  "scripts": {
    "start": "node src/index.js",
    "auth": "node src/cli/auth_command.js",
    "test": "jest"
  },
  "dependencies": {
    "axios": "^1.6.0",
    "commander": "^11.0.0",
    "dotenv": "^16.0.0",
    "express": "^4.18.0",
    "open": "^9.0.0",
    "jsonwebtoken": "^9.0.0",
    "node-fetch": "^3.3.0"
  },
  "devDependencies": {
    "jest": "^29.0.0",
    "eslint": "^8.0.0"
  }
}
```

---

## 🔐 Phase 2: OAuth 2.1 Implementation

### 2.1 PKCE Helper Functions

**Datei: `src/auth/pkce.js`**

```javascript
const crypto = require('crypto');

/**
 * PKCE (Proof Key for Code Exchange) Helper
 * RFC 7636 für sicheren OAuth Flow
 */
class PKCEHelper {
  /**
   * Generiert Code Verifier (43-128 Zeichen)
   */
  static generateCodeVerifier() {
    return crypto.randomBytes(32).toString('base64url');
  }

  /**
   * Generiert Code Challenge aus Verifier
   * Verwendet SHA256 und base64url encoding
   */
  static generateCodeChallenge(verifier) {
    return crypto
      .createHash('sha256')
      .update(verifier)
      .digest('base64url');
  }

  /**
   * Generiert State für CSRF-Schutz
   */
  static generateState() {
    return crypto.randomBytes(16).toString('hex');
  }
}

module.exports = PKCEHelper;
```

### 2.2 OAuth Flow Implementation

**Datei: `src/auth/oauth_flow.js`**

```javascript
const express = require('express');
const open = require('open');
const axios = require('axios');
const PKCEHelper = require('./pkce');
const TokenManager = require('./token_manager');

class OAuthFlow {
  constructor(config) {
    this.config = config;
    this.tokenManager = new TokenManager();
    this.callbackServer = null;
  }

  /**
   * Startet den OAuth 2.1 Authorization Code Flow
   */
  async authenticate() {
    console.log('🔐 Starte OAuth 2.1 Authentifizierung...');

    // 1. PKCE Parameter generieren
    const codeVerifier = PKCEHelper.generateCodeVerifier();
    const codeChallenge = PKCEHelper.generateCodeChallenge(codeVerifier);
    const state = PKCEHelper.generateState();

    // 2. Callback Server starten
    const callbackData = await this.startCallbackServer(state, codeVerifier);

    // 3. Authorization URL bauen
    const authUrl = this.buildAuthorizationUrl(
      codeChallenge,
      state,
      callbackData.port
    );

    console.log('🌐 Öffne Browser für Login...');
    console.log(`   ${authUrl}`);

    // 4. Browser öffnen
    await open(authUrl);

    // 5. Auf Callback warten
    console.log('⏳ Warte auf Authentifizierung...');
    return callbackData.promise;
  }

  /**
   * Baut die Authorization URL
   */
  buildAuthorizationUrl(codeChallenge, state, callbackPort) {
    const authUrl = new URL(this.config.oauth.authorizationUrl);
    
    authUrl.searchParams.set('client_id', this.config.oauth.clientId);
    authUrl.searchParams.set('redirect_uri', `http://localhost:${callbackPort}/callback`);
    authUrl.searchParams.set('response_type', 'code');
    authUrl.searchParams.set('scope', 'openid profile email');
    authUrl.searchParams.set('state', state);
    authUrl.searchParams.set('code_challenge', codeChallenge);
    authUrl.searchParams.set('code_challenge_method', 'S256');

    return authUrl.toString();
  }

  /**
   * Startet lokalen HTTP Server für OAuth Callback
   */
  startCallbackServer(expectedState, codeVerifier) {
    return new Promise((resolve, reject) => {
      const app = express();
      let server;
      const port = 8765; // Fester Port für lokalen Callback

      app.get('/callback', async (req, res) => {
        const { code, state, error } = req.query;

        // Error Check
        if (error) {
          res.send('❌ Authentifizierung fehlgeschlagen! Du kannst dieses Fenster schließen.');
          server.close();
          reject(new Error(`OAuth Error: ${error}`));
          return;
        }

        // State Validierung (CSRF-Schutz)
        if (state !== expectedState) {
          res.send('❌ Invalid state! Möglicher CSRF-Angriff. Du kannst dieses Fenster schließen.');
          server.close();
          reject(new Error('Invalid state parameter'));
          return;
        }

        try {
          // Token Exchange
          const tokens = await this.exchangeCodeForTokens(code, codeVerifier, port);
          
          // Tokens speichern
          await this.tokenManager.saveTokens(tokens);

          res.send('✅ Authentifizierung erfolgreich! Du kannst dieses Fenster schließen.');
          server.close();
          
          console.log('✅ Authentifizierung erfolgreich!');
          resolve(tokens);

        } catch (error) {
          res.send('❌ Token Exchange fehlgeschlagen! Du kannst dieses Fenster schließen.');
          server.close();
          reject(error);
        }
      });

      server = app.listen(port, () => {
        console.log(`📡 Callback Server läuft auf Port ${port}`);
      });

      resolve({
        port,
        promise: new Promise((res, rej) => {
          resolve = res;
          reject = rej;
        })
      });
    });
  }

  /**
   * Tauscht Authorization Code gegen Tokens
   */
  async exchangeCodeForTokens(code, codeVerifier, callbackPort) {
    const tokenUrl = this.config.oauth.tokenUrl;

    const response = await axios.post(tokenUrl, new URLSearchParams({
      grant_type: 'authorization_code',
      client_id: this.config.oauth.clientId,
      client_secret: this.config.oauth.clientSecret,
      code: code,
      redirect_uri: `http://localhost:${callbackPort}/callback`,
      code_verifier: codeVerifier,
    }), {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    if (response.status !== 200) {
      throw new Error(`Token exchange failed: ${response.statusText}`);
    }

    return {
      accessToken: response.data.access_token,
      refreshToken: response.data.refresh_token,
      idToken: response.data.id_token,
      expiresIn: response.data.expires_in,
      expiresAt: Date.now() + (response.data.expires_in * 1000),
    };
  }

  /**
   * Refreshed abgelaufene Tokens
   */
  async refreshTokens() {
    const tokens = await this.tokenManager.loadTokens();
    
    if (!tokens.refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await axios.post(this.config.oauth.tokenUrl, new URLSearchParams({
      grant_type: 'refresh_token',
      client_id: this.config.oauth.clientId,
      client_secret: this.config.oauth.clientSecret,
      refresh_token: tokens.refreshToken,
    }), {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    const newTokens = {
      accessToken: response.data.access_token,
      refreshToken: response.data.refresh_token || tokens.refreshToken,
      idToken: response.data.id_token,
      expiresIn: response.data.expires_in,
      expiresAt: Date.now() + (response.data.expires_in * 1000),
    };

    await this.tokenManager.saveTokens(newTokens);
    return newTokens;
  }
}

module.exports = OAuthFlow;
```

### 2.3 Token Management

**Datei: `src/auth/token_manager.js`**

```javascript
const fs = require('fs').promises;
const path = require('path');
const os = require('os');
const jwt = require('jsonwebtoken');

class TokenManager {
  constructor() {
    this.configDir = path.join(os.homedir(), '.leowiki-mcp');
    this.tokenFile = path.join(this.configDir, 'tokens.json');
  }

  /**
   * Speichert Tokens persistent
   */
  async saveTokens(tokens) {
    // Config Verzeichnis erstellen
    await fs.mkdir(this.configDir, { recursive: true });

    // User Info aus ID Token extrahieren
    const userInfo = this.decodeIdToken(tokens.idToken);

    const data = {
      ...tokens,
      user: {
        id: userInfo.sub,
        email: userInfo.email,
        name: userInfo.name,
        role: userInfo.role,
      },
      savedAt: new Date().toISOString(),
    };

    await fs.writeFile(this.tokenFile, JSON.stringify(data, null, 2), {
      mode: 0o600, // Nur Owner kann lesen/schreiben
    });

    console.log(`💾 Tokens gespeichert für: ${userInfo.email}`);
  }

  /**
   * Lädt gespeicherte Tokens
   */
  async loadTokens() {
    try {
      const data = await fs.readFile(this.tokenFile, 'utf-8');
      return JSON.parse(data);
    } catch (error) {
      if (error.code === 'ENOENT') {
        throw new Error('Keine Tokens gefunden. Bitte authentifiziere dich mit: leowiki-mcp-proxy auth');
      }
      throw error;
    }
  }

  /**
   * Prüft ob Token noch gültig ist
   */
  async isTokenValid() {
    try {
      const tokens = await this.loadTokens();
      return Date.now() < tokens.expiresAt - 60000; // 1 Minute Puffer
    } catch {
      return false;
    }
  }

  /**
   * Löscht gespeicherte Tokens (Logout)
   */
  async deleteTokens() {
    try {
      await fs.unlink(this.tokenFile);
      console.log('✅ Tokens gelöscht (Logout erfolgreich)');
    } catch (error) {
      if (error.code !== 'ENOENT') {
        throw error;
      }
    }
  }

  /**
   * Dekodiert ID Token (ohne Validierung)
   */
  decodeIdToken(idToken) {
    const payload = idToken.split('.')[1];
    return JSON.parse(Buffer.from(payload, 'base64url').toString());
  }
}

module.exports = TokenManager;
```

---

## 🔄 Phase 3: MCP Proxy Implementation

### 3.1 MCP Protocol Handler

**Datei: `src/proxy/protocol.js`**

```javascript
/**
 * MCP Protocol Implementation
 * Implementiert das Model Context Protocol für stdio Kommunikation
 */
class MCPProtocol {
  /**
   * Parst MCP Request von stdio
   */
  static parseRequest(line) {
    try {
      const request = JSON.parse(line);
      
      // MCP Request Validation
      if (!request.jsonrpc || request.jsonrpc !== '2.0') {
        throw new Error('Invalid JSON-RPC version');
      }

      return {
        id: request.id,
        method: request.method,
        params: request.params || {},
      };
    } catch (error) {
      throw new Error(`Failed to parse MCP request: ${error.message}`);
    }
  }

  /**
   * Erstellt MCP Response
   */
  static createResponse(id, result) {
    return JSON.stringify({
      jsonrpc: '2.0',
      id: id,
      result: result,
    });
  }

  /**
   * Erstellt MCP Error Response
   */
  static createError(id, code, message) {
    return JSON.stringify({
      jsonrpc: '2.0',
      id: id,
      error: {
        code: code,
        message: message,
      },
    });
  }

  /**
   * MCP Notification (ohne ID)
   */
  static createNotification(method, params) {
    return JSON.stringify({
      jsonrpc: '2.0',
      method: method,
      params: params,
    });
  }
}

module.exports = MCPProtocol;
```

### 3.2 HTTP Client für Remote Server

**Datei: `src/proxy/http_client.js`**

```javascript
const axios = require('axios');
const TokenManager = require('../auth/token_manager');
const OAuthFlow = require('../auth/oauth_flow');

class RemoteMCPClient {
  constructor(config) {
    this.config = config;
    this.tokenManager = new TokenManager();
    this.oauthFlow = new OAuthFlow(config);
    this.baseURL = config.remote.serverUrl;
  }

  /**
   * Sendet MCP Request an Remote Server
   */
  async sendRequest(method, params) {
    // Token holen (mit automatischem Refresh)
    const accessToken = await this.getValidAccessToken();

    try {
      // HTTP Request an Remote MCP Server
      const response = await axios.post(
        `${this.baseURL}/mcp`,
        {
          jsonrpc: '2.0',
          method: method,
          params: params,
        },
        {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        }
      );

      return response.data.result;

    } catch (error) {
      if (error.response?.status === 401) {
        // Token ungültig - versuche Refresh
        console.log('🔄 Token abgelaufen, refreshe...');
        await this.oauthFlow.refreshTokens();
        
        // Retry mit neuem Token
        return this.sendRequest(method, params);
      }

      throw error;
    }
  }

  /**
   * Holt gültigen Access Token (mit Auto-Refresh)
   */
  async getValidAccessToken() {
    const tokens = await this.tokenManager.loadTokens();

    // Prüfe Ablauf (mit 1 Minute Puffer)
    if (Date.now() >= tokens.expiresAt - 60000) {
      console.log('🔄 Token läuft ab, refreshe...');
      const newTokens = await this.oauthFlow.refreshTokens();
      return newTokens.accessToken;
    }

    return tokens.accessToken;
  }
}

module.exports = RemoteMCPClient;
```

### 3.3 Haupt Proxy Server

**Datei: `src/proxy/server.js`**

```javascript
const readline = require('readline');
const MCPProtocol = require('./protocol');
const RemoteMCPClient = require('./http_client');

class ProxyServer {
  constructor(config) {
    this.config = config;
    this.client = new RemoteMCPClient(config);
    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      terminal: false,
    });
  }

  /**
   * Startet den Proxy Server
   */
  async start() {
    console.error('🚀 LeoWiki MCP Proxy gestartet');
    console.error(`📡 Remote Server: ${this.config.remote.serverUrl}`);

    // Prüfe Token
    const tokenManager = require('../auth/token_manager');
    const tm = new tokenManager();
    const isValid = await tm.isTokenValid();

    if (!isValid) {
      console.error('❌ Keine gültige Authentifizierung!');
      console.error('   Führe aus: leowiki-mcp-proxy auth');
      process.exit(1);
    }

    const tokens = await tm.loadTokens();
    console.error(`👤 Angemeldet als: ${tokens.user.email} (${tokens.user.role})`);

    // stdin Listener
    this.rl.on('line', async (line) => {
      try {
        await this.handleRequest(line);
      } catch (error) {
        console.error('❌ Error:', error.message);
      }
    });

    // Graceful Shutdown
    process.on('SIGINT', () => {
      console.error('🛑 Proxy wird beendet...');
      this.rl.close();
      process.exit(0);
    });
  }

  /**
   * Verarbeitet MCP Request
   */
  async handleRequest(line) {
    // Parse MCP Request
    const request = MCPProtocol.parseRequest(line);

    console.error(`📥 Request: ${request.method}`);

    try {
      // An Remote Server weiterleiten
      const result = await this.client.sendRequest(request.method, request.params);

      // Response zurück an LLM
      const response = MCPProtocol.createResponse(request.id, result);
      console.log(response); // stdout = zurück an LLM

    } catch (error) {
      console.error(`❌ Error: ${error.message}`);
      
      // Error Response
      const errorResponse = MCPProtocol.createError(
        request.id,
        -32603,
        error.message
      );
      console.log(errorResponse);
    }
  }
}

module.exports = ProxyServer;
```

---

## 💻 Phase 4: CLI Commands

### 4.1 Auth Command

**Datei: `src/cli/auth_command.js`**

```javascript
const OAuthFlow = require('../auth/oauth_flow');
const config = require('../config/settings');

async function authCommand() {
  console.log('🔐 LeoWiki MCP Proxy - Authentifizierung\n');

  const oauth = new OAuthFlow(config);

  try {
    await oauth.authenticate();
    console.log('\n✅ Authentifizierung erfolgreich abgeschlossen!');
    console.log('   Du kannst jetzt LeoWiki MCP in deinen LLMs nutzen.\n');
  } catch (error) {
    console.error('\n❌ Authentifizierung fehlgeschlagen:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  authCommand();
}

module.exports = authCommand;
```

### 4.2 Status Command

**Datei: `src/cli/status_command.js`**

```javascript
const TokenManager = require('../auth/token_manager');

async function statusCommand() {
  const tokenManager = new TokenManager();

  try {
    const tokens = await tokenManager.loadTokens();
    const isValid = await tokenManager.isTokenValid();

    console.log('📊 LeoWiki MCP Proxy - Status\n');
    console.log('Authentication:');
    console.log(`  User:     ${tokens.user.name} (${tokens.user.email})`);
    console.log(`  Role:     ${tokens.user.role}`);
    console.log(`  Status:   ${isValid ? '✅ Gültig' : '⚠️  Abgelaufen'}`);
    console.log(`  Expires:  ${new Date(tokens.expiresAt).toLocaleString()}`);
    console.log(`  Saved:    ${tokens.savedAt}`);

  } catch (error) {
    console.log('📊 LeoWiki MCP Proxy - Status\n');
    console.log('Authentication: ❌ Nicht authentifiziert');
    console.log('\nFühre aus: leowiki-mcp-proxy auth');
  }
}

if (require.main === module) {
  statusCommand();
}

module.exports = statusCommand;
```

### 4.3 Logout Command

**Datei: `src/cli/logout_command.js`**

```javascript
const TokenManager = require('../auth/token_manager');

async function logoutCommand() {
  const tokenManager = new TokenManager();

  try {
    await tokenManager.deleteTokens();
    console.log('✅ Logout erfolgreich!');
    console.log('   Alle gespeicherten Tokens wurden gelöscht.');
  } catch (error) {
    console.error('❌ Logout fehlgeschlagen:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  logoutCommand();
}

module.exports = logoutCommand;
```

---

## ⚙️ Phase 5: Konfiguration

### 5.1 Default Config

**Datei: `config/default.json`**

```json
{
  "remote": {
    "serverUrl": "https://leowiki-mcp.stream"
  },
  "oauth": {
    "authorizationUrl": "https://leowikimcp.scalekit.dev/oauth/authorize",
    "tokenUrl": "https://leowikimcp.scalekit.dev/oauth/token",
    "clientId": "skc_107036659593249282",
    "clientSecret": ""
  },
  "proxy": {
    "timeout": 30000,
    "retryAttempts": 3
  }
}
```

### 5.2 Settings Loader

**Datei: `src/config/settings.js`**

```javascript
const fs = require('fs');
const path = require('path');

// Load default config
const defaultConfig = require('../../config/default.json');

// Load user config if exists
const userConfigPath = path.join(
  require('os').homedir(),
  '.leowiki-mcp',
  'config.json'
);

let userConfig = {};
if (fs.existsSync(userConfigPath)) {
  userConfig = JSON.parse(fs.readFileSync(userConfigPath, 'utf-8'));
}

// Load env variables
const envConfig = {
  oauth: {
    clientSecret: process.env.LEOWIKI_CLIENT_SECRET || '',
  },
};

// Merge configs
const config = {
  ...defaultConfig,
  ...userConfig,
  oauth: {
    ...defaultConfig.oauth,
    ...userConfig.oauth,
    ...envConfig.oauth,
  },
};

module.exports = config;
```

---

## 🚀 Phase 6: Entry Point & CLI

### 6.1 Main Entry Point

**Datei: `src/index.js`**

```javascript
#!/usr/bin/env node

const ProxyServer = require('./proxy/server');
const config = require('./config/settings');

async function main() {
  const proxy = new ProxyServer(config);
  await proxy.start();
}

main().catch((error) => {
  console.error('❌ Fatal Error:', error);
  process.exit(1);
});
```

### 6.2 CLI Executable

**Datei: `bin/leowiki-mcp-proxy`**

```bash
#!/usr/bin/env node

const { Command } = require('commander');
const authCommand = require('../src/cli/auth_command');
const statusCommand = require('../src/cli/status_command');
const logoutCommand = require('../src/cli/logout_command');
const ProxyServer = require('../src/proxy/server');
const config = require('../src/config/settings');

const program = new Command();

program
  .name('leowiki-mcp-proxy')
  .description('LeoWiki MCP Proxy - Multi-LLM OAuth 2.1 Proxy')
  .version('1.0.0');

// Auth Command
program
  .command('auth')
  .description('Authentifiziere dich mit ScaleKit OAuth 2.1')
  .action(authCommand);

// Status Command
program
  .command('status')
  .description('Zeigt aktuellen Authentifizierungs-Status')
  .action(statusCommand);

// Logout Command
program
  .command('logout')
  .description('Löscht gespeicherte Tokens (Logout)')
  .action(logoutCommand);

// Start Command (default - für LLMs)
program
  .command('start', { isDefault: true })
  .description('Startet den Proxy Server (für LLMs)')
  .action(async () => {
    const proxy = new ProxyServer(config);
    await proxy.start();
  });

program.parse();
```

---

## 📝 Phase 7: Dokumentation

### 7.1 README.md

**Datei: `README.md`**

```markdown
# 🔄 LeoWiki MCP Proxy

Local proxy server for using the remote LeoWiki MCP Server with OAuth 2.1 authentication in desktop LLM clients (Claude Desktop, Cursor IDE, Cline, etc.).

## Features

- ✅ Works with all MCP-compatible LLM clients
- ✅ OAuth 2.1 with PKCE authentication
- ✅ Automatic token refresh
- ✅ Persistent token caching
- ✅ Simple CLI interface
- ✅ Secure token storage (~/.leowiki-mcp/)

## Installation

### Global Installation (Recommended)

```bash
npm install -g leowiki-mcp-proxy
```

### From Source

```bash
git clone https://github.com/your-org/leowiki-mcp-proxy.git
cd leowiki-mcp-proxy
npm install
npm link
```

## Quick Start

### 1. Authenticate

```bash
leowiki-mcp-proxy auth
```

This will:
- Open your browser
- Redirect to ScaleKit login
- Save tokens locally

### 2. Configure Your LLM

#### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "leowiki": {
      "command": "leowiki-mcp-proxy",
      "args": ["start"]
    }
  }
}
```

#### Cursor IDE

Edit `~/.cursor/mcp_config.json`:

```json
{
  "mcpServers": {
    "leowiki": {
      "command": "leowiki-mcp-proxy",
      "args": ["start"]
    }
  }
}
```

#### Cline (VSCode)

Add to VSCode settings:

```json
{
  "cline.mcpServers": {
    "leowiki": {
      "command": "leowiki-mcp-proxy",
      "args": ["start"]
    }
  }
}
```

### 3. Use in Your LLM

Just start using LeoWiki commands in your LLM client!

## CLI Commands

```bash
# Authenticate
leowiki-mcp-proxy auth

# Check status
leowiki-mcp-proxy status

# Logout
leowiki-mcp-proxy logout

# Start proxy (automatic in LLMs)
leowiki-mcp-proxy start
```

## Configuration

### User Config

Create `~/.leowiki-mcp/config.json`:

```json
{
  "remote": {
    "serverUrl": "https://leowiki-mcp.stream"
  },
  "oauth": {
    "clientId": "your-client-id"
  }
}
```

### Environment Variables

```bash
export LEOWIKI_CLIENT_SECRET="your-secret"
```

## Troubleshooting

### "Keine gültige Authentifizierung"

Run: `leowiki-mcp-proxy auth`

### Token expired

Tokens are refreshed automatically. If issues persist:

```bash
leowiki-mcp-proxy logout
leowiki-mcp-proxy auth
```

### Connection failed

Check:
1. Internet connection
2. Remote server status
3. Firewall settings

## Security

- Tokens stored in `~/.leowiki-mcp/tokens.json` (chmod 600)
- OAuth 2.1 with PKCE (no client secret in browser)
- Automatic token refresh
- Local callback server (localhost only)

## Development

```bash
# Install dependencies
npm install

# Run tests
npm test

# Run locally
node src/index.js

# Build
npm run build
```

## License

MIT

## Support

- Documentation: https://docs.leowiki.dev/mcp-proxy
- Issues: https://github.com/your-org/leowiki-mcp-proxy/issues
```

---

## ✅ Phase 8: Testing & Deployment

### 8.1 Test Suite

**Datei: `test/auth.test.js`**

```javascript
const PKCEHelper = require('../src/auth/pkce');

describe('PKCE Helper', () => {
  test('generates valid code verifier', () => {
    const verifier = PKCEHelper.generateCodeVerifier();
    expect(verifier).toHaveLength(43);
  });

  test('generates valid code challenge', () => {
    const verifier = 'test-verifier';
    const challenge = PKCEHelper.generateCodeChallenge(verifier);
    expect(challenge).toBeTruthy();
    expect(challenge).not.toBe(verifier);
  });

  test('generates unique state', () => {
    const state1 = PKCEHelper.generateState();
    const state2 = PKCEHelper.generateState();
    expect(state1).not.toBe(state2);
  });
});
```

### 8.2 Integration Test

**Datei: `test/integration.test.js`**

```javascript
const ProxyServer = require('../src/proxy/server');
const config = require('../src/config/settings');

describe('Proxy Server Integration', () => {
  test('server initializes correctly', () => {
    const proxy = new ProxyServer(config);
    expect(proxy).toBeDefined();
    expect(proxy.config).toBe(config);
  });

  // Weitere Tests...
});
```

### 8.3 Deployment

#### NPM Publish

```bash
# 1. Version bump
npm version patch

# 2. Build
npm run build

# 3. Test
npm test

# 4. Publish
npm publish
```

#### GitHub Release

```bash
# Tag erstellen
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0

# GitHub Release erstellen
gh release create v1.0.0 --title "v1.0.0" --notes "Initial release"
```

---

## 📊 Phase 9: User Guide & Examples

### 9.1 Installation Guide für End-User

**Datei: `docs/USER_GUIDE.md`**

```markdown
# LeoWiki MCP Proxy - Benutzerhandbuch

## Schritt 1: Installation

```bash
npm install -g leowiki-mcp-proxy
```

## Schritt 2: Authentifizierung

```bash
leowiki-mcp-proxy auth
```

Ein Browser öffnet sich automatisch. Melde dich mit deinen LeoWiki Credentials an:

- **Admin**: janritt.office@gmail.com
- **Teacher**: cell.enohp.apps@gmail.com
- **Student**: leowikidev@gmail.com

## Schritt 3: LLM Konfiguration

### Claude Desktop

1. Öffne Config: `~/Library/Application Support/Claude/claude_desktop_config.json`
2. Füge hinzu:

```json
{
  "mcpServers": {
    "leowiki": {
      "command": "leowiki-mcp-proxy"
    }
  }
}
```

3. Starte Claude Desktop neu

### Cursor IDE

1. Öffne Config: `~/.cursor/mcp_config.json`
2. Füge hinzu:

```json
{
  "mcpServers": {
    "leowiki": {
      "command": "leowiki-mcp-proxy"
    }
  }
}
```

3. Starte Cursor neu

## Schritt 4: Nutzung

In deinem LLM:

```
@leowiki Suche nach "DokuWiki Plugins"
```

oder

```
Kannst du mir die neuesten Einträge aus dem LeoWiki zeigen?
```

## Fehlerbehebung

### Problem: "Keine gültige Authentifizierung"

**Lösung:**
```bash
leowiki-mcp-proxy auth
```

### Problem: Token abgelaufen

**Lösung:** Automatischer Refresh. Falls Probleme:
```bash
leowiki-mcp-proxy logout
leowiki-mcp-proxy auth
```

### Problem: Proxy startet nicht

**Lösung:**
```bash
leowiki-mcp-proxy status
```

Prüfe ob:
- Node.js installiert (v18+)
- npm installiert
- Internet-Verbindung aktiv
```

---

## 🎯 Zusammenfassung

### Was wurde erstellt:

1. ✅ **OAuth 2.1 Flow** mit PKCE
2. ✅ **Token Management** mit Auto-Refresh
3. ✅ **MCP Protocol Handler** für stdio
4. ✅ **HTTP Client** für Remote Server
5. ✅ **Proxy Server** (stdio ↔ HTTPS)
6. ✅ **CLI Commands** (auth, status, logout)
7. ✅ **Konfiguration** (user & env)
8. ✅ **Dokumentation** (README, Guide)
9. ✅ **Tests** (Unit & Integration)

### Architektur:

```
LLM Desktop Client (stdio)
        ↓
   MCP Proxy (lokal)
        ↓
   OAuth 2.1 + Token Cache
        ↓
   Remote MCP Server (HTTPS)
        ↓
   ScaleKit Auth
```

### Deployment:

- **NPM Package**: `leowiki-mcp-proxy`
- **Installation**: `npm install -g leowiki-mcp-proxy`
- **Konfiguration**: `~/.leowiki-mcp/config.json`
- **Tokens**: `~/.leowiki-mcp/tokens.json`

---

## 🚀 Nächste Schritte

1. **Code Review** durchführen
2. **Tests** ausführen
3. **NPM Package** publishen
4. **Dokumentation** finalisieren
5. **Beta-Testing** mit echten Usern

---

*Dokument erstellt: 08. Januar 2026*
*Version: 1.0*
*Autor: AI Assistant*
