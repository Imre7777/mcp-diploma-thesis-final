# 🔍 SSH-Key Troubleshooting - Warum Passwort noch abgefragt wird

**Problem:** Kollege muss beim Upload noch das Passwort eingeben, obwohl SSH-Key hinterlegt ist.

**Server-Status:** ✅ Alles korrekt konfiguriert!
- SSH-Key ist auf dem Server in `authorized_keys`
- Berechtigungen sind korrekt (600)
- SSH-Server akzeptiert Key-Auth (`pubkeyauthentication yes`)
- ed25519 Keys werden akzeptiert

**→ Problem liegt auf der KOLLEGEN-SEITE!**

---

## 🎯 Wahrscheinliche Ursache

Der **Private Key** auf dem PC des Kollegen **passt NICHT** zum **Public Key** auf dem Server!

### Mögliche Szenarien:

1. **Kollege hat den falschen Public Key geschickt**
   - Er hat mehrere SSH-Keys und den falschen geschickt
   
2. **Kollege verwendet den falschen Private Key**
   - Er hat mehrere Keys und SSH verwendet den falschen
   
3. **Kollege hat den Private Key nicht**
   - Public Key wurde von einem anderen PC generiert
   - Private Key wurde gelöscht oder ist nicht zugänglich

---

## ✅ Lösung: Key-Paar überprüfen

### Schritt 1: Kollege prüft welche Keys er hat

**Auf seinem PC ausführen:**

```bash
# Alle SSH-Keys anzeigen:
ls -la ~/.ssh/

# Sollte zeigen (Beispiel):
# id_ed25519       ← Private Key
# id_ed25519.pub   ← Public Key
```

### Schritt 2: Public Key vom Kollegen anzeigen

```bash
# Public Key anzeigen:
cat ~/.ssh/id_ed25519.pub

# Sollte ausgeben:
# ssh-ed25519 AAAAC3Nz... cell.enohp.apps@gmail.com
```

**WICHTIG:** Dieser Public Key muss **EXAKT** übereinstimmen mit dem Key auf dem Server!

**Key auf dem Server ist:**
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIA2rK3cdu/gdf7gKJ+kVmvWFuJbeCC/WuDTE7MHLjnbd cell.enohp.apps@gmail.com
```

### Schritt 3: Keys vergleichen

**Kollege macht:**
```bash
# Fingerprint des Public Keys berechnen:
ssh-keygen -lf ~/.ssh/id_ed25519.pub

# Output (Beispiel):
# 256 SHA256:abc123... cell.enohp.apps@gmail.com (ED25519)
```

**Ich mache auf dem Server:**
```bash
# Fingerprint des hinterlegten Keys:
ssh-keygen -lf ~/.ssh/authorized_keys

# Sollte den GLEICHEN Fingerprint zeigen!
```

**Wenn unterschiedlich → Keys passen nicht zusammen!**

---

## 🔧 Lösungen je nach Situation

### Situation A: Kollege hat den richtigen Private Key

**Test:**
```bash
# Explizit den Key angeben:
ssh -i ~/.ssh/id_ed25519 imreo@100.73.228.15

# Sollte OHNE Passwort funktionieren
```

**Falls es funktioniert:**
```bash
# SSH-Config erstellen damit Key automatisch verwendet wird:
nano ~/.ssh/config

# Einfügen:
Host raspi-docker
    HostName 100.73.228.15
    User imreo
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes

# Dann funktioniert:
ssh raspi-docker  # OHNE Passwort
scp file.jsonl raspi-docker:/home/imreo/mcp-diploma-thesis-final/data/incoming/
```

### Situation B: Kollege hat den Private Key nicht

**→ Neues Key-Paar generieren!**

**Kollege macht:**
```bash
# 1. Neuen Key generieren:
ssh-keygen -t ed25519 -C "cell.enohp.apps@gmail.com"

# Speicherort: ~/.ssh/id_ed25519_new (oder Standard überschreiben)

# 2. Public Key anzeigen:
cat ~/.ssh/id_ed25519_new.pub

# 3. Public Key an mich senden
```

**Ich mache:**
```bash
# Neuen Public Key zu authorized_keys hinzufügen:
nano ~/.ssh/authorized_keys

# Key einfügen (neue Zeile, den alten drin lassen!)
# Speichern
```

### Situation C: Kollege hat mehrere Keys

**Problem:** SSH verwendet automatisch den ersten Key, der nicht passt.

**Lösung 1: SSH-Config** (empfohlen)
```bash
# ~/.ssh/config erstellen/bearbeiten:
Host raspi-docker
    HostName 100.73.228.15
    User imreo
    IdentityFile ~/.ssh/id_ed25519  # Richtigen Key angeben!
    IdentitiesOnly yes  # NUR diesen Key verwenden
```

**Lösung 2: Explizit Key angeben**
```bash
# Bei jedem Befehl:
ssh -i ~/.ssh/id_ed25519 imreo@100.73.228.15
scp -i ~/.ssh/id_ed25519 file.jsonl imreo@100.73.228.15:/path/
```

**Lösung 3: SSH-Agent**
```bash
# Key zum Agent hinzufügen:
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Dann sollte es funktionieren
```

---

## 🧪 Debug-Befehle für Kollegen

### Test 1: Verbose SSH-Verbindung

```bash
ssh -vvv imreo@100.73.228.15

