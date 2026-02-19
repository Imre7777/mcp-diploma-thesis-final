# Golden Query Tests - LeoWiki MCP Server

## Übersicht

Die Golden Query Tests sind ein standardisiertes Testverfahren zur Evaluierung der semantischen Suchqualität des LeoWiki MCP Servers. Sie simulieren typische Anfragen von HTL-Schülern und Lehrern und messen, wie gut das System relevante Inhalte findet.

**Testdatum:** 2026-02-19  
**Collection:** educational_content  
**Dokumente:** 3,417 (indexed)  
**Embedding Model:** OpenAI text-embedding-3-large (3072 Dimensionen)  
**Vector DB:** Qdrant  

---

## Test-Methodik

### Scoring

- **Cosine Similarity Score**: Wertebereich 0.0 - 1.0, höher = bessere Übereinstimmung
- **Keyword Hit Rate**: Anteil der erwarteten Schlüsselwörter im Ergebnis

### Relevanz-Bewertung (automatisch)

| Keyword Hit Rate | Relevanz Score |
|------------------|----------------|
| ≥ 80% | 5 (Exzellent) |
| ≥ 60% | 4 (Gut) |
| ≥ 40% | 3 (Befriedigend) |
| ≥ 20% | 2 (Ausreichend) |
| < 20% | 1 (Mangelhaft) |

---

## Golden Queries Definition

| ID | Name | Frage | Erwartete Keywords |
|----|------|-------|-------------------|
| GQ01 | DA Format (Word?) | Darf ich meine Diplomarbeit mit MS Word schreiben? | Diplomarbeit, Format, Word |
| GQ02 | Matura Klausurtag | Wann ist Einlass am Klausurtag der Matura? | Matura, Klausur, Einlass |
| GQ03 | Office365 Mail | Ab wann gibt es die neuen Office365 Mail Accounts? | Office365, Mail, Account |
| GQ04 | Exkursion organisieren | Was ist zu beachten, wenn ich eine Exkursion organisiere? | Exkursion, organisieren, Leitfaden, Genehmigung |
| GQ05 | Exkursion Antrag | Wo finde ich das Antragsformular für Exkursionen? | Exkursion, Antrag, Formular, Download |
| GQ06 | DA kein Thema | Was ist wenn ich kein Thema für eine Diplomarbeit finde? | Diplomarbeit, Thema, Betreuung, Koordinator |
| GQ07 | Company Thesis Day | Was ist der Company Thesis Day? | Company Thesis Day, Diplomarbeit, Firmen |
| GQ08 | Dresscode Präsentation | Wie lautet der Dresscode für Diplomarbeitspräsentationen? | Diplomarbeit, Präsentation, Dresscode, Kleidung |

---

## Detaillierte Ergebnisse

### GQ01: DA Format (Word?)

**Frage:** Darf ich meine Diplomarbeit mit MS Word schreiben?

| Metrik | Wert |
|--------|------|
| **Top Score** | 0.5729 |
| **Source** | https://leowiki.htl-leonding.ac.at/doku.php?id=exams:da-inf-it |
| **Keywords Hit** | Diplomarbeit, Format, Word |
| **Keywords Miss** | - |
| **Hit Rate** | 100% (3/3) |
| **Relevanz** | ⭐⭐⭐⭐⭐ (5) |

**Top 3 Ergebnisse:**
| Rank | Score | Source |
|------|-------|--------|
| #1 | 0.5729 | exams:da-inf-it |
| #2 | 0.5663 | exams:da-inf-it |
| #3 | 0.5512 | exams:da-inf-it |

**Preview:** *"...cke zulassen - Die Entscheidung, was ein Laber-Textblock ist, wird von den Betreuer:innen gefällt..."*

---

### GQ02: Matura Klausurtag

**Frage:** Wann ist Einlass am Klausurtag der Matura?

| Metrik | Wert |
|--------|------|
| **Top Score** | 0.7109 |
| **Source** | https://leowiki.htl-leonding.ac.at/doku.php?id=exams:matura-tagesschule-allgemein |
| **Keywords Hit** | Klausur, Einlass |
| **Keywords Miss** | Matura |
| **Hit Rate** | 67% (2/3) |
| **Relevanz** | ⭐⭐⭐⭐ (4) |

