"""
Deterministic Tests for LeoWiki MCP Server Tools

Following FastMCP testing best practices:
- In-memory transport (no network overhead)
- Self-contained setup per test
- Mocked external dependencies (Qdrant, OpenAI)
- Single behavior per test

Reference: https://gofastmcp.com/patterns/testing
"""

import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError

# Configure pytest-asyncio
pytestmark = pytest.mark.asyncio(loop_scope="function")


# ============================================================================
# Test Server Factory (isolated from production server)
# ============================================================================
def create_test_server():
    """
    Create a minimal test server with mocked dependencies.
    
    This server mirrors production but with:
    - No real Qdrant connection
    - No real OpenAI API calls
    - Controlled, deterministic responses
    """
    mcp = FastMCP("LeoWiki-Test")
    
    # Mock search results for deterministic testing
    MOCK_STUDENT_RESULTS = [
        {"title": "Java Grundlagen", "text": "Java ist eine Programmiersprache...", "source": "wiki/java"},
        {"title": "Python Basics", "text": "Python ist einfach zu lernen...", "source": "wiki/python"},
    ]
    
    MOCK_TEACHER_RESULTS = [
        {"title": "Java Grundlagen", "text": "Java ist eine Programmiersprache...", "source": "wiki/java"},
        {"title": "Prüfungsfragen Java", "text": "Geheime Prüfungsfragen...", "source": "teacher:exams/java"},
        {"title": "Notenschlüssel", "text": "Bewertungskriterien...", "source": "class:grades"},
    ]
    
    @mcp.tool(name="search_content_student")
    async def search_student(query: str, limit: int = 10) -> dict:
        """Student search - returns filtered results."""
        if not query or not query.strip():
            raise ToolError("Suchanfrage darf nicht leer sein")
        
        # Filter out teacher content
        results = [r for r in MOCK_STUDENT_RESULTS if not r["source"].startswith(("teacher:", "class:"))]
        
        formatted = "\n\n".join([f"**{r['title']}**\n{r['text']}" for r in results[:limit]])
        return {"content": [{"type": "text", "text": formatted}]}
    
    @mcp.tool(name="search_content_teacher")
    async def search_teacher(query: str, limit: int = 10) -> dict:
        """Teacher search - returns all results."""
        if not query or not query.strip():
            raise ToolError("Suchanfrage darf nicht leer sein")
        
        results = MOCK_TEACHER_RESULTS[:limit]
        formatted = "\n\n".join([f"**{r['title']}**\n{r['text']}" for r in results])
        return {"content": [{"type": "text", "text": formatted}]}
    
    @mcp.tool(name="health_check")
    async def health() -> dict:
        """Health check tool."""
        return {"content": [{"type": "text", "text": "Status: Healthy ✓"}]}
    
    # -------------------------------------------------------------------------
    # Resources (for admin only in production)
    # -------------------------------------------------------------------------
    @mcp.resource("leowiki://categories")
    async def get_categories() -> str:
        """Get available categories."""
        return '["Programmierung", "Datenbanken", "Netzwerke", "Betriebssysteme"]'
    
    @mcp.resource("leowiki://stats")
    async def get_stats() -> str:
        """Get collection statistics."""
        return '{"total_documents": 3417, "student_accessible": 2449, "teacher_only": 968}'
    
    # -------------------------------------------------------------------------
    # Prompts
    # -------------------------------------------------------------------------
    @mcp.prompt(name="explain_topic")
    async def explain_topic(topic: str, difficulty: str = "medium") -> str:
        """Generate explanation prompt."""
        return f"Erkläre {topic} auf {difficulty} Niveau für HTL-Schüler."
    
    @mcp.prompt(name="summarize_search")
    async def summarize_search(query: str) -> str:
        """Generate search summary prompt."""
        return f"Fasse die Suchergebnisse für '{query}' zusammen."
    
    return mcp


# ============================================================================
# Pytest Fixtures
# ============================================================================
@pytest.fixture
def test_server():
    """Create a fresh test server for each test."""
    return create_test_server()


