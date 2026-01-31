"""
Static Metadata Resources for LeoWiki MCP Server

This module provides static resources that describe the server's capabilities,
structure, and usage guidelines. These resources help LLMs understand how to
effectively use the educational content search system.
"""

import json
import logging
from fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_metadata_resources(mcp: FastMCP):
    """
    Register static metadata resources with the MCP server.
    
    Args:
        mcp: FastMCP server instance
    """
    
    @mcp.resource(
        uri="leowiki://categories",
        name="Content Categories",
        description="List of all available content categories in LeoWiki",
        mime_type="application/json",
        tags={"metadata", "navigation"}
    )
    def get_categories() -> str:
        """
        Returns available content categories with descriptions.
        
        These categories help organize educational content by subject area
        and make it easier to narrow down search results.
        """
        categories = [
            {
                "id": "sew",
                "name": "Software Engineering",
                "name_de": "Softwareentwicklung",
                "description": "Programming, OOP, Design Patterns, Web Development",
                "description_de": "Programmierung, OOP, Design Patterns, Webentwicklung",
                "icon": "💻"
            },
            {
                "id": "nwt",
                "name": "Network Technology",
                "name_de": "Netzwerktechnik",
                "description": "Networking, Cisco, Protocols, Security",
                "description_de": "Netzwerke, Cisco, Protokolle, Sicherheit",
                "icon": "🌐"
            },
            {
                "id": "medientechnik",
                "name": "Media Technology",
                "name_de": "Medientechnik",
                "description": "Graphics, Video, Audio, Web Design",
                "description_de": "Grafik, Video, Audio, Webdesign",
                "icon": "🎨"
            },
            {
                "id": "syp",
                "name": "Systems Engineering",
                "name_de": "Systemplanung",
                "description": "Project Management, Requirements, Testing",
                "description_de": "Projektmanagement, Anforderungen, Testing",
                "icon": "📊"
            },
            {
                "id": "allgemein",
                "name": "General Information",
                "name_de": "Allgemeine Informationen",
                "description": "School info, Schedules, Guidelines",
                "description_de": "Schulinfos, Stundenpläne, Richtlinien",
                "icon": "📚"
            }
        ]
        
        return json.dumps(categories, ensure_ascii=False, indent=2)
    
    
    @mcp.resource(
        uri="leowiki://access-levels",
        name="Access Level Documentation",
        description="Explains the RBAC access levels and their permissions",
        mime_type="application/json",
        tags={"metadata", "rbac", "documentation"}
    )
    def get_access_levels() -> str:
        """
        Returns RBAC level descriptions.
        
        Explains what content each role can access and typical use cases.
        """
        levels = {
            "student": {
                "name": "Student",
                "name_de": "Schüler",
                "description": "Access to student-level educational content",
                "description_de": "Zugriff auf Unterrichtsmaterialien für Schüler",
                "can_access": ["student"],
                "typical_users": "HTL students",
                "typical_users_de": "HTL Schüler",
                "example_content": [
                    "Course materials and tutorials",
                    "Public documentation",
                    "General school information"
                ],
                "example_content_de": [
                    "Unterrichtsmaterialien und Tutorials",
                    "Öffentliche Dokumentation",
                    "Allgemeine Schulinformationen"
                ]
            },
            "teacher": {
                "name": "Teacher",
                "name_de": "Lehrer", 
                "description": "Access to student and teacher content including exam materials",
                "description_de": "Zugriff auf Schüler- und Lehrerinhalte inkl. Prüfungsmaterialien",
                "can_access": ["student", "teacher"],
                "typical_users": "HTL teachers and staff",
                "typical_users_de": "HTL Lehrer und Mitarbeiter",
                "example_content": [
                    "All student content",
                    "Teacher resources and guides",
                    "Exam materials and solutions",
                    "Internal documentation"
                ],
                "example_content_de": [
                    "Alle Schülerinhalte",
                    "Lehrerressourcen und Anleitungen",
                    "Prüfungsmaterialien und Lösungen",
                    "Interne Dokumentation"
                ]
            },
            "admin": {
                "name": "Administrator",
                "name_de": "Administrator",
                "description": "Full access to all content and administrative functions",
                "description_de": "Vollzugriff auf alle Inhalte und Verwaltungsfunktionen",
                "can_access": ["student", "teacher", "admin"],
                "typical_users": "IT administrators, department heads",
                "typical_users_de": "IT-Administratoren, Abteilungsvorstände",
                "example_content": [
                    "All content at all levels",
                    "System statistics and health",
                    "User management functions",
                    "Configuration and settings"
                ],
                "example_content_de": [
                    "Alle Inhalte auf allen Ebenen",
                    "Systemstatistiken und Status",
                    "Benutzerverwaltung",
                    "Konfiguration und Einstellungen"
                ]
            }
        }
        
        return json.dumps(levels, ensure_ascii=False, indent=2)
    
    
    @mcp.resource(
        uri="leowiki://search-hints",
        name="Search Tips",
        description="Tips for effective searching in LeoWiki",
        mime_type="text/markdown",
        tags={"help", "documentation", "tutorial"}
    )
    def get_search_hints() -> str:
        """
        Returns search usage tips and best practices.
        
        Helps users formulate better queries and understand search capabilities.
        """
        return """# LeoWiki Search Tips

## Effektive Suchanfragen

### Spezifische Begriffe verwenden
- ✅ **Gut**: "Java ArrayList iteration"
- ❌ **Zu breit**: "Java"

### Deutsche Begriffe bevorzugen
Der Großteil der Inhalte ist auf Deutsch:
- ✅ "OOP Vererbung Polymorphismus"
- ❌ "OOP inheritance polymorphism" (funktioniert, aber weniger Treffer)

### Mehrere Konzepte kombinieren
- "Subnetting IPv4 Beispiele"
- "Python Datenstrukturen Listen"

## Kategorien nutzen

Verfügbare Kategorien (über `leowiki://categories` Resource):
- `sew` - Software Engineering
- `nwt` - Netzwerktechnik
- `medientechnik` - Medientechnik
- `syp` - Systemplanung
- `allgemein` - Allgemeine Informationen

**Beispiel:** Suche nach "Subnetting" in Kategorie "nwt"

## Zugriffslevel (RBAC)

Ergebnisse werden automatisch nach deiner Rolle gefiltert:

### Schüler (Student)
- Zugriff auf Unterrichtsmaterialien
- Tutorials und Anleitungen
- Öffentliche Dokumente

### Lehrer (Teacher)
- Alle Schülerinhalte
- Prüfungsmaterialien und Lösungen
- Lehrerressourcen
- Interne Dokumentation

### Admin
- Vollzugriff auf alle Inhalte
- Systemstatistiken
- Verwaltungsfunktionen

## Keine Ergebnisse gefunden?

1. **Breitere Suchbegriffe** verwenden
2. **Kategorie-Filter entfernen**
3. **Rechtschreibung prüfen** (besonders bei deutschen Begriffen)
4. **Synonyme ausprobieren** (z.B., "Netzwerk" vs "Network")
5. **Englische Begriffe testen** (manche Materialien sind auf Englisch)

## Tipps für Lehrer

- Nutze spezifische Fachbegriffe aus dem Lehrplan
- Suche nach Dokumenttypen: "Prüfung", "Lösung", "Übung"
- Kombiniere Klasse und Thema: "3AHIF OOP"

## Support

Bei Problemen oder Fragen:
- Wiki: https://leowiki.htl-leonding.ac.at
- Support: leowiki-support@htl-leonding.ac.at
"""
    
    
    @mcp.resource(
        uri="leowiki://system-prompt",
        name="Assistant Behavior Guidelines",
        description="Guidelines for how Claude should present search results and interact with users",
        mime_type="text/markdown",
        tags={"system", "behavior", "guidelines"}
    )
    def get_system_prompt() -> str:
        """
        Returns behavioral guidelines for Claude when using LeoWiki.
        
        This resource provides instructions on how to present information
        naturally and helpfully to students and teachers.
        """
        return """# LeoWiki Assistent - Verhaltensrichtlinien

## Deine Rolle

Du bist ein **freundlicher und kompetenter Lernassistent** für Schüler und Lehrer der HTL Leonding. 
Dein Ziel ist es, Wissen verständlich und hilfreich zu vermitteln.

---

## Wie du antworten sollst

### 1. Natürlich und direkt sprechen

**So JA:**
> Java ist eine objektorientierte Programmiersprache, die sich besonders für 
> größere Softwareprojekte eignet. Die wichtigsten Konzepte sind Klassen, 
> Objekte und Vererbung...

**So NICHT:**
> Ich habe die Datenbank abgefragt und 5 Ergebnisse mit einem Score von 0.7 
> gefunden. Das erste Ergebnis (ID: 12345, score: 0.72) enthält...

### 2. Antworten strukturieren

Wenn du mehrere Informationen hast, präsentiere sie übersichtlich:

**Bei einem klaren Thema:**
- Beginne mit einer kurzen Erklärung
- Gehe dann auf Details ein
- Nenne praktische Beispiele wenn möglich

**Bei mehreren Treffern:**
- Fasse die wichtigsten Punkte zusammen
- Gruppiere ähnliche Informationen
- Hebe besonders relevante Inhalte hervor

### 3. Alle gefundenen Informationen nutzen

Wenn du mehrere relevante Ergebnisse findest:

✅ **Gut:** Kombiniere die Informationen zu einer vollständigen Antwort
```
Zum Thema Subnetting habe ich folgende Informationen gefunden:

**Grundlagen:** Subnetting teilt ein Netzwerk in kleinere Teilnetze...

**Berechnung:** Die Subnetzmaske bestimmt, welche Bits zum Netzwerkteil gehören...

**Beispiel:** Bei /24 stehen 254 Host-Adressen zur Verfügung...
```

❌ **Nicht:** Jeden Treffer einzeln auflisten wie eine Datenbankantwort

### 4. Quellenangaben

- Nenne die Quelle nur am Ende, kurz und unaufdringlich
- Format: `(Quelle: LeoWiki)` oder `(Aus dem LeoWiki)`
- KEINE langen URLs oder technischen Pfade

### 5. Sprache anpassen

**Für Schüler:**
- Einfache, klare Sprache
- Fachbegriffe erklären
- Praktische Beispiele aus dem Alltag

**Für Lehrer:**
- Präzise und vollständig
- Fachterminologie verwenden
- Referenzen zu weiterführenden Materialien

---

## Bei keinen Ergebnissen

Antworte freundlich und hilfsbereit:

> Zu deiner Frage über [Thema] konnte ich leider keine passenden Informationen 
> im LeoWiki finden. Das kann bedeuten, dass dieses Thema noch nicht 
> dokumentiert wurde.
>
> Kann ich dir vielleicht bei einem verwandten Thema helfen? Oder möchtest du 
> die Frage anders formulieren?

---

## Beispiele für gute Antworten

### Beispiel 1: Einfache Frage

**Frage:** "Was ist OOP?"

**Antwort:**
> **Objektorientierte Programmierung (OOP)** ist ein Programmierparadigma, 
> das auf dem Konzept von "Objekten" basiert. Diese Objekte enthalten 
> sowohl Daten (Attribute) als auch Funktionen (Methoden).
>
> **Die vier Grundprinzipien:**
> 1. **Abstraktion** - Komplexität verbergen, nur Wesentliches zeigen
> 2. **Kapselung** - Daten und Methoden zusammenfassen und schützen
> 3. **Vererbung** - Eigenschaften von einer Klasse an andere weitergeben
> 4. **Polymorphismus** - Gleiche Schnittstelle, unterschiedliches Verhalten
>
> In der HTL Leonding lernst du OOP hauptsächlich mit Java und C#.
> (Quelle: LeoWiki)

### Beispiel 2: Komplexeres Thema

**Frage:** "Wie funktioniert Subnetting?"

**Antwort:**
> **Subnetting** ist eine Methode, um ein IP-Netzwerk in kleinere Teilnetze 
> (Subnetze) aufzuteilen. Das ist wichtig für:
> - Effizientere Nutzung von IP-Adressen
> - Bessere Netzwerksicherheit durch Segmentierung
> - Reduzierung von Broadcast-Traffic
>
> **So funktioniert's:**
> Die Subnetzmaske bestimmt, welcher Teil einer IP-Adresse das Netzwerk 
> und welcher Teil den Host identifiziert. Bei einer /24-Maske (255.255.255.0) 
> sind die ersten 24 Bits für das Netzwerk reserviert.
>
> **Beispiel:**
> - Netzwerk: 192.168.1.0/24
> - Verfügbare Hosts: 192.168.1.1 bis 192.168.1.254
> - Broadcast: 192.168.1.255
>
> (Quelle: LeoWiki Netzwerktechnik)

---

## Zusammenfassung

1. **Sei natürlich** - Sprich wie ein hilfreicher Tutor, nicht wie eine Suchmaschine
2. **Sei informativ** - Nutze alle relevanten Informationen für eine vollständige Antwort
3. **Sei strukturiert** - Präsentiere Informationen übersichtlich
4. **Sei freundlich** - Auch bei Fehlern oder leeren Ergebnissen
5. **Sei präzise** - Fokussiere auf das, was der Benutzer wissen möchte
"""
    
    logger.info("Registered 4 metadata resources: categories, access-levels, search-hints, system-prompt")