**Top 3 Ergebnisse:**
| Rank | Score | Source |
|------|-------|--------|
| #1 | 0.7109 | exams:matura-tagesschule-allgemein |
| #2 | 0.6308 | - |
| #3 | 0.6173 | - |

**Preview:** *"#### Am Klausurtag - **ca. 7:30 - 8:00:** Die Vorbereitung der Säle erfolgt durch die Fachlehrer:i..."*

**Bemerkung:** Höchster Score aller Tests. Sehr präzise Treffer für Klausurtag-Informationen.

---

### GQ03: Office365 Mail

**Frage:** Ab wann gibt es die neuen Office365 Mail Accounts?

| Metrik | Wert |
|--------|------|
| **Top Score** | 0.5939 |
| **Source** | https://leowiki.htl-leonding.ac.at/doku.php?id=it:studentmail |
| **Keywords Hit** | Office365, Mail, Account |
| **Keywords Miss** | - |
| **Hit Rate** | 100% (3/3) |
| **Relevanz** | ⭐⭐⭐⭐⭐ (5) |

**Top 3 Ergebnisse:**
| Rank | Score | Source |
|------|-------|--------|
| #1 | 0.5939 | it:studentmail |
| #2 | 0.5750 | - |
| #3 | 0.5620 | - |

**Preview:** *"# Studentmail - Das neue Mailkonto ist als Office365 Konto im Mailclient hinzuzufügen..."*

---

### GQ04: Exkursion organisieren

**Frage:** Was ist zu beachten, wenn ich eine Exkursion organisiere?

| Metrik | Wert |
|--------|------|
| **Top Score** | 0.5859 |
| **Source** | https://leowiki.htl-leonding.ac.at/doku.php?id=teacher:neulehrerinnenhandbuch:teaching |
| **Keywords Hit** | Exkursion, Genehmigung |
| **Keywords Miss** | organisieren, Leitfaden |
| **Hit Rate** | 50% (2/4) |
| **Relevanz** | ⭐⭐⭐ (3) |

**Top 3 Ergebnisse:**
| Rank | Score | Source |
|------|-------|--------|
| #1 | 0.5859 | teacher:neulehrerinnenhandbuch:teaching |
| #2 | 0.5119 | - |
| #3 | 0.4727 | - |

**Preview:** *"##### Exkursionen, Lehrausgänge - Exkursionen müssen bewilligt werden. Das zugehörige [Antragsformul..."*

**Bemerkung:** Schwächste Relevanz. Das Ergebnis ist korrekt (Lehrer-Handbuch), aber nicht alle Keywords wurden gefunden.

---

### GQ05: Exkursion Antrag

**Frage:** Wo finde ich das Antragsformular für Exkursionen?

| Metrik | Wert |
|--------|------|
| **Top Score** | 0.7055 |
| **Source** | https://leowiki.htl-leonding.ac.at/doku.php?id=org:forms:exkursion |
| **Keywords Hit** | Exkursion, Antrag, Formular |
| **Keywords Miss** | Download |
| **Hit Rate** | 75% (3/4) |
| **Relevanz** | ⭐⭐⭐⭐ (4) |

**Top 3 Ergebnisse:**
| Rank | Score | Source |
|------|-------|--------|
| #1 | 0.7055 | org:forms:exkursion |
| #2 | 0.6786 | - |
| #3 | 0.6291 | - |

**Preview:** *"Title: Antrag auf Exkursion / Wandertag / Lehrausgang - Namespace: org:forms - Content_Type: FORM_COLLEC..."*

**Bemerkung:** Zweithöchster Score. Direkter Treffer auf das Antragsformular.

---

### GQ06: DA kein Thema

**Frage:** Was ist wenn ich kein Thema für eine Diplomarbeit finde?

| Metrik | Wert |
|--------|------|
| **Top Score** | 0.5366 |
| **Source** | https://leowiki.htl-leonding.ac.at/doku.php?id=exams:da-inf-it |
| **Keywords Hit** | Diplomarbeit, Thema, Betreuung |
| **Keywords Miss** | Koordinator |
| **Hit Rate** | 75% (3/4) |
| **Relevanz** | ⭐⭐⭐⭐ (4) |

