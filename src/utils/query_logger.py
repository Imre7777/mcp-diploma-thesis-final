"""
Query Logger for Educational Statistics

Persists user queries and responses for statistical analysis.
This is safe for the educational context as no sensitive personal data
(grades, addresses, etc.) is involved - only learning-related questions.

Data is stored in JSONL format for easy analysis with Python/Pandas.
"""

import json
import logging
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Thread-safe file writing
_write_lock = threading.Lock()

# Default log directory
DEFAULT_LOG_DIR = Path(__file__).parent.parent.parent / "data" / "statistics"


class QueryLogger:
    """
    Persistent query logger for educational statistics.
    
    Logs queries and responses to a JSONL file for later analysis.
    Thread-safe for concurrent access.
    """
    
    def __init__(self, log_dir: Optional[Path] = None):
        """
        Initialize the query logger.
        
        Args:
            log_dir: Directory for log files (default: data/statistics/)
        """
        self.log_dir = log_dir or DEFAULT_LOG_DIR
        self.log_file = self.log_dir / "queries.jsonl"
        
        # Ensure directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"QueryLogger initialized: {self.log_file}")
    
    def log_query(
        self,
        query: str,
        response: str,
        user_role: str,
        tool_name: str,
        result_count: int,
        user_id_hash: Optional[str] = None,
        request_id: Optional[str] = None,
        duration_ms: Optional[float] = None
    ) -> None:
        """
        Log a query and its response for statistics.
        
        Args:
            query: The user's search query
            response: The formatted response (truncated for storage)
            user_role: User's role (student, teacher, admin)
            tool_name: Which tool was used
            result_count: Number of results returned
            user_id_hash: Hashed user ID (for session tracking, not identification)
            request_id: Correlation ID for debugging
            duration_ms: Query processing time in milliseconds
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response_preview": response[:500] if response else "",  # First 500 chars
            "response_length": len(response) if response else 0,
            "user_role": user_role,
            "tool_name": tool_name,
            "result_count": result_count,
            "user_id_hash": user_id_hash,
            "request_id": request_id,
            "duration_ms": duration_ms
        }
        
        self._write_entry(entry)
    
    def _write_entry(self, entry: dict) -> None:
        """
        Thread-safe write of a log entry.
        
        Args:
            entry: Dictionary to write as JSON line
        """
        try:
            with _write_lock:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            # Don't fail the request if logging fails
            logger.error(f"Failed to write query log: {e}")
    
    def get_statistics(self) -> dict:
        """
        Get basic statistics from the query log.
        
        Returns:
            Dictionary with query statistics
        """
        if not self.log_file.exists():
            return {"total_queries": 0, "message": "No queries logged yet"}
        
        try:
            total = 0
            by_role = {"student": 0, "teacher": 0, "admin": 0}
            by_tool = {}
            
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        total += 1
                        
                        role = entry.get("user_role", "unknown")
                        if role in by_role:
                            by_role[role] += 1
                        
                        tool = entry.get("tool_name", "unknown")
                        by_tool[tool] = by_tool.get(tool, 0) + 1
            
            return {
                "total_queries": total,
                "by_role": by_role,
                "by_tool": by_tool,
                "log_file": str(self.log_file)
            }
        except Exception as e:
            logger.error(f"Failed to read query statistics: {e}")
            return {"error": str(e)}


# Global singleton instance
_query_logger: Optional[QueryLogger] = None
_logger_lock = threading.Lock()


def get_query_logger() -> QueryLogger:
    """
    Get the global QueryLogger instance (thread-safe singleton).
    
    Returns:
        QueryLogger instance
    """
    global _query_logger
    
    if _query_logger is None:
        with _logger_lock:
            if _query_logger is None:
                _query_logger = QueryLogger()
    
    return _query_logger