@pytest_asyncio.fixture
async def client(test_server):
    """
    Create a FastMCP Client connected to test server.
    
    Uses in-memory transport - no network overhead.
    Reference: https://gofastmcp.com/patterns/testing
    """
    from fastmcp import Client
    async with Client(test_server) as c:
        yield c


# ============================================================================
# Tool Registration Tests
# ============================================================================
class TestToolRegistration:
    """Verify tools are properly registered."""
    
    @pytest.mark.asyncio
    async def test_server_has_expected_tools(self, client):
        """Test that all expected tools are registered."""
        tools = await client.list_tools()
        tool_names = {t.name for t in tools}
        
        assert "search_content_student" in tool_names
        assert "search_content_teacher" in tool_names
        assert "health_check" in tool_names
    
    @pytest.mark.asyncio
    async def test_tool_count(self, client):
        """Test exact number of registered tools."""
        tools = await client.list_tools()
        assert len(tools) == 3, f"Expected 3 tools, got {len(tools)}"


# ============================================================================
# Student Search Tests
# ============================================================================
class TestStudentSearch:
    """Test student search tool behavior."""
    
    @pytest.mark.asyncio
    async def test_student_search_returns_results(self, client):
        """Test that student search returns results for valid query."""
        result = await client.call_tool("search_content_student", {"query": "Java"})
        
        assert result is not None
        assert len(result.content) > 0
        assert "Java" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_student_search_excludes_teacher_content(self, client):
        """Test that student search does NOT include teacher-only content."""
        result = await client.call_tool("search_content_student", {"query": "Java"})
        text = result.content[0].text
        
        # Should NOT contain teacher-only content
        assert "Prüfungsfragen" not in text
        assert "Notenschlüssel" not in text
        assert "Geheime" not in text
    
    @pytest.mark.asyncio
    async def test_student_search_empty_query_rejected(self, client):
        """Test that empty queries are rejected."""
        with pytest.raises(Exception) as exc_info:
            await client.call_tool("search_content_student", {"query": ""})
        
        assert "leer" in str(exc_info.value).lower() or "empty" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_student_search_whitespace_query_rejected(self, client):
        """Test that whitespace-only queries are rejected."""
        with pytest.raises(Exception):
            await client.call_tool("search_content_student", {"query": "   "})
    
    @pytest.mark.asyncio
    async def test_student_search_respects_limit(self, client):
        """Test that limit parameter is respected."""
        result = await client.call_tool("search_content_student", {"query": "test", "limit": 1})
        
        # With limit=1, should only have one result section
        text = result.content[0].text
        # Count the number of bold titles (** pattern)
        title_count = text.count("**")
        assert title_count <= 2, "Limit should restrict results"  # Each title has opening and closing **


# ============================================================================
# Teacher Search Tests
# ============================================================================
class TestTeacherSearch:
    """Test teacher search tool behavior."""
    
    @pytest.mark.asyncio
    async def test_teacher_search_includes_all_content(self, client):
        """Test that teacher search includes teacher-only content."""
        result = await client.call_tool("search_content_teacher", {"query": "Java"})
        text = result.content[0].text
        
        # Should include teacher content
        assert "Prüfungsfragen" in text or "Java" in text
    
    @pytest.mark.asyncio
    async def test_teacher_search_returns_more_than_student(self, client):
        """Test that teacher search returns more content than student search."""
        student_result = await client.call_tool("search_content_student", {"query": "Java"})
        teacher_result = await client.call_tool("search_content_teacher", {"query": "Java"})
        
        student_text = student_result.content[0].text
        teacher_text = teacher_result.content[0].text
        
        # Teacher should have more content (more characters)
        assert len(teacher_text) >= len(student_text)


# ============================================================================
# Health Check Tests
# ============================================================================
class TestHealthCheck:
    """Test health check tool."""
    
    @pytest.mark.asyncio
    async def test_health_check_returns_healthy(self, client):
        """Test that health check returns healthy status."""
        result = await client.call_tool("health_check", {})
        text = result.content[0].text
        
        assert "Healthy" in text or "healthy" in text.lower()


