"""
Search Tools with RBAC Support

This module provides semantic search tools with role-based access control.
Following security-by-design principles, we provide TWO separate tools:

1. search_content_student - For students (limited access)
2. search_content_teacher - For teachers (full access)

This prevents parameter manipulation and enforces RBAC at the tool level.

Reference: refactor/leowiki_rbac_tools_implementation.md
"""

import logging
import threading
from typing import List, Dict, Any, Optional

from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from qdrant_client.models import Filter, FieldCondition, MatchAny

from src.backends import QdrantBackend, create_vector_backend
from src.config.server_config import ServerConfig
from src.utils.embeddings import EmbeddingService
from src.utils.query_logger import get_query_logger

logger = logging.getLogger(__name__)

# Global config
config = ServerConfig()

# Global services (lazy initialized, thread-safe)
_db: Optional[QdrantBackend] = None
_embedding_service: Optional[EmbeddingService] = None
_init_lock = threading.Lock()


def _get_services():
    """
    Thread-safe lazy initialization of database and embedding services.
    
    Uses double-checked locking pattern to ensure:
    1. Only one initialization happens even with concurrent requests
    2. Minimal locking overhead after initialization
    
    This is important when multiple students/teachers use the server simultaneously.
    """
    global _db, _embedding_service
    
    # Fast path: already initialized (no lock needed)
    if _db is not None and _embedding_service is not None:
        return _db, _embedding_service
    
    # Slow path: need to initialize (with lock for thread safety)
    with _init_lock:
        # Double-check after acquiring lock
        if _db is None:
            logger.info("Initializing search backend (lazy, thread-safe)...")
            _db = create_vector_backend(
                name=config.vector_db_backend,
                url=config.vector_db_url,
                api_key=config.vector_db_api_key
            )
            logger.info(f"✓ Backend initialized: {config.vector_db_backend}")
        
        if _embedding_service is None:
            logger.info("Initializing embedding service (lazy, thread-safe)...")
            _embedding_service = EmbeddingService(
                api_key=config.openai_api_key,
                model=config.embedding_model
            )
            logger.info(f"✓ Embedding service initialized: {config.embedding_model}")
    
    return _db, _embedding_service

# Access level hierarchies for RBAC
# Each role can see its own level plus all levels below it
ROLE_ACCESS_LEVELS = {
    "student": ["student"],
    "teacher": ["student", "teacher"],
    "admin": ["student", "teacher", "admin"],
}


def get_access_filter(user_role: str) -> Filter:
    """
    Create a Qdrant filter for role-based access control.
    
    Args:
        user_role: User's role (student, teacher, admin)
        
    Returns:
        Filter: Qdrant filter for access control
    """
    # Get allowed access levels for this role
    allowed_levels = ROLE_ACCESS_LEVELS.get(user_role, ["student"])
    
    # Create filter
    return Filter(
        must=[
            FieldCondition(
                key="access_level",
                match=MatchAny(any=allowed_levels)
            )
        ]
    )


def _format_search_results(results: list, query: str) -> str:
    """
    Format search results for user-friendly presentation.
    
    Follows UX guidelines from refactor/MCP_Server_Best_Practices_Diplomarbeit.md:
    - Answer First, Details Second, Metadata Last
    - No technical details (scores, counts, etc.)
    - Natural language presentation
    
    Args:
        results: List of search results from Qdrant
        query: Original search query
        
    Returns:
        Formatted string for presentation to user
    """
    if not results:
        return f"""Ich konnte leider keine passenden Informationen zu "{query}" finden.

Mögliche Gründe:
- Die Information ist noch nicht im Wiki dokumentiert
- Die Suche war zu spezifisch
- Das Dokument wurde noch nicht indexiert

Kann ich dir bei etwas anderem helfen?"""
    
    # Format each result
    formatted_parts = []
    for i, result in enumerate(results[:5], 1):  # Limit to top 5
        title = result.payload.get("title", "Untitled")
        text = result.payload.get("text", "")
        
        # Truncate long text
        if len(text) > 500:
            text = text[:500] + "..."
        
        # Build result entry
        entry = f"**{title}**\n\n{text}"
        
        # Add source info (minimal, at the end)
        source = result.payload.get("source", "LeoWiki")
        entry += f"\n\n(Quelle: {source})"
        
        formatted_parts.append(entry)
    
    # Join with separators
    return "\n\n" + "---\n\n".join(formatted_parts)


