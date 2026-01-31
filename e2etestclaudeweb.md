LeoWiki Remote MCP Server - Funktionsübersicht
Tools:

search_content_student - Inhaltssuche mit Student-Zugriff
search_content_teacher - Inhaltssuche mit Teacher-Zugriff (voller Zugriff)
get_collection_stats - Detaillierte Sammlungsstatistiken (nur Teacher/Admin)
health_check - Server-Gesundheitsprüfung und Konnektivität

Resources:

leowiki://categories - Liste aller Inhaltskategorien
leowiki://access-levels - RBAC-Zugriffsebenen Dokumentation
leowiki://search-hints - Tipps für effektive Suche
leowiki://system-prompt - Richtlinien für Assistant-Verhalten
leowiki://stats - Statistiken über die Wissensdatenbank
leowiki://topic/{topic_id} - Details zu spezifischen Themen
leowiki://recent/{count} - Kürzlich aktualisierte Inhalte

Prompts:

explain_topic - Strukturierte Erklärung für Bildungsthemen
create_quiz - Quiz-Fragen generieren
compare_concepts - Vergleich verwandter Konzepte
summarize_search - Suchergebnisse zusammenfassen
learning_path - Lernpfad/Roadmap erstellen

Test-Ergebnisse:
✅ explain_topic Prompt
Input:

Topic: "Objektorientierte Programmierung"
Difficulty: "intermediate"
Include examples: true

Output: Strukturierte Anleitung für eine Erklärung mit:

Definition
Kernkonzepte (3-5 Punkte)
Warum ist das wichtig?
Praktische Beispiele
Häufige Fehler
Zusammenfassung

Kontext: HTL Leonding, Deutsch, schülerfreundlich

✅ summarize_search Prompt
Input:

Query: "Was ist der Unterschied zwischen Stack und Heap?"

Output: Anleitung zum Zusammenfassen von Suchergebnissen mit:

Logischer Strukturierung
Wichtigste Punkte hervorheben
Kohärente Verknüpfung der Ergebnisse
Weiterführende Themen empfehlen
Direkte Antwort ohne Meta-Kommentare
Deutsche Sprache, HTL Leonding Kontext

Hinweis: Bei include_examples muss der Boolean als String "true" übergeben werden, nicht als Boolean.

Test-Ergebnisse Resources:
✅ leowiki://categories
5 Kategorien verfügbar:

sew - Software Engineering 💻
nwt - Netzwerktechnik 🌐
medientechnik - Medientechnik 🎨
syp - Systemplanung 📊
allgemein - Allgemeine Informationen 📚

✅ leowiki://access-levels
3 Zugriffsebenen definiert:

Student - Unterrichtsmaterialien
Teacher - Inkl. Prüfungsmaterialien und Lösungen
Admin - Vollzugriff + Systemfunktionen

✅ leowiki://search-hints
Umfangreiche Suchhinweise in Markdown:

Tipps für effektive Suchanfragen
Kategorien nutzen
RBAC-Zugriffslevel erklärt
Troubleshooting bei keinen Ergebnissen

❌ leowiki://stats
Fehler: 'OptimizersStatusOneOf' object has no attribute 'status'
(Bug in der Implementierung - Qdrant-Status kann nicht abgerufen werden)
⚠️ leowiki://recent/5
Funktioniert, aber 0 Ergebnisse:

Keine kürzlich aktualisierten Inhalte in der DB
User-Role wird korrekt erkannt: "admin"

✅ leowiki://system-prompt
Sehr ausführliche Verhaltensrichtlinien für den Assistenten:

Natürliche, direkte Kommunikation
Strukturierung von Antworten
Quellenangaben
Sprachanpassung für Schüler/Lehrer
Beispiele für gute Antworten

Fazit: 5 von 6 Resources funktionieren. Der Stats-Endpoint hat einen Bug beim Abrufen des Qdrant-Status.