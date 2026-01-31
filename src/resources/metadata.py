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
    
    logger.info("Registered 3 metadata resources: categories, access-levels, search-hints")
