# 🖥️ CLAUDE DESKTOP CONNECTION GUIDE - MCP Diploma Thesis

**Für externe Tester/Kollegen über das Internet**

**Server:** https://leowiki-mcp.stream  
**MCP Endpoint:** https://leowiki-mcp.stream/mcp  
**Datum:** 06. Januar 2026

---

## 🎯 ÜBERBLICK

Dieses Dokument erklärt, wie du dich von deinem Computer (egal wo auf der Welt) mit dem MCP Educational Server über **Claude Desktop** verbindest.

---

## 📋 VORAUSSETZUNGEN

### Was du brauchst:

1. **Claude Desktop App** installiert
   - Download: https://claude.ai/download
   - Version: 0.7.0 oder neuer

2. **Internet-Verbindung**
   - Keine VPN oder speziellen Firewall-Einstellungen nötig
   - Der Server ist öffentlich über HTTPS erreichbar

3. **Zugang zur Config-Datei**
   - Du musst die Claude Desktop Konfiguration bearbeiten können

---

## 🚀 SCHRITT-FÜR-SCHRITT ANLEITUNG

### SCHRITT 1: Claude Desktop schließen

**WICHTIG:** Claude Desktop muss komplett geschlossen sein!

**Windows:**
```
1. Rechtsklick auf Claude Desktop in der Taskleiste
2. "Beenden" wählen
3. Task Manager öffnen (Ctrl+Shift+Esc)
4. Überprüfen, dass kein "Claude" Prozess läuft
```

**macOS:**
```
1. Cmd+Q drücken (oder Claude → Quit Claude)
2. Activity Monitor öffnen
3. Überprüfen, dass kein "Claude" Prozess läuft
```

**Linux:**
```bash
# Claude Desktop beenden
pkill -f claude

# Überprüfen
ps aux | grep claude
```

---

### SCHRITT 2: Config-Datei finden und öffnen

Die Claude Desktop Konfiguration liegt hier:

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```
Vollständiger Pfad normalerweise:
```
C:\Users\DEIN_NAME\AppData\Roaming\Claude\claude_desktop_config.json
```

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

---

### SCHRITT 3: Config-Datei bearbeiten

Öffne die Datei mit einem Text-Editor:

**Windows:** Notepad, VS Code, oder Notepad++
**macOS:** TextEdit, VS Code
**Linux:** nano, vim, gedit, VS Code

**WICHTIG:** Die Datei muss gültiges JSON sein!

---

### SCHRITT 4: MCP Server hinzufügen

#### **VARIANTE A: Ohne OAuth (Einfacher Start)**

Füge diesen Code in die `claude_desktop_config.json` ein:

```json
{
  "mcpServers": {
    "mcp-educational-server": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/client",
        "https://leowiki-mcp.stream/mcp"
      ],
      "env": {}
    }
  }
}
```

**Hinweis:** Aktuell ist OAuth auf dem Server deaktiviert (`ENABLE_AUTH=false`), daher funktioniert diese Variante sofort!

---

#### **VARIANTE B: Mit OAuth (Wenn aktiviert)**

Wenn OAuth auf dem Server aktiviert ist (`ENABLE_AUTH=true`), brauchst du einen JWT Token:

```json
{
  "mcpServers": {
    "mcp-educational-server": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/client",
        "https://leowiki-mcp.stream/mcp"
      ],
      "env": {
        "MCP_AUTH_TOKEN": "DEIN_JWT_TOKEN_HIER"
      }
    }
  }
}
```

**JWT Token bekommen:**
1. Kontaktiere den Server-Administrator (Imre)
2. Oder login über: https://mcpeduauth.scalekit.dev
3. Token in die Config einfügen

---

### SCHRITT 5: Datei speichern

**WICHTIG:** 
- Speichere als **UTF-8** ohne BOM
- Überprüfe, dass es gültiges JSON ist
- Keine Kommas am Ende des letzten Elements!

**JSON-Validator:** https://jsonlint.com

---

### SCHRITT 6: Claude Desktop starten

1. Starte Claude Desktop neu
2. Warte 5-10 Sekunden, bis die App vollständig geladen ist

---

### SCHRITT 7: Verbindung überprüfen

#### **In Claude Desktop:**

Schaue in der unteren rechten Ecke nach dem **🔌 MCP-Icon**.

**Wenn verbunden:**
- Icon ist **grün** oder **aktiv**
- Klicke darauf, um verbundene Server zu sehen
- Du solltest "mcp-educational-server" sehen

**Wenn nicht verbunden:**
- Icon ist **grau** oder fehlt
- Siehe **Troubleshooting** unten

---

### SCHRITT 8: MCP Server testen

#### **Test 1: Tools anzeigen**

In Claude Desktop, schreibe:

```
Welche MCP Tools stehen dir zur Verfügung?
```

**Erwartete Antwort:**
Claude sollte diese Tools auflisten:
- `search_content` - Semantic search in educational content
- `get_collection_stats` - Database statistics

---

#### **Test 2: Search durchführen**

In Claude Desktop, schreibe:

```
Suche nach "HTL Leonding" in der Educational Database
```

oder

```
Use the search_content tool to search for "HTL Leonding"
```

**Erwartete Antwort:**
- Claude verwendet das `search_content` Tool
- Du siehst Suchergebnisse mit Titeln und Scores
- (Wenn Daten in der DB sind)

---

#### **Test 3: Collection Stats**

In Claude Desktop, schreibe:

```
Wie viele Dokumente sind in der Educational Database?
```

oder

```
Use get_collection_stats to show database information
```

**Erwartete Antwort:**
- Claude verwendet das `get_collection_stats` Tool
- Du siehst Statistiken: Collection Name, Anzahl Dokumente, etc.

---

## 🧪 ERWEITERTE TESTS

### Test 4: RBAC (Role-Based Access)

**Als Student:**

```
Suche als Student nach "Lehrer Informationen"
```

**Claude sollte:**
- Nur Dokumente mit `access_level: "public"` oder `"student"` finden
- KEINE Dokumente mit `access_level: "teacher"` anzeigen

---

**Als Teacher:**

```
Suche als Lehrer nach "Prüfungslösungen"
```

**Claude sollte:**
- ALLE Dokumente finden (public, student, teacher)
- Auch vertrauliche Lehrer-Dokumente anzeigen

---

### Test 5: Verschiedene Suchanfragen

```
1. "Was ist die Matura?"
2. "Python Programmierung"
3. "Mathematik Formeln"
4. "HTL Leonding Geschichte"
5. "Computer Science Basics"
```

Jede Anfrage sollte:
- Semantisch ähnliche Dokumente finden
- Mit Relevanz-Scores anzeigen
- Schnell antworten (< 2 Sekunden)

---

## 🆘 TROUBLESHOOTING

### Problem 1: "MCP Server nicht verbunden"

**Lösung:**

1. **Überprüfe die URL:**
   ```bash
   # Von deinem PC aus testen:
   curl https://leowiki-mcp.stream/health
   
   # Erwartete Antwort:
   # {"status":"healthy",...}
   ```

2. **Überprüfe die Config:**
   - Ist die JSON-Datei gültig? → jsonlint.com
   - Ist die URL richtig? → `https://leowiki-mcp.stream/mcp`
   - Sind die Anführungszeichen korrekt? → `"` nicht `'`