def register_search_tools(mcp: FastMCP) -> None:
    """
    Register TWO separate search tools for RBAC security.
    
    This function registers:
    1. search_content_student - Limited access for students
    2. search_content_teacher - Full access for teachers
    
    Security by Design: No parameter manipulation possible.
    
    Args:
        mcp: FastMCP server instance with lifespan context
    """
    
    @mcp.tool(
        name="search_content_student",
        description="Search educational content with student-level access",
        annotations=ToolAnnotations(
            title="LeoWiki Student Search",
            readOnlyHint=True,      # No side effects, safe to cache
            idempotentHint=True,    # Same input = same output
            openWorldHint=False,    # Results from known dataset
        ),
        tags={"search", "read-only", "student"}
    )
    async def search_content_student(
        query: str,
        limit: int = 10,
        ctx: Context = None
    ) -> dict:
        """
        Search educational content with STUDENT access level.
        
        WICHTIGE INSTRUKTIONEN FÜR CLAUDE:
        
        1. PRÄSENTATION:
           - Präsentiere Ergebnisse natürlich und direkt
           - NIEMALS technische Details wie Scores, Result-Counts oder Datenbankinfo erwähnen
           - Fokus auf den INHALT der Antwort, nicht die Mechanik
        
        2. STIL:
           - Kurze, präzise Antworten
           - Freundlicher aber professioneller Ton
           - Schülerfreundliche Sprache
        
        3. QUELLEN:
           - Nur am Ende, in Klammern
           - Format: "(Quelle: [Dokumenttyp])"
           - NICHT: Lange URLs oder technische Pfade
        
        4. FEHLERBEHANDLUNG:
           - Bei keinen Ergebnissen: Freundlich erklären, Alternativen anbieten
           - NICHT: "Der Server hat 0 Ergebnisse zurückgegeben"
           - SONDERN: "Ich konnte leider keine Informationen dazu finden"
        
        5. BEISPIELE:
        
           SCHLECHT:
           "Ich habe den Leowiki-Server abgefragt und 3 Ergebnisse mit Scores
           zwischen 0.4 und 0.6 erhalten. Result 1 (score: 0.45) zeigt..."
           
           GUT:
           "Java ist eine objektorientierte Programmiersprache. 
           Hier sind die wichtigsten Konzepte für Einsteiger..."
        
        Access Level: STUDENT
        - Public content
        - Student-level educational materials
        - Course materials and tutorials
        
        NOT Accessible:
        - Teacher-internal documents
        - Administrative content
        - Exam solutions (teacher-only)
        
        Args:
            query: Search query in natural language (German or English)
            limit: Maximum number of results (1-20, default: 10)
            ctx: MCP context (automatically provided)
            
        Returns:
            Formatted search results optimized for student presentation
            
        Examples:
            >>> search_content_student("Was ist OOP?", limit=5)
            "OOP steht für Objektorientierte Programmierung..."
            
            >>> search_content_student("Wie funktioniert Subnetting?")
            "Subnetting teilt ein Netzwerk in kleinere Subnetze..."
        """
        try:
            # Get services (lazy initialization)
            db, embedding_service = _get_services()
            
            # Validate input
            if not query or not query.strip():
                raise ToolError("Suchanfrage darf nicht leer sein")
            
            # Limit bounds
            limit = max(1, min(limit, 20))
            
            # Progress reporting: Step 1
            if ctx:
                await ctx.report_progress(0, 4, "Analysiere Suchanfrage...")
                await ctx.info(f"Suche nach: {query[:50]}{'...' if len(query) > 50 else ''}")
            
            # Generate embedding
            if ctx:
                await ctx.report_progress(1, 4, "Generiere Embedding...")
            query_embedding = embedding_service.embed_query(query)
            
            # Build RBAC filter for STUDENT access
            # Students CANNOT see teacher namespace content
            if ctx:
                await ctx.report_progress(2, 4, "Wende Zugriffs-Filter an...")
            
            # Execute search with dynamic loading for RBAC filtering
            # Students need enough results AFTER teacher content is filtered out
            if ctx:
                await ctx.report_progress(3, 4, "Durchsuche Wissensdatenbank...")
            
            if config.enable_rbac:
                # RBAC ENABLED: Dynamically fetch until we have enough student results
                # This ensures students always get the requested number of results
                results = []
                fetch_limit = limit * 3  # Start with 3x
                max_fetch = limit * 10   # Safety limit to prevent infinite loops
                
                while len(results) < limit and fetch_limit <= max_fetch:
                    raw_results = db.search(
                        query_vector=query_embedding,
                        collection=config.default_collection,
                        limit=fetch_limit,
                        filters=None  # No Qdrant filter - we filter in Python
                    )
                    
                    # Filter out teacher content for students
                    results = []
                    for result in raw_results:
                        source = result.payload.get("source", "") if hasattr(result, 'payload') else ""
                        # Students cannot see teacher namespace
                        if "teacher:" not in source:
                            results.append(result)
                            if len(results) >= limit:
                                break
                    
                    # If we don't have enough, fetch more
                    if len(results) < limit:
                        fetch_limit = fetch_limit * 2  # Double the fetch limit
                        logger.debug(f"[RBAC] Not enough student results, increasing fetch to {fetch_limit}")
                
                # Trim to requested limit
                results = results[:limit]
                logger.info(f"[RBAC] Student filter: fetched {fetch_limit}, returned {len(results)} student-accessible results")
            else:
                # RBAC DISABLED: Simple fetch
                raw_results = db.search(
                    query_vector=query_embedding,
                    collection=config.default_collection,
                    limit=limit,
                    filters=None
                )
                results = raw_results[:limit]
            
            # Format results
            if ctx:
                await ctx.report_progress(4, 4, "Formatiere Ergebnisse...")
            formatted = _format_search_results(results, query)
            
            # Log audit trail (FastMCP 3.0: async ctx methods)
            user_id = await ctx.get_state("user_id") if ctx else "anonymous"
            user_role = await ctx.get_state("user_role") if ctx else "student"
            request_id = await ctx.get_state("request_id") if ctx else None
            
            logger.info(
                f"[SEARCH_STUDENT] user={hash(user_id) if user_id else 'anon'}, query='{query[:30]}...', results={len(results)}"
            )
            
            # Persist query for statistics (educational analytics)
            try:
                query_logger = get_query_logger()
                query_logger.log_query(
                    query=query,
                    response=formatted,
                    user_role=user_role,
                    tool_name="search_content_student",
                    result_count=len(results),
                    user_id_hash=str(hash(user_id)) if user_id else None,
                    request_id=request_id
                )
            except Exception as log_err:
                logger.warning(f"Failed to persist query log: {log_err}")
            
            if ctx:
                await ctx.info(f"✓ {len(results)} Ergebnisse gefunden")
            
            return {
                "content": [{
                    "type": "text",
                    "text": formatted
                }]
            }
            
        except ToolError as e:
            logger.warning(f"Student search validation error: {e}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Fehler: {str(e)}"
                }],
                "isError": True
            }
        except Exception as e:
            # Log full error for debugging (server-side only)
            logger.error(f"Student search error: {e}", exc_info=True)
            # Return generic message - NO implementation details to users!
            return {
                "content": [{
                    "type": "text",
                    "text": "Es ist ein Fehler bei der Suche aufgetreten. Bitte versuche es erneut."
                }],
                "isError": True
            }
    
    
    @mcp.tool(
        name="search_content_teacher",
        description="Search educational content with teacher-level access (full access)",
        annotations=ToolAnnotations(
            title="LeoWiki Teacher Search",
            readOnlyHint=True,
            idempotentHint=True,
            openWorldHint=False,
        ),
        tags={"search", "read-only", "teacher"}
    )
    async def search_content_teacher(
        query: str,
        limit: int = 10,
        ctx: Context = None
    ) -> dict:
        """
        Search educational content with TEACHER access level.
        
        WICHTIGE INSTRUKTIONEN FÜR CLAUDE:
        
        1. PRÄSENTATION:
           - Präsentiere Ergebnisse natürlich und direkt
           - NIEMALS technische Details wie Scores, Result-Counts oder Datenbankinfo erwähnen
           - Fokus auf den INHALT der Antwort, nicht die Mechanik
        
        2. STIL:
           - Präzise und vollständig
           - Professionelle Sprache
           - Quellenangaben wichtig für Lehrer
        
        3. QUELLEN:
           - Am Ende, in Klammern
           - Format: "(Quelle: [Dokumenttyp])"
           - Vollständigere Info als bei Schülern (Lehrer brauchen Kontext)
        
        4. FEHLERBEHANDLUNG:
           - Bei keinen Ergebnissen: Professionell erklären
           - Alternativen vorschlagen
        
        5. BEISPIELE:
        
           SCHLECHT:
           "Die Suche im Lehrer-Tool ergab 5 Treffer mit hohen Scores..."
           
           GUT:
           "Der No-Blame-Approach ist eine Interventionsmethode bei Mobbing.
           Hier die Schritte für Klassenvorstände: ..."
        
        Access Level: TEACHER
        - All student content
        - Teacher-internal documents and resources
        - Exam materials and solutions
        - Administrative guidelines
        - All namespaces
        
        Args:
            query: Search query in natural language (German or English)
            limit: Maximum number of results (1-20, default: 10)
            ctx: MCP context (automatically provided)
            
        Returns:
            Formatted search results optimized for teacher presentation
            
        Examples:
            >>> search_content_teacher("No-Blame-Approach Anleitung", limit=5)
            "Der No-Blame-Approach ist eine bewährte Methode zur Intervention..."
            
            >>> search_content_teacher("Prüfungsfragen OOP 3AHIF")
            "Hier sind die Prüfungsfragen für OOP (3AHIF)..."
        """
        try:
            # Get services (lazy initialization)
            db, embedding_service = _get_services()
            
            # Validate input
            if not query or not query.strip():
                raise ToolError("Suchanfrage darf nicht leer sein")
            
            # Limit bounds
            limit = max(1, min(limit, 20))
            
            # Progress reporting: Step 1
            if ctx:
                await ctx.report_progress(0, 4, "Analysiere Suchanfrage...")
                await ctx.info(f"Lehrer-Suche: {query[:50]}{'...' if len(query) > 50 else ''}")
            
            # Generate embedding
            if ctx:
                await ctx.report_progress(1, 4, "Generiere Embedding...")
            query_embedding = embedding_service.embed_query(query)
            
            # TEACHER ACCESS: No filter needed - teachers see everything
            if ctx:
                await ctx.report_progress(2, 4, "Vollzugriff (Lehrer)...")
            
            # Execute search - NO FILTER for teachers (full access)
            if ctx:
                await ctx.report_progress(3, 4, "Durchsuche Wissensdatenbank...")
            results = db.search(
                query_vector=query_embedding,
                collection=config.default_collection,
                limit=limit,
                filters=None  # Teachers see ALL content including teacher namespace
            )
            
            logger.info(f"[RBAC] Teacher search: full access, {len(results)} results")
            
            # Format results
            if ctx:
                await ctx.report_progress(4, 4, "Formatiere Ergebnisse...")
            formatted = _format_search_results(results, query)
            
            # Log audit trail (FastMCP 3.0: async ctx methods)
            user_id = await ctx.get_state("user_id") if ctx else "anonymous"
            user_role = await ctx.get_state("user_role") if ctx else "teacher"
            request_id = await ctx.get_state("request_id") if ctx else None
            
            logger.info(
                f"[SEARCH_TEACHER] user={hash(user_id) if user_id else 'anon'}, query='{query[:30]}...', results={len(results)}"
            )
            
            # Persist query for statistics (educational analytics)
            try:
                query_logger = get_query_logger()
                query_logger.log_query(
                    query=query,
                    response=formatted,
                    user_role=user_role,
                    tool_name="search_content_teacher",
                    result_count=len(results),
                    user_id_hash=str(hash(user_id)) if user_id else None,
                    request_id=request_id
                )
            except Exception as log_err:
                logger.warning(f"Failed to persist query log: {log_err}")
            
            if ctx:
                await ctx.info(f"✓ {len(results)} Ergebnisse gefunden (Lehrer-Zugriff)")
            
            return {
                "content": [{
                    "type": "text",
                    "text": formatted
                }]
            }
            
        except ToolError as e:
            logger.warning(f"Teacher search validation error: {e}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Fehler: {str(e)}"
                }],
                "isError": True
            }
        except Exception as e:
            # Log full error for debugging (server-side only)
            logger.error(f"Teacher search error: {e}", exc_info=True)
            # Return generic message - NO implementation details to users!
            return {
                "content": [{
                    "type": "text",
                    "text": "Es ist ein Fehler bei der Suche aufgetreten. Bitte versuche es erneut."
                }],
                "isError": True
            }
    
    
    @mcp.tool(
        name="get_collection_stats",
        description="Get detailed collection statistics (teacher/admin only)",
        annotations=ToolAnnotations(
            title="Collection Statistics",
            readOnlyHint=True,
        ),
        tags={"admin", "stats", "monitoring"}
    )
    async def get_collection_stats(ctx: Context = None) -> dict:
        """
        Get statistics about the educational content collection.
        
        This tool is restricted to teachers and admins via RBACEnforcementMiddleware.
        
        Returns information about:
        - Total number of documents
        - Access level distribution
        - Collection health
        - Vector configuration
        
        Args:
            ctx: MCP context (automatically provided)
            
        Returns:
            Dictionary with collection statistics
        """
        try:
            # Get services (lazy initialization)
            db, _ = _get_services()
            
            user_role = await ctx.get_state("user_role") if ctx else "student"
            logger.info(f"Getting collection stats for role={user_role}")
            
            # Get collection info
            collection_info = db.client.get_collection(config.default_collection)
            total_count = collection_info.points_count
            
            # Analyze content distribution for RBAC
            # RBAC Logic: 
            #   - Schüler see everything WITHOUT "teacher:" in URL
            #   - Lehrer/Admin see EVERYTHING
            all_points = db.client.scroll(
                collection_name=config.default_collection,
                limit=10000,
                with_payload=["source"],
                with_vectors=False
            )[0]
            
            teacher_only_count = 0  # Documents with "teacher:" in URL
            student_accessible_count = 0  # Documents WITHOUT "teacher:" in URL
            
            for point in all_points:
                source = point.payload.get("source", "")
                if "teacher:" in source:
                    teacher_only_count += 1
                else:
                    student_accessible_count += 1
            
            access_distribution = {
                "teacher_only": teacher_only_count,
                "student_accessible": student_accessible_count,
                "total": len(all_points),
            }
            
            # Get optimizer status safely (API changed in qdrant-client 1.16+)
            optimizer_status = "unknown"
            if collection_info.optimizer_status:
                try:
                    # Try new API (qdrant-client 1.16+)
                    if hasattr(collection_info.optimizer_status, 'ok'):
                        optimizer_status = "ok" if collection_info.optimizer_status.ok else "optimizing"
                    elif hasattr(collection_info.optimizer_status, 'status'):
                        optimizer_status = collection_info.optimizer_status.status.name
                    else:
                        optimizer_status = str(collection_info.optimizer_status)
                except Exception:
                    optimizer_status = "unknown"
            
            stats = {
                "collection": config.default_collection,
                "total_documents": total_count,
                "vector_dimensions": collection_info.config.params.vectors.size,
                "distance_metric": collection_info.config.params.vectors.distance.name,
                "access_levels": access_distribution,
                "rbac_enabled": config.enable_rbac,
                "segments_count": collection_info.segments_count,
                "optimizer_status": optimizer_status,
            }
            
            # Calculate what each role can see
            student_sees = access_distribution["student_accessible"]
            teacher_sees = access_distribution["total"]  # Lehrer sehen ALLES
            teacher_only = access_distribution["teacher_only"]
            
            return {
                "content": [{
                    "type": "text",
                    "text": f"""**Collection Statistics**

Collection: {stats['collection']}
Total Documents: {stats['total_documents']}
Vector Dimensions: {stats['vector_dimensions']}
Distance Metric: {stats['distance_metric']}

**RBAC Content Access:**
- Schüler sehen: {student_sees} Dokumente
- Lehrer/Admin sehen: {teacher_sees} Dokumente (alle)
- Nur für Lehrer (teacher: namespace): {teacher_only} Dokumente

**System Status:**
- RBAC: {'Enabled' if stats['rbac_enabled'] else 'Disabled'}
- Segments: {stats['segments_count']}
- Optimizer: {stats['optimizer_status']}"""
                }]
            }
            
        except Exception as e:
            # Log full error for debugging (server-side only)
            logger.error(f"Error getting collection stats: {e}", exc_info=True)
            # Return generic message - NO implementation details to users!
            return {
                "content": [{
                    "type": "text",
                    "text": "Fehler beim Abrufen der Statistiken. Bitte versuche es später erneut."
                }],
                "isError": True
            }
    
    @mcp.tool(
        name="get_query_statistics",
        description="Statistiken über Benutzeranfragen abrufen (nur Admin). Zeigt wie viele Anfragen von welcher Rolle gestellt wurden.",
        annotations=ToolAnnotations(
            title="Query-Statistiken",
            readOnlyHint=True,
            openWorldHint=False
        )
    )
    async def get_query_statistics(ctx: Context) -> dict:
        """
        Get statistics about user queries for educational analytics.
        
        RBAC: admin only
        
        Returns:
            Query statistics including count by role, tool usage, etc.
        """
        try:
            query_logger = get_query_logger()
            stats = query_logger.get_statistics()
            
            if stats.get("total_queries", 0) == 0:
                return {
                    "content": [{
                        "type": "text",
                        "text": "**Query-Statistiken**\n\nNoch keine Anfragen protokolliert."
                    }]
                }
            
            by_role = stats.get("by_role", {})
            by_tool = stats.get("by_tool", {})
            
            role_breakdown = "\n".join([f"- {role}: {count}" for role, count in by_role.items()])
            tool_breakdown = "\n".join([f"- {tool}: {count}" for tool, count in by_tool.items()])
            
            return {
                "content": [{
                    "type": "text",
                    "text": f"""**Query-Statistiken (Educational Analytics)**

**Gesamtanzahl Anfragen:** {stats['total_queries']}

**Nach Benutzer-Rolle:**
{role_breakdown}

**Nach Tool:**
{tool_breakdown}

*Log-Datei: {stats.get('log_file', 'N/A')}*"""
                }]
            }
            
        except Exception as e:
            logger.error(f"Error getting query statistics: {e}", exc_info=True)
            return {
                "content": [{
                    "type": "text",
                    "text": "Fehler beim Abrufen der Query-Statistiken."
                }],
                "isError": True
            }
    
    logger.info("Registered 4 search tools: search_content_student, search_content_teacher, get_collection_stats, get_query_statistics")
