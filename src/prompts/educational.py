"""
Educational Prompt Templates for LeoWiki MCP Server

This module provides reusable prompt templates for common educational workflows:
- Topic explanations with pedagogical structure
- Quiz generation for assessment
- Concept comparisons for understanding
- Search result summarization
- Learning path planning

These prompts help LLMs generate better educational content by providing
clear structure and guidelines.
"""

import logging
from fastmcp import FastMCP, Context
from fastmcp.prompts import Message

logger = logging.getLogger(__name__)


def register_educational_prompts(mcp: FastMCP):
    """
    Register educational prompt templates with the MCP server.
    
    Args:
        mcp: FastMCP server instance
    """
    
    @mcp.prompt(
        name="explain_topic",
        description="Generate a structured explanation for an educational topic",
        tags={"education", "explanation", "german"}
    )
    def explain_topic(
        topic: str,
        difficulty: str = "intermediate",
        include_examples: bool = True
    ) -> str:
        """
        Creates a pedagogically structured explanation request.
        
        This prompt template helps generate educational explanations that follow
        best practices for learning and comprehension.
        
        Args:
            topic: The topic to explain (e.g., "Polymorphismus", "TCP/IP")
            difficulty: beginner, intermediate, or advanced
            include_examples: Whether to include practical examples
            
        Returns:
            Structured prompt for topic explanation
        """
        difficulty_map = {
            "beginner": "Anfänger (keine Vorkenntnisse)",
            "intermediate": "Fortgeschritten (Grundkenntnisse vorhanden)",
            "advanced": "Experte (vertiefte Kenntnisse)"
        }
        
        prompt = f"""Erkläre das Thema "{topic}" für einen Schüler auf dem Niveau: {difficulty_map.get(difficulty, difficulty)}.

Strukturiere deine Erklärung wie folgt:

## 1. Definition
Eine klare, präzise Definition des Konzepts in 1-2 Sätzen.

## 2. Kernkonzepte
Die wichtigsten Aspekte, die man verstehen muss (3-5 Punkte).

## 3. Warum ist das wichtig?
Praktische Relevanz und Anwendungsgebiete im echten Leben.
"""
        
        if include_examples:
            prompt += """
## 4. Praktische Beispiele
Konkrete Codebeispiele oder Anwendungsfälle mit Erklärung.

## 5. Häufige Fehler
Typische Missverständnisse und wie man sie vermeidet.
"""
        
        prompt += """
## Zusammenfassung
Die wichtigsten Punkte in 2-3 Sätzen zum Wiederholen.

**Kontext:** HTL Leonding, Informatik-Ausbildung
**Sprache:** Deutsch
**Stil:** Klar, präzise, schülerfreundlich
"""
        return prompt
    
    
    @mcp.prompt(
        name="create_quiz",
        description="Generate quiz questions for a topic",
        tags={"education", "quiz", "assessment"}
    )
    def create_quiz(
        topic: str,
        num_questions: int = 5,
        question_type: str = "mixed",
        difficulty: str = "intermediate"
    ) -> str:
        """
        Creates a quiz generation prompt.
        
        Args:
            topic: Subject for the quiz
            num_questions: Number of questions (1-10)
            question_type: multiple_choice, true_false, short_answer, or mixed
            difficulty: beginner, intermediate, advanced
            
        Returns:
            Structured prompt for quiz generation
        """
        # Limit questions to reasonable range
        num_questions = min(max(num_questions, 1), 10)
        
        type_instructions = {
            "multiple_choice": "Multiple-Choice mit 4 Optionen (A-D)",
            "true_false": "Wahr/Falsch-Fragen",
            "short_answer": "Kurzantwort-Fragen",
            "mixed": "Eine Mischung aus verschiedenen Fragetypen"
        }
        
        return f"""Erstelle ein Quiz zum Thema "{topic}".

**Anforderungen:**
- Anzahl Fragen: {num_questions}
- Fragetyp: {type_instructions.get(question_type, question_type)}
- Schwierigkeitsgrad: {difficulty}

**Für jede Frage:**
1. Klare, eindeutige Fragestellung
2. Bei Multiple-Choice: 4 Optionen, eine davon korrekt
3. Korrekte Antwort deutlich markiert
4. Kurze Erklärung (1-2 Sätze) warum die Antwort richtig ist

**Format:** 
```json
{{
  "topic": "{topic}",
  "difficulty": "{difficulty}",
  "questions": [
    {{
      "id": 1,
      "type": "multiple_choice",
      "question": "...",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct": "B",
      "explanation": "..."
    }}
  ]
}}
```

**Qualitätskriterien:**
- Fragen testen Verständnis, nicht nur Auswendiglernen
- Distraktoren (falsche Antworten) sind plausibel aber eindeutig falsch
- Erklärungen helfen beim Lernen

**Kontext:** HTL Informatik-Ausbildung
**Sprache:** Deutsch
"""
    
    
    @mcp.prompt(
        name="compare_concepts",
        description="Compare two or more related concepts",
        tags={"education", "comparison", "analysis"}
    )
    def compare_concepts(
        concepts: str,  # Comma-separated: "Vererbung, Komposition"
        aspects: str = "definition,usage,advantages,disadvantages"
    ) -> str:
        """
        Creates a comparison prompt for related concepts.
        
        Args:
            concepts: Comma-separated list of concepts to compare
            aspects: Comma-separated aspects to compare
            
        Returns:
            Structured comparison prompt
        """
        concept_list = [c.strip() for c in concepts.split(",")]
        aspect_list = [a.strip() for a in aspects.split(",")]
        
        aspects_german = {
            "definition": "Definition",
            "usage": "Verwendung",
            "advantages": "Vorteile",
            "disadvantages": "Nachteile",
            "examples": "Beispiele",
            "performance": "Performance",
            "complexity": "Komplexität"
        }
        
        aspects_formatted = [
            aspects_german.get(a.lower(), a.title()) for a in aspect_list
        ]
        
        return f"""Vergleiche die folgenden Konzepte: {', '.join(concept_list)}

Erstelle eine strukturierte Vergleichsanalyse mit folgenden Aspekten:

{chr(10).join(f'## {aspect}' + chr(10) + f'- Vergleich von {" vs. ".join(concept_list)}' for aspect in aspects_formatted)}

**Format:**
Verwende eine Vergleichstabelle wo sinnvoll für bessere Übersichtlichkeit.

**Abschluss:**
### Wann welches Konzept verwenden?
- Praktische Entscheidungshilfe mit konkreten Szenarien
- Empfehlungen basierend auf Anwendungsfall

**Kontext:** HTL Informatik-Ausbildung
**Sprache:** Deutsch
**Stil:** Objektiv, faktenbasiert, hilfreich für Lernende
"""
    
    
    @mcp.prompt(
        name="summarize_search",
        description="Summarize search results into a coherent answer",
        tags={"search", "summary", "synthesis"}
    )
    async def summarize_search(
        query: str,
        ctx: Context
    ) -> str:
        """
        Creates a prompt to summarize search results.
        
        This prompt helps synthesize multiple search results into a
        coherent, comprehensive answer. It uses the server's categories
        resource for context.
        
        Args:
            query: Original user query
            ctx: MCP context for resource access
            
        Returns:
            Prompt for summarizing search results
        """
        # Read the categories resource for context
        try:
            categories = await ctx.read_resource("leowiki://categories")
            categories_content = categories.content
        except:
            categories_content = "Kategorien nicht verfügbar"
        
        return f"""Der Benutzer hat nach "{query}" gesucht.

**Verfügbare Kategorien im LeoWiki:**
{categories_content}

**Deine Aufgabe:**
1. Fasse die relevanten Suchergebnisse zusammen
2. Strukturiere die Information logisch und übersichtlich
3. Hebe die wichtigsten Punkte hervor
4. Verknüpfe verschiedene Ergebnisse zu einem kohärenten Ganzen
5. Empfehle weiterführende Themen falls relevant

**Präsentations-Richtlinien:**
- Beginne direkt mit der Antwort (keine Meta-Kommentare wie "Die Suche ergab...")
- Nutze klare Überschriften und Struktur
- Quellenangaben dezent am Ende in Klammern
- Deutsche Sprache, schülerfreundlich

**Sprache:** Deutsch
**Kontext:** HTL Leonding Informatik-Ausbildung
"""
    
    
    @mcp.prompt(
        name="learning_path",
        description="Generate a learning roadmap for a topic",
        tags={"education", "planning", "curriculum", "roadmap"}
    )
    def learning_path(
        goal: str,
        current_level: str = "beginner",
        time_available: str = "1 month"
    ) -> list[Message]:
        """
        Creates a multi-turn learning path conversation.
        
        This prompt helps students plan their learning journey with
        structured milestones and resources.
        
        Args:
            goal: Learning goal (e.g., "Java Backend Development")
            current_level: Current knowledge level
            time_available: Time frame for learning
            
        Returns:
            Multi-message prompt for learning path generation
        """
        return [
            Message(
                role="user",
                content=f"""Ich möchte "{goal}" lernen.

**Meine Situation:**
- Aktuelles Niveau: {current_level}
- Verfügbare Zeit: {time_available}
- Kontext: HTL Informatik-Ausbildung

Bitte erstelle einen strukturierten Lernplan mit:

1. **Voraussetzungen prüfen**
   - Welche Vorkenntnisse sollte ich haben?
   - Welche Grundlagen muss ich zuerst auffrischen?

2. **Themen-Roadmap**
   - Wochenweise oder nach Meilensteinen aufgeteilt
   - Logische Reihenfolge (Grundlagen → Fortgeschritten)

3. **Ressourcen aus dem LeoWiki**
   - Welche Materialien im Wiki sind relevant?
   - In welcher Reihenfolge sollte ich sie durchgehen?

4. **Praktische Übungen**
   - Konkrete Übungsprojekte zum Anwenden
   - Steigende Schwierigkeit

5. **Selbstüberprüfung**
   - Meilensteine mit Checkpoints
   - Wie erkenne ich, dass ich bereit für den nächsten Schritt bin?

Bitte sei spezifisch und praxisorientiert!"""
            ),
            Message(
                role="assistant",
                content=f"""Sehr gerne erstelle ich dir einen personalisierten Lernplan für "{goal}"!

Lass mich zuerst die verfügbaren Ressourcen im LeoWiki prüfen und dann einen strukturierten Plan erstellen, der zu deinem Niveau ({current_level}) und deinem Zeitrahmen ({time_available}) passt.

Ich beginne mit der Analyse der Voraussetzungen und baue dann einen schrittweisen Lernpfad auf..."""
            )
        ]
    
    logger.info("Registered 5 educational prompts: explain_topic, create_quiz, compare_concepts, summarize_search, learning_path")