3. **Claude Desktop Logs überprüfen:**
   
   **Windows:**
   ```
   %APPDATA%\Claude\logs\
   ```
   
   **macOS:**
   ```
   ~/Library/Logs/Claude/
   ```
   
   **Linux:**
   ```
   ~/.config/Claude/logs/
   ```
   
   Schaue nach Fehlermeldungen mit "mcp" oder "server"

4. **Firewall/Proxy überprüfen:**
   - Blockiert deine Firewall HTTPS-Verbindungen?
   - Bist du hinter einem Corporate Proxy?
   - Versuche es von einem anderen Netzwerk (z.B. Handy Hotspot)

---

### Problem 2: "Tools werden nicht angezeigt"

**Lösung:**

1. **Claude Desktop komplett neu starten:**
   - Prozess beenden (Task Manager / Activity Monitor)
   - App neu öffnen
   - 10 Sekunden warten

2. **Config neu laden:**
   - Config-Datei erneut öffnen
   - Kleine Änderung machen (z.B. Leerzeichen)
   - Speichern
   - Claude Desktop neu starten

3. **Verbindung manuell testen:**
   ```bash
   # MCP Inspector verwenden
   npx @modelcontextprotocol/inspector https://leowiki-mcp.stream/mcp
   ```

---

### Problem 3: "Authentication Failed" (bei OAuth)

**Lösung:**

1. **Token überprüfen:**
   - Ist der JWT Token gültig?
   - Ist er abgelaufen? (Standard: 1 Stunde)
   - Neuen Token anfordern

2. **OAuth Metadata überprüfen:**
   ```bash
   curl https://leowiki-mcp.stream/.well-known/oauth-protected-resource
   ```

3. **Server-Status überprüfen:**
   ```bash
   curl https://leowiki-mcp.stream/health
   ```

---

### Problem 4: "Keine Suchergebnisse"

**Mögliche Ursachen:**

1. **Datenbank ist leer:**
   - Kontaktiere den Administrator
   - Überprüfe mit `get_collection_stats`

2. **RBAC filtert alles raus:**
   - Du suchst als "student" nach "teacher"-only Inhalten
   - Versuche allgemeine Begriffe

3. **Suchbegriff zu spezifisch:**
   - Verwende allgemeinere Begriffe
   - Versuche auf Deutsch oder Englisch

---

### Problem 5: "Timeout" oder "Verbindung langsam"

**Lösung:**

1. **Server Status überprüfen:**
   ```bash
   curl https://leowiki-mcp.stream/health
   ```

2. **Internet-Verbindung testen:**
   ```bash
   ping leowiki-mcp.stream
   traceroute leowiki-mcp.stream
   ```

3. **Zu einem anderen Zeitpunkt testen:**
   - Ist der Server überlastet?
   - Ist deine Internet-Verbindung langsam?

---

## 📊 PERFORMANCE ERWARTUNGEN

