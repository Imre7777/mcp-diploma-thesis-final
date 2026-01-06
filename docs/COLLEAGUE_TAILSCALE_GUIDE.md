# 📤 Anleitung für Daten-Upload via Tailscale

**Für:** Kollegen (Daten-Lieferant)  
**Server:** MCP Educational Server (Raspberry Pi)  
**Methode:** Tailscale VPN + SCP Upload

---

## 🎯 Überblick

Sie können JSONL-Dateien sicher und verschlüsselt über **Tailscale** zum MCP Server hochladen.

**Vorteile:**
- ✅ **Verschlüsselt:** WireGuard-Protokoll (end-to-end)
- ✅ **Einfach:** Nur 3 Schritte
- ✅ **Von überall:** Von zu Hause, Büro, unterwegs
- ✅ **Keine Port-Freigabe:** Funktioniert hinter Firewalls/NAT

---

## 📋 Voraussetzungen (Einmalig)

### Schritt 1: Tailscale installieren

**Windows:**
```powershell
# Download von: https://tailscale.com/download/windows
# Oder mit winget:
winget install tailscale.tailscale
```

**macOS:**
```bash
# Download von: https://tailscale.com/download/mac
# Oder mit Homebrew:
brew install tailscale
```

**Linux:**
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

### Schritt 2: Tailscale verbinden

1. **Tailscale App öffnen** (im Tray/Menübar)
2. **"Sign in"** klicken
3. **Mit Google/Microsoft/GitHub anmelden**
   - ⚠️ **WICHTIG:** Verwenden Sie den **gleichen Account** wie Imre!
   - Oder: Imre muss Sie zu seinem Tailscale-Netzwerk einladen
4. **Status überprüfen:** App sollte "Connected" zeigen (grüner Punkt)

### Schritt 3: Raspberry Pi sehen

1. **Tailscale App öffnen**
2. **"Machines" oder "Devices" klicken**
3. **Sie sollten sehen:**
   - Ihr eigener PC (z.B. "LAPTOP-XYZ")
   - Raspberry Pi (z.B. "raspberrypi" oder "mcp-pi")

**Tailscale IP des Pi:**
```
100.73.228.15  # ← Raspberry Pi Tailscale IP
```

**Oder mit Hostname:**
```
raspi-docker  # ← Raspberry Pi Hostname (Magic DNS)
```

---

## 📤 JSONL-Datei hochladen

### Methode 1: Über Kommandozeile (empfohlen)

**Windows (PowerShell oder CMD):**
```powershell
scp meine_daten.jsonl imreo@100.73.228.15:/home/imreo/mcp-diploma-thesis-final/data/incoming/
```

**macOS / Linux:**
```bash
scp meine_daten.jsonl imreo@100.73.228.15:/home/imreo/mcp-diploma-thesis-final/data/incoming/
```

**Mit Hostname (falls Magic DNS aktiviert):**
```bash
scp meine_daten.jsonl imreo@mcp-pi:/home/imreo/mcp-diploma-thesis-final/data/incoming/
```

**Beim ersten Mal:**
- Passwort-Eingabe wird verlangt → Passwort von Imre erhalten
- Fingerprint bestätigen mit "yes"

### Methode 2: Mit SSH-Key (kein Passwort)

**Einmalig: SSH-Key generieren**

```bash
# Key generieren
ssh-keygen -t ed25519 -C "ihr.email@example.com"

# Enter drücken für Standard-Speicherort
# Optional: Passphrase eingeben (oder leer lassen)

# Public Key anzeigen
cat ~/.ssh/id_ed25519.pub
```

**Public Key an Imre senden:**
- Inhalt von `id_ed25519.pub` kopieren
- Per Email an Imre senden
- Imre fügt den Key zum Pi hinzu

**Danach:** SCP funktioniert OHNE Passwort-Eingabe! 🎉

### Methode 3: Mit FileZilla (GUI)

1. **FileZilla installieren:** https://filezilla-project.org/
2. **SFTP-Verbindung einrichten:**
   - Host: `sftp://{{TAILSCALE_IP}}`
   - Port: `22`
   - User: `imreo`
   - Password: (von Imre erhalten)