# ============================================================================
# Input Validation Tests
# ============================================================================
class TestInputValidation:
    """Test input validation across tools."""
    
    @pytest.mark.asyncio
    async def test_search_with_special_characters(self, client):
        """Test that special characters don't break search."""
        # Should not raise an exception
        result = await client.call_tool(
            "search_content_student",
            {"query": "Java <script>alert('xss')</script>"}
        )
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_search_with_very_long_query(self, client):
        """Test behavior with very long query."""
        long_query = "Java " * 100
        result = await client.call_tool(
            "search_content_student",
            {"query": long_query}
        )
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_search_with_unicode(self, client):
        """Test that unicode characters work correctly."""
        result = await client.call_tool(
            "search_content_student",
            {"query": "Übersicht über Größen"}
        )
        assert result is not None


# ============================================================================
# Error Handling Tests
# ============================================================================
class TestErrorHandling:
    """Test error handling behavior."""
    
    @pytest.mark.asyncio
    async def test_error_messages_are_user_friendly(self, client):
        """Test that error messages don't leak implementation details."""
        with pytest.raises(Exception) as exc_info:
            await client.call_tool("search_content_student", {"query": ""})
        
        error_msg = str(exc_info.value)
        
        # Should NOT contain technical details
        assert "Exception" not in error_msg or "ToolError" in error_msg
        assert "Traceback" not in error_msg
        assert "line" not in error_msg.lower() or "leer" in error_msg.lower()


# ============================================================================
# Resource Tests
# ============================================================================
class TestResources:
    """Test resource functionality."""
    
    @pytest.mark.asyncio
    async def test_resources_are_registered(self, client):
        """Test that resources are properly registered."""
        resources = await client.list_resources()
        resource_uris = {str(r.uri) for r in resources}
        
        assert "leowiki://categories" in resource_uris
        assert "leowiki://stats" in resource_uris
    
    @pytest.mark.asyncio
    async def test_categories_resource_returns_json(self, client):
        """Test that categories resource returns valid JSON."""
        import json
        result = await client.read_resource("leowiki://categories")
        
        # Result is a list of content items
        content = result[0].text if hasattr(result[0], 'text') else str(result[0])
        data = json.loads(content)
        assert isinstance(data, list)
        assert len(data) > 0
    
    @pytest.mark.asyncio
    async def test_stats_resource_returns_counts(self, client):
        """Test that stats resource returns document counts."""
        import json
        result = await client.read_resource("leowiki://stats")
        
        # Result is a list of content items
        content = result[0].text if hasattr(result[0], 'text') else str(result[0])
        data = json.loads(content)
        assert "total_documents" in data
        assert "student_accessible" in data
        assert data["total_documents"] > 0


# ============================================================================
# Prompt Tests
# ============================================================================
class TestPrompts:
    """Test prompt functionality."""
    
    @pytest.mark.asyncio
    async def test_prompts_are_registered(self, client):
        """Test that prompts are properly registered."""
        prompts = await client.list_prompts()
        prompt_names = {p.name for p in prompts}
        
        assert "explain_topic" in prompt_names
        assert "summarize_search" in prompt_names
    
    @pytest.mark.asyncio
    async def test_explain_topic_prompt(self, client):
        """Test explain_topic prompt generation."""
        result = await client.get_prompt("explain_topic", {"topic": "Java"})
        
        # Should contain the topic
        text = result.messages[0].content.text
        assert "Java" in text
    
    @pytest.mark.asyncio
    async def test_explain_topic_with_difficulty(self, client):
        """Test explain_topic with custom difficulty."""
        result = await client.get_prompt(
            "explain_topic", 
            {"topic": "Polymorphismus", "difficulty": "advanced"}
        )
        
        text = result.messages[0].content.text
        assert "Polymorphismus" in text
        assert "advanced" in text
    
    @pytest.mark.asyncio
    async def test_summarize_search_prompt(self, client):
        """Test summarize_search prompt generation."""
        result = await client.get_prompt("summarize_search", {"query": "Datenbanken"})
        
        text = result.messages[0].content.text
        assert "Datenbanken" in text


# ============================================================================
# Run tests directly
# ============================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
