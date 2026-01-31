"""
FastMCP Custom Middleware for LeoWiki MCP Server

This module implements custom middleware components for the FastMCP framework:
- Request logging with correlation IDs
- User context extraction from JWT tokens
- RBAC enforcement at the tool level

These middleware components complement the existing Scalekit OAuth middleware
and provide additional functionality for request tracking and authorization.
"""

import logging
import time
import uuid
import jwt
from typing import Any

from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.dependencies import get_http_headers
from fastmcp.exceptions import ToolError

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(Middleware):
    """
    Log all MCP requests with timing and correlation IDs.
    
    This middleware:
    - Generates unique request IDs for correlation
    - Logs request start and completion
    - Measures and logs request duration
    - Tracks errors with full context
    """
    
    async def on_request(self, context: MiddlewareContext, call_next):
        """
        Handle incoming requests with logging.
        
        Args:
            context: Middleware context with request information
            call_next: Next middleware/handler in the chain
            
        Returns:
            Response from downstream handlers
        """
        # Generate correlation ID
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # Store request ID in FastMCP context for access in tools
        if context.fastmcp_context:
            context.fastmcp_context.set_state("request_id", request_id)
        
        # Log request start
        logger.info(f"[{request_id}] → {context.method}")
        
        try:
            # Call next handler
            result = await call_next(context)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful completion
            logger.info(f"[{request_id}] ✓ {context.method} completed in {duration_ms:.1f}ms")
            
            return result
            
        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            logger.error(
                f"[{request_id}] ✗ {context.method} failed after {duration_ms:.1f}ms: {e}",
                exc_info=True
            )
            raise


class UserContextMiddleware(Middleware):
    """
    Extract user information from JWT tokens and populate session state.
    
    This middleware:
    - Extracts JWT claims from Authorization header
    - Populates FastMCP context with user information
    - Provides default values for unauthenticated requests
    
    Note: Token validation is already done by ScalekitAuthMiddleware.
    This middleware only extracts claims for use in tools.
    """
    
    async def on_request(self, context: MiddlewareContext, call_next):
        """
        Extract user context from JWT and populate session state.
        
        Args:
            context: Middleware context
            call_next: Next middleware/handler
            
        Returns:
            Response from downstream handlers
        """
        # Get HTTP headers
        headers = get_http_headers() or {}
        auth_header = headers.get("authorization", "")
        
        # Default values for unauthenticated requests
        user_id = None
        user_email = None
        user_role = "student"  # Default role
        user_scopes = set()
        
        # Extract JWT claims if Bearer token present
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                # Token is already validated by Scalekit middleware
                # We just extract claims (no signature verification needed)
                claims = jwt.decode(token, options={"verify_signature": False})
                
                # Extract standard claims
                user_id = claims.get("sub")
                user_email = claims.get("email")
                
                # Extract role from custom claim or default to student
                user_role = claims.get("role", "student")
                
                # Extract scopes if present
                scope_str = claims.get("scope", "")
                if scope_str:
                    user_scopes = set(scope_str.split())
                
                logger.debug(
                    f"User context extracted: id={user_id}, email={user_email}, "
                    f"role={user_role}, scopes={user_scopes}"
                )
                
            except Exception as e:
                # If JWT parsing fails, use defaults
                logger.warning(f"Failed to extract JWT claims: {e}")
                logger.debug("Using default user context (student role)")
        
        # Populate FastMCP context state
        if context.fastmcp_context:
            context.fastmcp_context.set_state("user_id", user_id)
            context.fastmcp_context.set_state("user_email", user_email)
            context.fastmcp_context.set_state("user_role", user_role)
            context.fastmcp_context.set_state("user_scopes", user_scopes)
        
        # Proceed to next handler
        return await call_next(context)