**Top 3 Ergebnisse:**
| Rank | Score | Source |
|------|-------|--------|
| #1 | 0.5366 | exams:da-inf-it |
| #2 | 0.5111 | - |
| #3 | 0.4994 | - |

**Preview:** *"...zu erarbeiten. So wie immer lassen allgemeine Definitionen einen gewissen Interpretationsspielraum..."*

---

### GQ07: Company Thesis Day

**Frage:** Was ist der Company Thesis Day?

| Metrik | Wert |
|--------|------|
| **Top Score** | 0.5399 |
| **Source** | https://leowiki.htl-leonding.ac.at/doku.php?id=exams:da-inf-it |
| **Keywords Hit** | Company Thesis Day, Diplomarbeit, Firmen |
| **Keywords Miss** | - |
| **Hit Rate** | 100% (3/3) |
| **Relevanz** | ⭐⭐⭐⭐⭐ (5) |

**Top 3 Ergebnisse:**
| Rank | Score | Source |
|------|-------|--------|
| #1 | 0.5399 | exams:da-inf-it |
| #2 | 0.5091 | - |
| #3 | 0.4678 | - |

**Preview:** *"Title: Diplomarbeiten in der Informatik und IT Medientechnik - Namespace: exams - Content_Type: NEWS..."*

---

### GQ08: Dresscode Präsentation

**Frage:** Wie lautet der Dresscode für Diplomarbeitspräsentationen?

| Metrik | Wert |
|--------|------|
| **Top Score** | 0.6764 |
| **Source** | https://leowiki.htl-leonding.ac.at/doku.php?id=exams:da-inf-it |
| **Keywords Hit** | Diplomarbeit, Präsentation, Kleidung |
| **Keywords Miss** | Dresscode |
| **Hit Rate** | 75% (3/4) |
| **Relevanz** | ⭐⭐⭐⭐ (4) |

**Top 3 Ergebnisse:**
| Rank | Score | Source |
|------|-------|--------|
| #1 | 0.6764 | exams:da-inf-it |
| #2 | 0.5646 | - |
| #3 | 0.5511 | - |

**Preview:** *"...karton. Alternativ kann auch ein Deckblatt mit bedrucktem Karton anstatt der Folie verwendet werden..."*

---

## Zusammenfassung

### Ergebnis-Tabelle

| GQ ID | Name | Score | Keywords Hit | Keywords Miss | Relevanz |
|-------|------|-------|--------------|---------------|----------|
| GQ01 | DA Format (Word?) | 0.573 | Diplomarbeit, Format, Word | - | 5 |
| GQ02 | Matura Klausurtag | 0.711 | Klausur, Einlass | Matura | 4 |
| GQ03 | Office365 Mail | 0.594 | Office365, Mail, Account | - | 5 |
| GQ04 | Exkursion organisieren | 0.586 | Exkursion, Genehmigung | organisieren, Leitfaden | 3 |
| GQ05 | Exkursion Antrag | 0.705 | Exkursion, Antrag, Formular | Download | 4 |
| GQ06 | DA kein Thema | 0.537 | Diplomarbeit, Thema, Betreuung | Koordinator | 4 |
| GQ07 | Company Thesis Day | 0.540 | Company Thesis Day, Diplomarbeit, Firmen | - | 5 |
| GQ08 | Dresscode Präsentation | 0.676 | Diplomarbeit, Präsentation, Kleidung | Dresscode | 4 |

### Statistiken

| Metrik | Wert |
|--------|------|
| **Durchschnittlicher Score** | 0.615 |
| **Höchster Score** | 0.711 (GQ02 - Matura Klausurtag) |
| **Niedrigster Score** | 0.537 (GQ06 - DA kein Thema) |
| **Durchschnittliche Relevanz** | 4.25 / 5 |
| **Tests mit Relevanz 5** | 4 (50%) |
| **Tests mit Relevanz 4** | 3 (37.5%) |
| **Tests mit Relevanz 3** | 1 (12.5%) |
| **Gesamt Keyword Hit Rate** | 79% (23/29) |

### Score-Verteilung