3. **Verbinden**
4. **Datei per Drag & Drop hochladen zu:**
   ```
   /home/imreo/mcp-diploma-thesis-final/data/incoming/
   ```

---

## 📝 JSONL-Format

### Grundstruktur

Jede Zeile = ein JSON-Dokument (kein Array, keine Formatierung!)

```jsonl
{"id": "doc_001", "title": "Python Grundlagen", "content": "Python ist...", "metadata": {"frontmatter": {"access_level": "student"}}}
{"id": "doc_002", "title": "Python Übung", "content": "Übung 1...", "metadata": {"frontmatter": {"access_level": "teacher"}}}
```

### Pflichtfelder

| Feld | Typ | Beschreibung | Beispiel |
|------|-----|--------------|----------|
| `id` | string | Eindeutige ID | `"doc_001"` |
| `title` | string | Dokumenttitel | `"Python Einführung"` |
| `content` | string | Hauptinhalt | `"Python ist eine..."` |
| `metadata.frontmatter.access_level` | string | Zugriffslevel | `"student"`, `"teacher"`, `"admin"` |

### Access Levels

| Level | Sichtbar für |
|-------|--------------|
| `"student"` | Alle Studenten (und Teachers, Admins) |
| `"teacher"` | Nur Teachers und Admins |
| `"admin"` | Nur Admins |

### Optionale Felder

```json
{
  "id": "doc_001",
  "title": "Python Grundlagen",
  "content": "Python ist eine...",
  "metadata": {
    "frontmatter": {
      "access_level": "student",
      "content_type": "KNOWLEDGE",
      "freshness_score": 0.9,
      "freshness_category": "recent",
      "namespace": "Informatik/Programmierung",
      "author": "Prof. Müller",
      "source": "Vorlesung WS2024",
      "date": "2024-01-15"
    }
  }
}
```

### Beispiel: Vollständige JSONL-Datei

```jsonl
{"id": "htl_001", "title": "HTL Leonding Geschichte", "content": "Die HTL Leonding wurde 1971 gegründet...", "metadata": {"frontmatter": {"access_level": "student", "content_type": "KNOWLEDGE", "namespace": "HTL/Geschichte"}}}
{"id": "htl_002", "title": "Python Einführung", "content": "Python ist eine interpretierte, objektorientierte Programmiersprache...", "metadata": {"frontmatter": {"access_level": "student", "content_type": "TUTORIAL", "namespace": "Informatik/Python"}}}
{"id": "htl_003", "title": "Übung 5 Musterlösung", "content": "Lösung zu Übung 5: def calculate(x, y): return x + y...", "metadata": {"frontmatter": {"access_level": "teacher", "content_type": "SOLUTION", "namespace": "Informatik/Übungen"}}}
```

---

## ✅ Upload-Workflow

### Schritt 1: Datei vorbereiten

```bash
# Beispiel: education_data_20260106.jsonl erstellen
# Mit Text-Editor oder Export-Tool
```

### Schritt 2: Tailscale Status prüfen

```bash
# Tailscale App öffnen
# Status: "Connected" (grün) → OK!
# Status: "Disconnected" (grau) → Verbindung herstellen
```

### Schritt 3: Hochladen

```bash
scp education_data_20260106.jsonl imreo@{{TAILSCALE_IP}}:/home/imreo/mcp-diploma-thesis-final/data/incoming/
```

**Erwartete Ausgabe:**
```
education_data_20260106.jsonl    100%  1234KB   2.1MB/s   00:00
```

### Schritt 4: Bestätigung (optional)

**Option A: Email an Imre**
```
Betreff: JSONL Upload
Inhalt: Datei education_data_20260106.jsonl hochgeladen (1234 KB, 50 Dokumente)
```

**Option B: Selbst überprüfen (falls SSH-Zugang)**
```bash
ssh imreo@100.73.228.15
ls -lh /home/imreo/mcp-diploma-thesis-final/data/incoming/
# → Datei sollte da sein

# Processed files checken (nach 1-2 Minuten):
ls -lh /home/imreo/mcp-diploma-thesis-final/data/processed/
# → Datei sollte hier sein wenn erfolgreich verarbeitet
```

### Schritt 5: Automatische Verarbeitung

