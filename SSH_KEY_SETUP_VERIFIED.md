# ✅ SSH Key Setup - Verifiziert und Bereit

**Datum:** 06. Januar 2026  
**Status:** 🟢 **SSH-Key vom Kollegen erfolgreich hinterlegt**

---

## ✅ Setup-Status

| Check | Status | Details |
|-------|--------|---------|
| **SSH-Key hinterlegt** | ✅ | 1 Key in `~/.ssh/authorized_keys` |
| **Berechtigungen korrekt** | ✅ | `.ssh/` = 700, `authorized_keys` = 600 |
| **SSH-Server läuft** | ✅ | Active seit 3 Tagen |
| **Upload-Verzeichnis** | ✅ | `incoming/` Owner: imreo:imreo, 755 |
| **Tailscale aktiv** | ✅ | IP: 100.73.228.15 |

---

## 🔑 Hinterlegter SSH-Key

**Key-Typ:** `ssh-ed25519` (modern, sicher, schnell)  
**Email/Identifier:** `cell.enohp.apps@gmail.com`  
**Fingerprint:** Letzter Teil des Keys: `...7MHLjnbd`

**Voller Key (für Referenz):**
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIA2rK3cdu/gdf7gKJ+kVmvWFuJbeCC/WuDTE7MHLjnbd cell.enohp.apps@gmail.com
```

---

## 📂 Verzeichnis-Struktur

```
/home/imreo/mcp-diploma-thesis-final/data/
├── incoming/     (drwxr-xr-x imreo:imreo) ← Upload hier
├── processed/    (drwxr-xr-x imreo:imreo) ← Erfolgreich verarbeitet
└── failed/       (drwxr-xr-x imreo:imreo) ← Fehlgeschlagene Dateien
```

**Berechtigungen:** ✅ Alle Verzeichnisse gehören User `imreo`

---

## 🔒 SSH-Konfiguration

**File:** `~/.ssh/authorized_keys`
- **Berechtigungen:** `600` (rw-------) ✅
- **Owner:** `imreo:imreo` ✅
- **Anzahl Keys:** 1 ✅

**SSH-Server:**
- **Status:** Active (running) seit 3 Tagen ✅
- **Port:** 22 (Standard) ✅
- **Key-Auth:** Enabled ✅

---

## 📤 Upload-Befehle für Kollegen

### Variante 1: Mit Tailscale IP (empfohlen)

```bash
scp datei.jsonl imreo@100.73.228.15:/home/imreo/mcp-diploma-thesis-final/data/incoming/
```

### Variante 2: Mit Hostname (Magic DNS)

```bash
scp datei.jsonl imreo@raspi-docker:/home/imreo/mcp-diploma-thesis-final/data/incoming/
```

### Beispiel mit Test-Datei:

```bash
# Test-JSONL erstellen:
echo '{"id":"test_001","title":"Upload Test","content":"Testing SSH key upload","metadata":{"frontmatter":{"access_level":"student"}}}' > test_upload.jsonl

# Hochladen:
scp test_upload.jsonl imreo@100.73.228.15:/home/imreo/mcp-diploma-thesis-final/data/incoming/

# Erwartete Ausgabe:
# test_upload.jsonl    100%  123B   1.2MB/s   00:00
```

**WICHTIG:** 
- ✅ **KEIN Passwort wird mehr abgefragt!**
- ✅ Upload funktioniert automatisch mit SSH-Key
- ✅ Sicher und bequem

---

## 🧪 Test-Schritte für Kollegen

### Test 1: SSH-Verbindung

```bash
ssh imreo@100.73.228.15

# Erwartung:
# - KEINE Passwort-Abfrage!
# - Direkt eingeloggt
# - Prompt: imreo@raspi-docker:~$
```

Wenn eingeloggt:
```bash
# Verzeichnis prüfen:
ls -lh /home/imreo/mcp-diploma-thesis-final/data/incoming/

# Ausloggen:
exit
```

### Test 2: Datei hochladen

```bash
# Test-Datei erstellen:
echo '{"id":"test_001","title":"SSH Test","content":"Test","metadata":{"frontmatter":{"access_level":"student"}}}' > test.jsonl

# Upload:
scp test.jsonl imreo@100.73.228.15:/home/imreo/mcp-diploma-thesis-final/data/incoming/

# Sollte OHNE Passwort-Abfrage funktionieren! ✅
```

### Test 3: Upload verifizieren

```bash
# SSH zum Pi:
ssh imreo@100.73.228.15

# Datei checken:
ls -lh /home/imreo/mcp-diploma-thesis-final/data/incoming/
# → test.jsonl sollte da sein!

# Inhalt prüfen (optional):
cat /home/imreo/mcp-diploma-thesis-final/data/incoming/test.jsonl