```
Score Range     | Count | Queries
----------------|-------|---------------------------
0.70 - 0.80     | 2     | GQ02, GQ05
0.60 - 0.70     | 2     | GQ03, GQ08
0.50 - 0.60     | 4     | GQ01, GQ04, GQ06, GQ07
```

---

## Analyse

### Stärken

1. **Hohe Trefferquote bei spezifischen Themen**
   - Matura-Klausurtag (0.711) und Exkursion-Antrag (0.705) zeigen exzellente Ergebnisse
   - Das System findet präzise die richtigen Dokumente

2. **Konsistente Qualität**
   - Alle Tests erreichen mindestens Relevanz 3
   - 87.5% der Tests erreichen Relevanz 4 oder besser

3. **Gute Keyword-Abdeckung**
   - 79% aller erwarteten Keywords werden gefunden
   - 50% der Tests erreichen 100% Keyword-Hit-Rate

### Verbesserungspotenzial

1. **GQ04 (Exkursion organisieren)**
   - Niedrigste Relevanz (3)
   - Keywords "organisieren" und "Leitfaden" nicht gefunden
   - Mögliche Lösung: Synonyme oder mehr Content zum Thema

2. **Fehlende Keywords**
   - "Matura" in GQ02 nicht gefunden (obwohl Inhalt korrekt)
   - "Download" in GQ05 fehlt
   - "Dresscode" in GQ08 fehlt (nur "Kleidung" gefunden)

3. **Score-Varianz**
   - Unterschied zwischen höchstem (0.711) und niedrigstem (0.537) Score = 0.174
   - Einige Queries könnten von besseren Embeddings profitieren

---

## Test-Ausführung

### Voraussetzungen

- Docker Container läuft (`mcp-server`, `mcp-qdrant`)
- OPENAI_API_KEY ist gesetzt (im Container)
- qdrant-client >= 1.7
- openai Python-Package

### Befehle

```bash
# Im Docker Container ausführen
docker exec mcp-server python /app/scripts/run_golden_queries.py \
    --qdrant http://mcp-qdrant:6333

# Nur Health-Check
docker exec mcp-server python /app/scripts/run_golden_queries.py \
    --health-only

# Mit anderem Server
docker exec mcp-server python /app/scripts/run_golden_queries.py \
    --url https://other-server.com \
    --qdrant http://other-qdrant:6333
```

### Output

- **Terminal:** Markdown-Tabelle für Testing-Protokoll
- **JSON:** `data/statistics/golden_query_results.json`

---

## Vergleich mit Host-Clients

Diese Golden Query Results können mit den Ergebnissen verglichen werden, die ein Host-Client (Claude, ChatGPT, etc.) über die MCP-Tools erhält:

| Aspekt | Golden Query (direkt) | Host-Client (MCP) |
|--------|----------------------|-------------------|
| Methode | Direkt gegen Qdrant | Über MCP Tools |
| Embedding | OpenAI API | OpenAI API (gleich) |
| RBAC | Nicht angewendet | Wird angewendet |
| Antwort-Format | Raw Scores + Preview | Formatierter Text |
| Vergleichbar | Ja (gleiche Embeddings) | Ja (gleiche Daten) |

### Erwartete Unterschiede

1. **Schüler-Suche:** Sollte keine Teacher-Inhalte zeigen (RBAC-Filter)
2. **Lehrer-Suche:** Sollte alle Inhalte zeigen
3. **Score:** Sollte identisch sein (gleiche Vektoren)
4. **Formatierung:** Host-Clients formatieren die Antwort schöner

---

## Anhang: Raw JSON Results

Die vollständigen Ergebnisse werden in `data/statistics/golden_query_results.json` gespeichert:

```json
[
  {
    "id": "GQ01",
    "name": "DA Format (Word?)",
    "top_title": "",
    "top_score": 0.57297266,
    "keywords_hit": ["Diplomarbeit", "Format", "Word"],
    "keywords_miss": [],
    "top3": [["", 0.57297266], ["", 0.56638944], ["", 0.55122685]]
  },
  ...
]
```

---

## Changelog

| Datum | Version | Änderung |
|-------|---------|----------|
| 2026-02-19 | 1.0 | Initial Golden Query Test Run |

---

*Generiert mit `scripts/run_golden_queries.py`*