**Mit Watchdog Service (empfohlen):**
- ✅ Datei wird automatisch verarbeitet (5-30 Sekunden)
- ✅ Datei wird nach `processed/` verschoben wenn erfolgreich
- ✅ Datei wird nach `failed/` verschoben wenn fehlerhaft

**Manuell (falls Watchdog nicht läuft):**
- Imre muss manuell Ingestion starten
- Sie erhalten Bestätigung per Email

---

## 🔧 Troubleshooting

### Problem: "Connection refused"

**Ursache:** Tailscale nicht verbunden

**Lösung:**
```
1. Tailscale App öffnen
2. Status prüfen: Sollte "Connected" sein
3. Falls nicht: "Connect" klicken
4. Warten bis grüner Status
5. Upload erneut versuchen
```

### Problem: "Permission denied (publickey,password)"

**Ursache:** Falsches Passwort oder SSH-Key fehlt

**Lösung:**
```
1. Passwort von Imre erhalten
2. Richtig eingeben (copy-paste empfohlen)
3. Oder: SSH-Key Setup durchführen (siehe oben)
```

### Problem: "No such file or directory"

**Ursache:** Falscher Upload-Pfad

**Lösung:**
```
Korrekter Pfad:
/home/imreo/mcp-diploma-thesis-final/data/incoming/

Nicht:
/home/pi/...
/data/incoming/
~/incoming/
```

### Problem: "scp: command not found" (Windows)

**Ursache:** OpenSSH nicht installiert

**Lösung:**
```powershell
# Windows OpenSSH installieren:
# Settings → Apps → Optional Features → Add → OpenSSH Client

# Oder: Git Bash verwenden (enthält SCP)
# Download: https://git-scm.com/download/win
```

### Problem: Datei wird nicht verarbeitet

**Ursache:** JSONL-Format fehlerhaft

**Lösung:**
```
1. JSONL validieren:
   - Jede Zeile = 1 JSON-Objekt
   - Keine Arrays: [ ]
   - Keine Leerzeilen
   
2. Online-Validator verwenden:
   - https://jsonlint.com (für einzelne Lines)
   
3. Pflichtfelder prüfen:
   - id, title, content, metadata.frontmatter.access_level
```

### Problem: "Host key verification failed"

**Ursache:** SSH-Fingerprint ändert sich (nach Pi-Neuinstallation)

**Lösung:**
```bash
# Host-Key aus known_hosts entfernen:
ssh-keygen -R {{TAILSCALE_IP}}

# Upload erneut versuchen
# Bei "Are you sure?" → yes eingeben
```

---

## 📞 Support

Bei Problemen oder Fragen:

**Kontakt:** Obermüller Imre  
**Email:** imre.obermueller@gmail.com

**Hilfreiche Informationen bei Support-Anfrage:**
1. Ihr Betriebssystem (Windows/Mac/Linux)
2. Tailscale Status (Connected/Disconnected)
3. Exakte Fehlermeldung (Screenshot oder copy-paste)
4. Was haben Sie versucht?
5. Dateiname und -größe

---

## 📊 Upload-Statistik (optional)

Sie können Statistiken zu Ihren Uploads einsehen:

```bash
# SSH zum Pi
ssh imreo@100.73.228.15

# Statistiken anzeigen
cat /home/imreo/mcp-diploma-thesis-final/data/statistics/ingestion_stats.json
```

**Beispiel-Output:**
```json
{
  "total_documents": 1234,
  "by_access_level": {
    "student": 800,
    "teacher": 400,
    "admin": 34
  },
  "last_upload": "2026-01-06T14:30:00",
  "total_size_mb": 45.6
}
```

---

## ✅ Checkliste für ersten Upload

- [ ] Tailscale installiert
- [ ] Tailscale verbunden (grüner Status)
- [ ] Raspberry Pi im Tailscale-Netzwerk sichtbar
- [ ] Tailscale IP von Imre erhalten: `{{TAILSCALE_IP}}`
- [ ] Passwort von Imre erhalten (oder SSH-Key eingerichtet)
- [ ] JSONL-Datei erstellt und validiert
- [ ] Pflichtfelder vorhanden (id, title, content, access_level)
- [ ] Test-Upload durchgeführt
- [ ] Bestätigung von Imre erhalten (oder self-check)

**Viel Erfolg! 🚀**
