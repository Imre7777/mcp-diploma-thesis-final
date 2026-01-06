"""
OAuth 2.1 Authorization Code Flow for Scalekit

This module implements the OAuth login/callback endpoints for user authentication.
"""

import logging
import secrets
from typing import Optional, Dict, Any
from urllib.parse import urlencode
import httpx
from fastapi import APIRouter, Request, HTTPException, Response
from fastapi.responses import RedirectResponse, JSONResponse

logger = logging.getLogger(__name__)


def create_oauth_router(
    scalekit_env_url: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    frontend_callback_url: Optional[str] = None,
) -> APIRouter:
    """
    Create OAuth router with login/callback/logout endpoints.
    
    Args:
        scalekit_env_url: Scalekit environment URL
        client_id: Scalekit client ID
        client_secret: Scalekit client secret
        redirect_uri: OAuth redirect URI (this server's callback endpoint)
        frontend_callback_url: Optional frontend URL to redirect to after auth
        
    Returns:
        FastAPI router with OAuth endpoints
    """
    router = APIRouter(tags=["authentication"])
    
    # In-memory session store (for development)
    # In production, use Redis or encrypted cookies
    sessions: Dict[str, Dict[str, Any]] = {}
    
    @router.get("/auth/login")
    async def login(
        request: Request,
        organization_id: Optional[str] = None,
        connection_id: Optional[str] = None,
    ):
        """
        Initiate OAuth login flow.
        
        This endpoint redirects the user to Scalekit's authorization page.
        
        Query Parameters:
            organization_id: Optional organization ID for SSO
            connection_id: Optional connection ID for specific SSO provider
            
        Returns:
            Redirect to Scalekit authorization page
        """
        # Generate state parameter for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Generate PKCE code verifier and challenge (optional but recommended)
        code_verifier = secrets.token_urlsafe(32)
        
        # Store state and code_verifier in session
        sessions[state] = {
            "code_verifier": code_verifier,
            "created_at": "now",  # In production, use actual timestamp
        }
        
        # Build authorization URL
        auth_params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "openid profile email",  # Standard OIDC scopes
        }
        
        # Add optional parameters
        if organization_id:
            auth_params["organization_id"] = organization_id
        if connection_id:
            auth_params["connection_id"] = connection_id
        
        # Scalekit authorization endpoint
        auth_url = f"{scalekit_env_url}/authorize?{urlencode(auth_params)}"
        
        logger.info(f"Redirecting to Scalekit login: state={state[:8]}...")
        
        return RedirectResponse(url=auth_url, status_code=302)
    
    @router.get("/auth/callback")
    async def callback(
        request: Request,
        code: Optional[str] = None,
        state: Optional[str] = None,
        error: Optional[str] = None,
        error_description: Optional[str] = None,
    ):
        """
        OAuth callback endpoint.
        
        Scalekit redirects here after user authentication.
        
        Query Parameters:
            code: Authorization code (if successful)
            state: CSRF protection state
            error: Error code (if failed)
            error_description: Error description (if failed)
            
        Returns:
            Access token or error response
        """
        # Check for errors from Scalekit
        if error:
            logger.error(f"OAuth error: {error} - {error_description}")
            raise HTTPException(
                status_code=400,
                detail=f"Authentication failed: {error_description or error}"
            )
        
        # Validate required parameters
        if not code or not state:
            raise HTTPException(
                status_code=400,
                detail="Missing required parameters: code and state"
            )
        
        # Validate state (CSRF protection)
        session_data = sessions.get(state)
        if not session_data:
            logger.warning(f"Invalid state parameter: {state[:8]}...")
            raise HTTPException(
                status_code=400,
                detail="Invalid state parameter. Possible CSRF attack."
            )
        
        # Exchange authorization code for access token
        token_url = f"{scalekit_env_url}/token"
        token_params = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_url,
                    data=token_params,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=10.0,
                )
                
                if response.status_code != 200:
                    logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=502,
                        detail=f"Failed to exchange authorization code: {response.text}"
                    )
                
                token_data = response.json()
                
                # Clean up session
                del sessions[state]
                
                logger.info("OAuth authentication successful!")
                
                # Return tokens
                # In production, you might:
                # 1. Create a session cookie
                # 2. Redirect to frontend with token
                # 3. Store token in secure HTTP-only cookie
                
                if frontend_callback_url:
                    # Redirect to frontend with token as URL parameter
                    # WARNING: This exposes token in URL! Use POST or secure cookie in production
                    redirect_url = f"{frontend_callback_url}?access_token={token_data['access_token']}"
                    return RedirectResponse(url=redirect_url, status_code=302)
                else:
                    # Return token as JSON (for API clients)
                    return JSONResponse({
                        "access_token": token_data.get("access_token"),
                        "token_type": token_data.get("token_type", "Bearer"),
                        "expires_in": token_data.get("expires_in"),
                        "refresh_token": token_data.get("refresh_token"),
                        "id_token": token_data.get("id_token"),
                        "scope": token_data.get("scope"),
                    })
        
        except httpx.RequestError as e:
            logger.error(f"HTTP error during token exchange: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"Failed to connect to Scalekit: {str(e)}"
            )
    
    @router.get("/auth/logout")
    async def logout(
        request: Request,
        id_token: Optional[str] = None,
    ):
        """
        Logout endpoint.
        
        Redirects to Scalekit logout to end SSO session.
        
        Query Parameters:
            id_token: Optional ID token for logout
            
        Returns:
            Redirect to Scalekit logout
        """
        # Scalekit logout endpoint
        logout_params = {}
        if id_token:
            logout_params["id_token_hint"] = id_token
        
        logout_url = f"{scalekit_env_url}/logout"
        if logout_params:
            logout_url += f"?{urlencode(logout_params)}"
        
        logger.info("User logged out")
        
        return RedirectResponse(url=logout_url, status_code=302)
    
    @router.get("/auth/user")
    async def get_user(request: Request):
        """
        Get current authenticated user info.
        
        This endpoint requires authentication (Bearer token).
        Returns user information from the validated JWT token.
        
        Returns:
            User information dict
        """
        # Check if user is authenticated (set by middleware)
        if not hasattr(request.state, "user"):
            raise HTTPException(
                status_code=401,
                detail="Not authenticated. Please log in."
            )
        
        user = request.state.user
        
        return {
            "user_id": user.get("sub"),
            "email": user.get("email"),
            "name": user.get("name"),
            "role": user.get("role"),
            "org_id": user.get("org_id"),
            "authenticated": True,
        }
    
    return router