| Aktion | Erwartete Zeit |
|--------|----------------|
| Verbindung aufbauen | 2-5 Sekunden |
| Tools laden | 1-2 Sekunden |
| Search Query (ohne Daten) | 0.5-1 Sekunden |
| Search Query (mit Daten) | 1-3 Sekunden |
| Collection Stats | 0.5-1 Sekunden |

**Wenn langsamer:**
- Server könnte überlastet sein
- Internet-Verbindung könnte langsam sein
- Viele gleichzeitige Anfragen

---

## 🔒 SICHERHEIT & DATENSCHUTZ

### Was der Server sieht:

✅ **Der Server sieht:**
- Deine Suchanfragen
- Verwendete Tools
- Zeitstempel der Anfragen
- IP-Adresse (für Rate Limiting)

❌ **Der Server sieht NICHT:**
- Deine gesamten Claude-Konversationen
- Andere Tools, die du verwendest
- Persönliche Daten (außer du sendest sie)

### Deine Daten:

- Alle Anfragen werden über **HTTPS** verschlüsselt
- Logs werden nur für Debugging verwendet
- Keine Weitergabe an Dritte
- Server steht in Österreich (DSGVO-konform)

---

## 💡 TIPPS & TRICKS

### Tip 1: Effektive Suchanfragen

**Gut:**
```
"Suche nach Python Programmierung Grundlagen"
"Finde Informationen über die Matura"
"Was gibt es über HTL Leonding?"
```

**Weniger gut:**
```
"py" (zu kurz)
"12345" (keine semantische Bedeutung)
"asdfgh" (kein sinnvoller Begriff)
```

---

### Tip 2: Tool-Verwendung erzwingen

Wenn Claude das Tool nicht automatisch verwendet:

```
Bitte verwende GENAU das search_content Tool, um nach "HTL" zu suchen.
```

oder

```
@use search_content query="HTL Leonding" limit=5
```

---

### Tip 3: Debugging

Wenn etwas nicht funktioniert:

1. **In Claude Desktop:**
   ```
   Zeige mir den genauen API-Call, den du gerade gemacht hast.
   ```

2. **Server-Logs überprüfen:**
   - Kontaktiere den Administrator
   - Oder schaue selbst: `docker compose logs mcp-server`

3. **MCP Inspector verwenden:**
   ```bash
   npx @modelcontextprotocol/inspector https://leowiki-mcp.stream/mcp
   ```

---

## 📞 SUPPORT

### Bei Problemen kontaktiere:

**Administrator:** Obermüller Imre  
**Email:** imre.obermueller@gmail.com  
**Server:** https://leowiki-mcp.stream

### Hilfreiche Informationen beim Support-Request:

1. Dein Betriebssystem (Windows/macOS/Linux)
2. Claude Desktop Version
3. Fehlermeldung (exakt kopiert)
4. Was du versucht hast
5. Logs (falls vorhanden)

---

## ✅ ERFOLGREICHE VERBINDUNG - CHECKLISTE

Du hast alles richtig gemacht, wenn:

- [x] Claude Desktop zeigt MCP-Icon (🔌)
- [x] Icon ist grün/aktiv
- [x] "mcp-educational-server" wird gelistet
- [x] Claude kann Tools auflisten
- [x] `search_content` funktioniert
- [x] `get_collection_stats` funktioniert
- [x] Suchergebnisse kommen innerhalb von 2-3 Sekunden
- [x] Keine Fehlermeldungen in den Logs

---

## 🎓 FÜR TESTER

### Was du testen solltest:

1. **Funktionalität:**
   - [ ] Verbindung herstellen
   - [ ] Tools anzeigen
   - [ ] Einfache Suche
   - [ ] Komplexe Suche
   - [ ] Collection Stats
   - [ ] RBAC (verschiedene Rollen)

2. **Performance:**
   - [ ] Antwortzeiten messen
   - [ ] Mehrere gleichzeitige Anfragen
   - [ ] Große Ergebnismengen

3. **Edge Cases:**
   - [ ] Leere Suche
   - [ ] Sehr lange Suchanfragen
   - [ ] Sonderzeichen
   - [ ] Verschiedene Sprachen

4. **Stabilität:**
   - [ ] Verbindung über längere Zeit
   - [ ] Nach Neustart
   - [ ] Nach Server-Update

### Feedback geben:

Bitte dokumentiere:
- Was funktioniert gut?
- Was funktioniert nicht?
- Verbesserungsvorschläge?
- Gefundene Bugs?

---

## 🚀 LOS GEHT'S!

**Start hier:**

1. ✅ Claude Desktop schließen
2. ✅ Config-Datei öffnen
3. ✅ MCP Server eintragen (siehe SCHRITT 4)
4. ✅ Speichern
5. ✅ Claude Desktop starten
6. ✅ Verbindung überprüfen (🔌 Icon)
7. ✅ Tools testen

**Viel Erfolg! 🎉**

Bei Fragen → Administrator kontaktieren!

---

**Letzte Aktualisierung:** 06. Januar 2026  
**Server Version:** 1.0.0 (Production)  
**Status:** 🟢 Online & Ready for Testing
