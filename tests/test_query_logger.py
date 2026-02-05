"""
Deterministic Tests for Query Logger

Tests the query logging system for educational statistics.
Uses temporary directories to avoid affecting production data.

Reference: https://gofastmcp.com/patterns/testing
"""

import pytest
import json
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch


# ============================================================================
# Test Implementation (mirrors production)
# ============================================================================
class TestQueryLogger:
    """In-memory implementation for testing."""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_file = log_dir / "queries.jsonl"
        self._lock = threading.Lock()
    
    def log_query(
        self,
        query: str,
        response: str,
        user_role: str,
        tool_name: str,
        result_count: int,
        user_id_hash: str = None,
        request_id: str = None
    ) -> None:
        """Log a query to JSONL file."""
        from datetime import datetime
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response,
            "user_role": user_role,
            "tool_name": tool_name,
            "result_count": result_count,
            "user_id_hash": user_id_hash,
            "request_id": request_id
        }
        
        with self._lock:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    def get_statistics(self) -> dict:
        """Get statistics from log file."""
        if not self.log_file.exists():
            return {"total_queries": 0, "by_role": {}, "by_tool": {}}
        
        stats = {
            "total_queries": 0,
            "by_role": {},
            "by_tool": {}
        }
        
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    stats["total_queries"] += 1
                    
                    role = entry.get("user_role", "unknown")
                    stats["by_role"][role] = stats["by_role"].get(role, 0) + 1
                    
                    tool = entry.get("tool_name", "unknown")
                    stats["by_tool"][tool] = stats["by_tool"].get(tool, 0) + 1
        
        return stats


# ============================================================================
# Fixtures
# ============================================================================
@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for test logs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def logger(temp_log_dir):
    """Create a logger with temporary directory."""
    return TestQueryLogger(temp_log_dir)


# ============================================================================
# Basic Logging Tests
# ============================================================================
class TestBasicLogging:
    """Test basic logging functionality."""
    
    def test_log_creates_file(self, logger, temp_log_dir):
        """Test that logging creates the log file."""
        logger.log_query(
            query="test query",
            response="test response",
            user_role="student",
            tool_name="search_content_student",
            result_count=5
        )
        
        assert (temp_log_dir / "queries.jsonl").exists()
    
    def test_log_entry_format(self, logger, temp_log_dir):
        """Test that log entries have correct format."""
        logger.log_query(
            query="Java Grundlagen",
            response="Java ist eine Programmiersprache...",
            user_role="teacher",
            tool_name="search_content_teacher",
            result_count=10
        )
        
        with open(temp_log_dir / "queries.jsonl", "r") as f:
            entry = json.loads(f.readline())
        
        assert entry["query"] == "Java Grundlagen"
        assert entry["response"] == "Java ist eine Programmiersprache..."
        assert entry["user_role"] == "teacher"
        assert entry["tool_name"] == "search_content_teacher"
        assert entry["result_count"] == 10
        assert "timestamp" in entry
    
    def test_multiple_entries_appended(self, logger, temp_log_dir):
        """Test that multiple entries are appended."""
        for i in range(3):
            logger.log_query(
                query=f"query {i}",
                response=f"response {i}",
                user_role="student",
                tool_name="search_content_student",
                result_count=i
            )
        
        with open(temp_log_dir / "queries.jsonl", "r") as f:
            lines = f.readlines()
        
        assert len(lines) == 3
    
    def test_unicode_preserved(self, logger, temp_log_dir):
        """Test that unicode characters are preserved."""
        logger.log_query(
            query="Größe und Übersicht",
            response="Die größte Übersicht enthält äöü",
            user_role="student",
            tool_name="search_content_student",
            result_count=1
        )
        
        with open(temp_log_dir / "queries.jsonl", "r", encoding="utf-8") as f:
            entry = json.loads(f.readline())
        
        assert "Größe" in entry["query"]
        assert "äöü" in entry["response"]


# ============================================================================
# Statistics Tests
# ============================================================================
class TestStatistics:
    """Test statistics calculation."""
    
    def test_empty_statistics(self, logger):
        """Test statistics for empty log."""
        stats = logger.get_statistics()
        
        assert stats["total_queries"] == 0
        assert stats["by_role"] == {}
        assert stats["by_tool"] == {}
    
    def test_role_counting(self, logger):
        """Test that roles are counted correctly."""
        logger.log_query("q1", "r1", "student", "search_content_student", 1)
        logger.log_query("q2", "r2", "student", "search_content_student", 1)
        logger.log_query("q3", "r3", "teacher", "search_content_teacher", 1)
        
        stats = logger.get_statistics()
        
        assert stats["total_queries"] == 3
        assert stats["by_role"]["student"] == 2
        assert stats["by_role"]["teacher"] == 1
    
    def test_tool_counting(self, logger):
        """Test that tools are counted correctly."""
        logger.log_query("q1", "r1", "student", "search_content_student", 1)
        logger.log_query("q2", "r2", "teacher", "search_content_teacher", 1)
        logger.log_query("q3", "r3", "teacher", "search_content_teacher", 1)
        
        stats = logger.get_statistics()
        
        assert stats["by_tool"]["search_content_student"] == 1
        assert stats["by_tool"]["search_content_teacher"] == 2


# ============================================================================
# Thread Safety Tests
# ============================================================================
class TestThreadSafety:
    """Test thread safety of logging."""
    
    def test_concurrent_writes(self, logger, temp_log_dir):
        """Test that concurrent writes don't corrupt data."""
        import concurrent.futures
        
        def log_entry(i):
            logger.log_query(
                query=f"concurrent query {i}",
                response=f"response {i}",
                user_role="student",
                tool_name="search_content_student",
                result_count=i
            )
        
        # Write 100 entries concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(log_entry, i) for i in range(100)]
            concurrent.futures.wait(futures)
        
        # Verify all entries were written
        with open(temp_log_dir / "queries.jsonl", "r") as f:
            lines = f.readlines()
        
        assert len(lines) == 100
        
        # Verify all entries are valid JSON
        for line in lines:
            entry = json.loads(line)  # Should not raise
            assert "query" in entry


# ============================================================================
# Edge Cases
# ============================================================================
class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_query(self, logger, temp_log_dir):
        """Test logging empty query."""
        logger.log_query(
            query="",
            response="No results",
            user_role="student",
            tool_name="search_content_student",
            result_count=0
        )
        
        with open(temp_log_dir / "queries.jsonl", "r") as f:
            entry = json.loads(f.readline())
        
        assert entry["query"] == ""
    
    def test_very_long_response(self, logger, temp_log_dir):
        """Test logging very long response."""
        long_response = "x" * 10000
        
        logger.log_query(
            query="test",
            response=long_response,
            user_role="teacher",
            tool_name="search_content_teacher",
            result_count=100
        )
        
        with open(temp_log_dir / "queries.jsonl", "r") as f:
            entry = json.loads(f.readline())
        
        assert len(entry["response"]) == 10000
    
    def test_special_characters_in_query(self, logger, temp_log_dir):
        """Test logging query with special characters."""
        special_query = 'Test "quotes" and \'apostrophes\' and \n newlines'
        
        logger.log_query(
            query=special_query,
            response="response",
            user_role="student",
            tool_name="search_content_student",
            result_count=1
        )
        
        with open(temp_log_dir / "queries.jsonl", "r") as f:
            entry = json.loads(f.readline())
        
        assert entry["query"] == special_query


# ============================================================================
# Run tests directly
# ============================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
