"""
Deterministic RBAC Tests for LeoWiki MCP Server

Tests role-based access control without external dependencies.
Verifies that tool visibility and content access is properly restricted.

Reference: https://gofastmcp.com/patterns/testing
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Set


# ============================================================================
# RBAC Rules (mirrored from production for testing)
# ============================================================================
TOOL_PERMISSIONS = {
    # Student tools - students, teachers, and admins
    "search_content_student": {"student", "teacher", "admin"},
    
    # Teacher tools - only teachers and admins can use
    "search_content_teacher": {"teacher", "admin"},
    
    # Admin-only tools
    "get_collection_stats": {"admin"},
    "get_query_statistics": {"admin"},
    
    # Public tools - all roles
    "health_check": {"student", "teacher", "admin"},
}

RESOURCE_PERMISSIONS = {
    "leowiki://categories": {"admin"},
    "leowiki://stats": {"admin"},
    "leowiki://system-prompt": {"admin"},
}


def get_allowed_tools(role: str) -> Set[str]:
    """Get set of tools allowed for a given role."""
    return {
        tool for tool, roles in TOOL_PERMISSIONS.items()
        if role in roles
    }


def get_allowed_resources(role: str) -> Set[str]:
    """Get set of resources allowed for a given role."""
    return {
        resource for resource, roles in RESOURCE_PERMISSIONS.items()
        if role in roles
    }


# ============================================================================
# Role Permission Tests
# ============================================================================
class TestStudentPermissions:
    """Test what students can and cannot access."""
    
    def test_student_allowed_tools(self):
        """Test tools accessible to students."""
        allowed = get_allowed_tools("student")
        
        assert "search_content_student" in allowed
        assert "health_check" in allowed
        
        # Total should be exactly 2
        assert len(allowed) == 2
    
    def test_student_blocked_tools(self):
        """Test tools that students CANNOT access."""
        allowed = get_allowed_tools("student")
        
        assert "search_content_teacher" not in allowed
        assert "get_collection_stats" not in allowed
        assert "get_query_statistics" not in allowed
    
    def test_student_no_resource_access(self):
        """Test that students have no direct resource access."""
        allowed = get_allowed_resources("student")
        
        assert len(allowed) == 0


class TestTeacherPermissions:
    """Test what teachers can access."""
    
    def test_teacher_allowed_tools(self):
        """Test tools accessible to teachers."""
        allowed = get_allowed_tools("teacher")
        
        assert "search_content_student" in allowed  # Can compare
        assert "search_content_teacher" in allowed
        assert "health_check" in allowed
        
        # Total should be 3
        assert len(allowed) == 3
    
    def test_teacher_blocked_from_admin_tools(self):
        """Test that teachers cannot access admin-only tools."""
        allowed = get_allowed_tools("teacher")
        
        assert "get_collection_stats" not in allowed
        assert "get_query_statistics" not in allowed
    
    def test_teacher_no_resource_access(self):
        """Test that teachers have no direct resource access."""
        allowed = get_allowed_resources("teacher")
        
        assert len(allowed) == 0


class TestAdminPermissions:
    """Test what admins can access."""
    
    def test_admin_has_all_tools(self):
        """Test that admins can access all tools."""
        allowed = get_allowed_tools("admin")
        
        # Admin should have access to everything
        for tool in TOOL_PERMISSIONS.keys():
            assert tool in allowed, f"Admin should have access to {tool}"
    
    def test_admin_has_all_resources(self):
        """Test that admins can access all resources."""
        allowed = get_allowed_resources("admin")
        
        for resource in RESOURCE_PERMISSIONS.keys():
            assert resource in allowed, f"Admin should have access to {resource}"


# ============================================================================
# Security Isolation Tests
# ============================================================================
class TestSecurityIsolation:
    """Test that role isolation is properly enforced."""
    
    def test_student_cannot_escalate_to_teacher(self):
        """
        Test that student role cannot access teacher tools.
        
        Critical security test - this must NEVER fail in production.
        """
        student_tools = get_allowed_tools("student")
        teacher_tools = get_allowed_tools("teacher")
        
        # Teacher has strictly more access
        assert student_tools < teacher_tools
        
        # Specific critical check
        assert "search_content_teacher" not in student_tools
    
    def test_teacher_cannot_escalate_to_admin(self):
        """
        Test that teacher role cannot access admin tools.
        """
        teacher_tools = get_allowed_tools("teacher")
        admin_tools = get_allowed_tools("admin")
        
        # Admin has strictly more access
        assert teacher_tools < admin_tools
        
        # Specific critical check
        assert "get_collection_stats" not in teacher_tools
    
    def test_unknown_role_has_no_access(self):
        """
        Test that unknown roles have no tool access.
        """
        allowed = get_allowed_tools("hacker")
        
        assert len(allowed) == 0
    
    def test_empty_role_has_no_access(self):
        """
        Test that empty role string has no access.
        """
        allowed = get_allowed_tools("")
        
        assert len(allowed) == 0


# ============================================================================
# Permission Matrix Tests
# ============================================================================
class TestPermissionMatrix:
    """Test the complete permission matrix."""
    
    @pytest.mark.parametrize("role,tool,expected", [
        # Students
        ("student", "search_content_student", True),
        ("student", "search_content_teacher", False),
        ("student", "get_collection_stats", False),
        ("student", "health_check", True),
        
        # Teachers
        ("teacher", "search_content_student", True),
        ("teacher", "search_content_teacher", True),
        ("teacher", "get_collection_stats", False),
        ("teacher", "health_check", True),
        
        # Admins
        ("admin", "search_content_student", True),
        ("admin", "search_content_teacher", True),
        ("admin", "get_collection_stats", True),
        ("admin", "health_check", True),
    ])
    def test_permission_check(self, role, tool, expected):
        """
        Parametrized test for permission matrix.
        
        Reference: https://gofastmcp.com/patterns/testing#using-fixtures
        """
        allowed = get_allowed_tools(role)
        
        if expected:
            assert tool in allowed, f"{role} should have access to {tool}"
        else:
            assert tool not in allowed, f"{role} should NOT have access to {tool}"


# ============================================================================
# RBAC Enforcement Middleware Tests
# ============================================================================
class TestRBACEnforcementLogic:
    """Test RBAC enforcement logic in isolation."""
    
    def test_filter_tools_for_student(self):
        """Test that tool filtering works for students."""
        all_tools = list(TOOL_PERMISSIONS.keys())
        
        # Simulate middleware filtering
        visible_tools = [t for t in all_tools if "student" in TOOL_PERMISSIONS.get(t, set())]
        
        assert len(visible_tools) == 2
        assert "search_content_student" in visible_tools
        assert "health_check" in visible_tools
    
    def test_filter_tools_for_teacher(self):
        """Test that tool filtering works for teachers."""
        all_tools = list(TOOL_PERMISSIONS.keys())
        
        # Simulate middleware filtering
        visible_tools = [t for t in all_tools if "teacher" in TOOL_PERMISSIONS.get(t, set())]
        
        assert len(visible_tools) == 3
    
    def test_tool_call_blocked_for_unauthorized_role(self):
        """
        Test that unauthorized tool calls are blocked.
        
        Simulates what RBACEnforcementMiddleware should do.
        """
        def enforce_rbac(tool_name: str, user_role: str) -> bool:
            """Simulated RBAC enforcement."""
            allowed_roles = TOOL_PERMISSIONS.get(tool_name, set())
            return user_role in allowed_roles
        
        # Student trying to use teacher tool
        assert not enforce_rbac("search_content_teacher", "student")
        
        # Teacher trying to use admin tool
        assert not enforce_rbac("get_collection_stats", "teacher")
        
        # Admin can use everything
        assert enforce_rbac("search_content_teacher", "admin")
        assert enforce_rbac("get_collection_stats", "admin")


# ============================================================================
# Content Access Level Tests
# ============================================================================
class TestContentAccessLevels:
    """Test content access level filtering."""
    
    MOCK_DOCUMENTS = [
        {"id": 1, "title": "Public Info", "access_level": "student"},
        {"id": 2, "title": "Teacher Notes", "access_level": "teacher"},
        {"id": 3, "title": "Admin Config", "access_level": "admin"},
    ]
    
    def test_student_sees_only_student_content(self):
        """Test that students only see student-level content."""
        allowed_levels = {"student"}
        
        visible = [d for d in self.MOCK_DOCUMENTS if d["access_level"] in allowed_levels]
        
        assert len(visible) == 1
        assert visible[0]["title"] == "Public Info"
    
    def test_teacher_sees_student_and_teacher_content(self):
        """Test that teachers see student + teacher content."""
        allowed_levels = {"student", "teacher"}
        
        visible = [d for d in self.MOCK_DOCUMENTS if d["access_level"] in allowed_levels]
        
        assert len(visible) == 2
        titles = {d["title"] for d in visible}
        assert "Public Info" in titles
        assert "Teacher Notes" in titles
    
    def test_admin_sees_all_content(self):
        """Test that admins see all content levels."""
        allowed_levels = {"student", "teacher", "admin"}
        
        visible = [d for d in self.MOCK_DOCUMENTS if d["access_level"] in allowed_levels]
        
        assert len(visible) == 3


# ============================================================================
# Run tests directly
# ============================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
