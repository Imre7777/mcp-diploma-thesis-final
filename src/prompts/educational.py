"""
Educational Prompt Templates for LeoWiki MCP Server

This module provides reusable prompt templates for common educational workflows:
- Topic explanations with pedagogical structure
- Search result summarization

These prompts help LLMs generate better educational content by providing
clear structure and guidelines.
"""

import logging
from fastmcp import FastMCP, Context

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
    
    logger.info("Registered 2 educational prompts: explain_topic, summarize_search")