# Exit:
exit
```

---

## ✅ Was funktioniert OHNE Passwort

Mit dem hinterlegten SSH-Key funktioniert alles OHNE Passwort-Eingabe:

- ✅ `ssh imreo@100.73.228.15` - Einloggen
- ✅ `scp file.jsonl imreo@100.73.228.15:/path/` - Datei hochladen
- ✅ `rsync -avz files/ imreo@100.73.228.15:/path/` - Sync (falls benötigt)
- ✅ Automatisierung via Scripts möglich

---

## 🔧 Troubleshooting

### Problem: "Permission denied (publickey)"

**Mögliche Ursachen:**

1. **Falscher Private Key wird verwendet**
   ```bash
   # Kollege prüft welcher Key verwendet wird:
   ssh -v imreo@100.73.228.15 2>&1 | grep "Offering public key"
   
   # Sollte zeigen:
   # Offering public key: ... SHA256:... ed25519 cell.enohp.apps@gmail.com
   ```

2. **SSH-Agent läuft nicht**
   ```bash
   # SSH-Agent starten (Linux/Mac):
   eval "$(ssh-agent -s)"
   ssh-add ~/.ssh/id_ed25519
   
   # Windows (PowerShell):
   Start-Service ssh-agent
   ssh-add $env:USERPROFILE\.ssh\id_ed25519
   ```

3. **Falscher Private Key-Pfad**
   ```bash
   # Explizit Key angeben:
   ssh -i ~/.ssh/id_ed25519 imreo@100.73.228.15
   scp -i ~/.ssh/id_ed25519 file.jsonl imreo@100.73.228.15:/path/
   ```

### Problem: "Host key verification failed"

**Lösung:**
```bash
# Known hosts bereinigen:
ssh-keygen -R 100.73.228.15
ssh-keygen -R raspi-docker

# Erneut connecten:
ssh imreo@100.73.228.15
# Bei "Are you sure?" → yes
```

### Problem: Passwort wird DOCH abgefragt

**Ursachen:**

1. **Falscher Key wird angeboten**
   - Kollege verwendet falschen Private Key
   - Lösung: Explizit Key angeben mit `-i`

2. **Key nicht im SSH-Agent**
   - Lösung: `ssh-add ~/.ssh/id_ed25519`

3. **Berechtigungen falsch (auf Kollegen-PC)**
   ```bash
   # Kollege prüft seine Berechtigungen:
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/id_ed25519
   chmod 644 ~/.ssh/id_ed25519.pub
   ```

---

## 🔐 Sicherheits-Features

### SSH-Key Vorteile

- ✅ **Sicherer als Passwort:** Kein Passwort kann geraten/bruteforced werden
- ✅ **Bequemer:** Kein Passwort-Tippen mehr
- ✅ **Automatisierbar:** Scripts können ohne User-Interaktion laufen
- ✅ **Audit-Trail:** Key hat Identifier (Email) für Logging

### Berechtigungen

**Auf dem Pi (bereits gesetzt):**
```bash
~/.ssh/                  → 700 (drwx------)  ✅
~/.ssh/authorized_keys   → 600 (-rw-------)  ✅
```

**Beim Kollegen (sollte so sein):**
```bash
~/.ssh/                  → 700 (drwx------)
~/.ssh/id_ed25519        → 600 (-rw-------)  # Private Key!
~/.ssh/id_ed25519.pub    → 644 (-rw-r--r--)  # Public Key
```

### Key-Rotation (Optional für später)

Falls später ein neuer Key benötigt wird:

```bash
# Neuer Key generieren:
ssh-keygen -t ed25519 -C "new_email@example.com" -f ~/.ssh/id_ed25519_new

# Neuen Public Key an Sie senden
# Sie fügen ihn zu authorized_keys hinzu (neue Zeile)
# Alter Key kann dann entfernt werden
```

---

## 📊 Server-Logs (für Debugging)

Falls Probleme auftreten, können Sie die SSH-Logs überprüfen:

```bash
# SSH-Authentication Logs:
sudo tail -f /var/log/auth.log | grep -i ssh

# Bei erfolgreichem Login sollte stehen:
# "Accepted publickey for imreo from 100.92.229.90 port XXXXX ssh2: ED25519 SHA256:..."
```

---

## 📝 Zusammenfassung für Kollegen

**Was Sie wissen müssen:**

1. **SSH-Key ist hinterlegt** ✅
   - Ihr Public Key ist auf dem Pi
   - Upload funktioniert OHNE Passwort

2. **Upload-Befehl:**
   ```bash
   scp ihre_datei.jsonl imreo@100.73.228.15:/home/imreo/mcp-diploma-thesis-final/data/incoming/
   ```

3. **Testen:**
   - Erstellen Sie eine Test-Datei
   - Upload mit SCP
   - Sollte OHNE Passwort-Abfrage funktionieren

4. **Bei Problemen:**
   - Überprüfen Sie ob Ihr Private Key korrekt ist
   - SSH-Agent starten: `eval "$(ssh-agent -s)"` → `ssh-add ~/.ssh/id_ed25519`
   - Kontakt: imre.obermueller@gmail.com

---

## ✅ Checkliste - Alles bereit

- [x] SSH-Key vom Kollegen hinterlegt
- [x] Berechtigungen korrekt gesetzt (600 für authorized_keys)
- [x] SSH-Server läuft
- [x] Upload-Verzeichnisse existieren und haben korrekte Berechtigungen
- [x] Tailscale aktiv (100.73.228.15)
- [x] Test-Datei erstellt (/tmp/test_upload.jsonl)

**Status:** 🟢 **Bereit für Upload!**

**Kollege kann jetzt:**
- ✅ SSH ohne Passwort
- ✅ SCP Upload ohne Passwort
- ✅ JSONL-Dateien hochladen

---

## 📞 Bei Fragen

**Administrator:** Obermüller Imre  
**Email:** imre.obermueller@gmail.com  
**Tailscale IP:** 100.73.228.15  
**Hostname:** raspi-docker

**Für Support bitte angeben:**
- Betriebssystem (Windows/Mac/Linux)
- Exakte Fehlermeldung
- Output von: `ssh -v imreo@100.73.228.15` (erste 20 Zeilen)