# Output analysieren:
# Suchen nach: "Offering public key"
# Zeigt welcher Key verwendet wird

# Suchen nach: "Server accepts key"
# Zeigt ob Server den Key akzeptiert

# Suchen nach: "Authentications that can continue: publickey,password"
# Bedeutet: Key wurde NICHT akzeptiert
```

**Beispiel Output (erfolgreich):**
```
debug1: Offering public key: /home/user/.ssh/id_ed25519 ED25519 SHA256:...
debug1: Server accepts key: /home/user/.ssh/id_ed25519 ED25519 SHA256:...
debug1: Authentication succeeded (publickey).
```

**Beispiel Output (fehlgeschlagen):**
```
debug1: Offering public key: /home/user/.ssh/id_ed25519 ED25519 SHA256:...
debug1: Authentications that can continue: publickey,password
debug1: Next authentication method: password
```

### Test 2: Welche Keys werden angeboten?

```bash
ssh -v imreo@100.73.228.15 2>&1 | grep "Offering public key"

# Zeigt alle Keys die SSH anbietet
# Einer davon muss zum Server-Key passen!
```

### Test 3: Key-Fingerprint vergleichen

**Kollege:**
```bash
ssh-keygen -lf ~/.ssh/id_ed25519.pub
# Output: 256 SHA256:XYZ... cell.enohp.apps@gmail.com (ED25519)
```

**Ich auf dem Server:**
```bash
ssh-keygen -lf ~/.ssh/authorized_keys
# Output: 256 SHA256:XYZ... cell.enohp.apps@gmail.com (ED25519)
```

**SHA256-Hash muss IDENTISCH sein!**

---

## 📋 Checkliste für Kollegen

Bitte folgende Befehle ausführen und mir die Outputs schicken:

```bash
# 1. Welche SSH-Keys hast du?
ls -la ~/.ssh/

# 2. Public Key anzeigen:
cat ~/.ssh/id_ed25519.pub

# 3. Fingerprint des Public Keys:
ssh-keygen -lf ~/.ssh/id_ed25519.pub

# 4. Verbose SSH-Test:
ssh -vvv imreo@100.73.228.15 2>&1 | grep -E "Offering|accepts|Authentications"

# 5. Welche Keys werden angeboten:
ssh -v imreo@100.73.228.15 2>&1 | grep "Offering public key"
```

**Mit diesen Infos kann ich das Problem exakt identifizieren!**

---

## 🎯 Schnellste Lösung

**Falls alles zu kompliziert ist:**

### Option 1: Neues Key-Paar generieren (5 Minuten)

**Kollege:**
```bash
# Backup des alten Keys (falls vorhanden):
mv ~/.ssh/id_ed25519 ~/.ssh/id_ed25519.old 2>/dev/null
mv ~/.ssh/id_ed25519.pub ~/.ssh/id_ed25519.pub.old 2>/dev/null

# Neuen Key generieren:
ssh-keygen -t ed25519 -C "cell.enohp.apps@gmail.com"
# Enter, Enter, Enter (keine Passphrase)

# Public Key anzeigen:
cat ~/.ssh/id_ed25519.pub

# → Mir den KOMPLETTEN Key schicken!
```

**Ich:**
```bash
# Neuen Key zu authorized_keys hinzufügen:
echo "NEUER_PUBLIC_KEY_HIER" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Test:
ssh-keygen -lf ~/.ssh/authorized_keys  # Sollte neuen Key zeigen
```

**Kollege:**
```bash
# Test ohne Passwort:
ssh imreo@100.73.228.15

# Sollte jetzt funktionieren! ✅
```

---

## 📞 Was ich jetzt brauche

**Bitte vom Kollegen:**

1. **Output von:** `cat ~/.ssh/id_ed25519.pub`
   - Damit ich sehen kann ob Keys übereinstimmen

2. **Output von:** `ssh-keygen -lf ~/.ssh/id_ed25519.pub`
   - Fingerprint zum Vergleich

3. **Output von:** `ssh -vvv imreo@100.73.228.15 2>&1 | head -50`
   - Erste 50 Zeilen des Verbose-Outputs
   - Zeigt welcher Key angeboten wird

**Mit diesen 3 Outputs kann ich das Problem sofort lösen!**

---

## ⚡ Schnelltest

**Kollege macht:**
```bash
# Dieser Befehl zeigt ob ein funktionierender Private Key vorhanden ist:
ssh -o PreferredAuthentications=publickey -o PubkeyAuthentication=yes imreo@100.73.228.15 echo "KEY WORKS"

# Wenn "KEY WORKS" angezeigt wird → Key funktioniert!
# Wenn "Permission denied" → Key funktioniert NICHT
```

---

## 🔐 Server ist OK - Problem beim Kollegen!

**Server-Konfiguration (alles ✅):**
```
✅ pubkeyauthentication yes
✅ passwordauthentication yes  
✅ ssh-ed25519 wird akzeptiert
✅ authorized_keys hat richtigen Key
✅ Berechtigungen korrekt (600)
✅ SSH-Server läuft
```

**→ Der Private Key beim Kollegen passt nicht zum Public Key auf dem Server!**

Lassen Sie uns das zusammen debuggen - schicken Sie mir die 3 Outputs und wir finden die Lösung! 🔍