class RBACEnforcementMiddleware(Middleware):
    """
    Enforce role-based access control at the tool level.
    
    This middleware:
    1. FILTERS the tool list (on_list_tools) - users only see tools they can use
    2. ENFORCES access control (on_call_tool) - prevents unauthorized execution
    
    Tool permissions are defined in TOOL_PERMISSIONS mapping.
    """
    
    # Define which tools require which roles
    # Tools not listed here are accessible to all authenticated users
    TOOL_PERMISSIONS = {
        # Admin-only tools
        "get_collection_stats": {"admin", "teacher"},
        "reindex_document": {"admin"},
        "delete_content": {"admin"},
        "manage_users": {"admin"},
        "bulk_operation": {"admin"},
        
        # Teacher+ tools
        "admin_health_check": {"admin", "teacher"},
        "content_get_document": {"teacher", "admin"},  # If we add detailed document access
        
        # Student sees only student tools, teacher sees teacher tools
        "search_content_teacher": {"admin", "teacher"},
    }
    
    async def on_list_tools(self, context: MiddlewareContext, call_next):
        """
        Filter tool list based on user role.
        
        Students only see student-accessible tools.
        Teachers see teacher and student tools.
        Admins see all tools.
        
        Args:
            context: Middleware context
            call_next: Next middleware/handler
            
        Returns:
            Filtered list of tools based on user role
        """
        # Get full tool list
        all_tools = await call_next(context)
        
        # Get user role from context
        user_role = "student"  # Default
        if context.fastmcp_context:
            user_role = context.fastmcp_context.get_state("user_role") or "student"
        
        # Filter tools based on role
        filtered_tools = []
        for tool in all_tools:
            tool_name = tool.name
            required_roles = self.TOOL_PERMISSIONS.get(tool_name, set())
            
            # If tool has no restrictions, show to all
            if not required_roles:
                filtered_tools.append(tool)
                continue
            
            # If user has required role, show tool
            if user_role in required_roles:
                filtered_tools.append(tool)
        
        logger.debug(
            f"Tool list filtered for role '{user_role}': "
            f"{len(filtered_tools)}/{len(all_tools)} tools visible"
        )
        
        return filtered_tools
    
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """
        Enforce RBAC before tool execution.
        
        Args:
            context: Middleware context with tool name
            call_next: Next middleware/handler
            
        Returns:
            Tool execution result
            
        Raises:
            ToolError: If user doesn't have required role
        """
        tool_name = context.message.name
        required_roles = self.TOOL_PERMISSIONS.get(tool_name, set())
        
        # If tool has role requirements, check them
        if required_roles:
            user_role = context.fastmcp_context.get_state("user_role") or "guest"
            
            if user_role not in required_roles:
                logger.warning(
                    f"Access denied: user with role '{user_role}' tried to access "
                    f"tool '{tool_name}' (requires: {', '.join(required_roles)})"
                )
                raise ToolError(
                    f"Access denied. Tool '{tool_name}' requires one of these roles: "
                    f"{', '.join(sorted(required_roles))}"
                )
            
            logger.debug(f"RBAC check passed: {user_role} can access {tool_name}")
        
        # User has required role, proceed
        return await call_next(context)


class AuditLoggingMiddleware(Middleware):
    """
    Audit logging middleware for compliance and security monitoring.
    
    Logs all tool invocations with:
    - Who (user ID, role)
    - What (tool name, parameters)
    - When (timestamp)
    - Result (success/failure)
    
    This is essential for DSGVO compliance and security audits.
    """
    
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """
        Log tool invocation for audit trail.
        
        Args:
            context: Middleware context
            call_next: Next handler
            
        Returns:
            Tool execution result
        """
        tool_name = context.message.name
        
        # Extract user information
        user_id = context.fastmcp_context.get_state("user_id") or "anonymous"
        user_role = context.fastmcp_context.get_state("user_role") or "unknown"
        request_id = context.fastmcp_context.get_state("request_id") or "unknown"
        
        # Hash user ID for privacy (DSGVO pseudonymization)
        user_id_hash = hash(user_id) if user_id != "anonymous" else "anonymous"
        
        # Get tool arguments (without sensitive data)
        # Note: We don't log the full arguments to avoid logging sensitive queries
        
        try:
            # Execute tool
            result = await call_next(context)
            
            # Log successful invocation
            logger.info(
                f"[AUDIT] Tool invocation successful - "
                f"request_id={request_id}, tool={tool_name}, "
                f"user={user_id_hash}, role={user_role}"
            )
            
            return result
            
        except Exception as e:
            # Log failed invocation
            logger.warning(
                f"[AUDIT] Tool invocation failed - "
                f"request_id={request_id}, tool={tool_name}, "
                f"user={user_id_hash}, role={user_role}, "
                f"error={type(e).__name__}"
            )
            raise
