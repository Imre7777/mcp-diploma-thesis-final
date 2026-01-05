"""
Scalekit OAuth 2.1 Client

This module implements JWT token validation for Scalekit MCP servers.
Based on Scalekit's Python examples and OAuth 2.0 standards.
"""

import logging
from typing import Optional, Dict, Any
import httpx
import jwt
from jwt import PyJWKClient
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ScalekitClient:
    """
    Client for validating Scalekit JWT tokens.
    
    This client:
    - Fetches JWKS (JSON Web Key Set) from Scalekit
    - Validates JWT tokens using RS256 algorithm
    - Extracts user claims and roles from tokens
    """
    
    def __init__(
        self,
        env_url: str,
        client_id: str,
        client_secret: str,
    ):
        """
        Initialize Scalekit client.
        
        Args:
            env_url: Scalekit environment URL (e.g., https://mcpeduauth.scalekit.dev)
            client_id: Scalekit client ID
            client_secret: Scalekit client secret
        """
        self.env_url = env_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        
        # JWKS URL for fetching public keys
        self.jwks_url = f"{self.env_url}/.well-known/jwks.json"
        
        # Initialize JWKS client for fetching signing keys
        self.jwks_client = PyJWKClient(self.jwks_url)
        
        logger.info(f"Scalekit client initialized: env={self.env_url}")
    
    def validate_access_token(
        self,
        token: str,
        audience: str,
    ) -> bool:
        """
        Validate access token (simple boolean check).
        
        Args:
            token: JWT token string
            audience: Expected audience (your MCP server URL)
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            self.validate_token_and_get_claims(token, audience)
            return True
        except Exception as ex:
            logger.warning(f"Token validation failed: {ex}")
            return False
    
    def validate_token_and_get_claims(
        self,
        token: str,
        audience: str,
    ) -> Dict[str, Any]:
        """
        Validate token and return claims.
        
        This method:
        1. Fetches the signing key from JWKS
        2. Verifies the token signature
        3. Validates expiration, issuer, and audience
        4. Returns the decoded claims
        
        Args:
            token: JWT token string
            audience: Expected audience (your MCP server URL)
            
        Returns:
            Dict of token claims
            
        Raises:
            jwt.InvalidTokenError: If token is invalid
        """
        try:
            # Get signing key from JWKS
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            
            # Decode and validate token
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=audience,
                issuer=self.env_url,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "verify_iss": True,
                },
            )
            
            logger.debug(f"Token validated successfully: sub={claims.get('sub')}")
            return claims
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise
        except jwt.InvalidAudienceError:
            logger.warning(f"Invalid audience. Expected: {audience}")
            raise
        except jwt.InvalidIssuerError:
            logger.warning(f"Invalid issuer. Expected: {self.env_url}")
            raise
        except jwt.InvalidTokenError as ex:
            logger.warning(f"Invalid token: {ex}")
            raise
        except Exception as ex:
            logger.error(f"Unexpected error validating token: {ex}", exc_info=True)
            raise jwt.InvalidTokenError(f"Token validation failed: {ex}")
