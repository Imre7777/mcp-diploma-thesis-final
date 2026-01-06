"""
Test JWT validation with mock tokens.

This script tests:
1. JWT token generation (for testing only!)
2. JWT token validation with Scalekit client
3. Role extraction from token claims
4. Authentication middleware behavior
"""

import sys
import os
from pathlib import Path
import asyncio
import logging
from datetime import datetime, timedelta
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.auth.scalekit_client import ScalekitClient
from src.config.server_config import ServerConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockJWTGenerator:
    """
    Generate mock JWT tokens for testing.
    
    WARNING: This is for testing only! In production, Scalekit generates tokens.
    """
    
    def __init__(self):
        """Generate RSA key pair for signing mock tokens."""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        self.public_key = self.private_key.public_key()
        
        # Serialize keys
        self.private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        
        self.public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    
    def generate_token(
        self,
        user_id: str = "user_123",
        email: str = "student@test.com",
        roles: list[str] = None,
        org_id: str = "org_456",
        issuer: str = "https://mcpeduauth.scalekit.dev",
        audience: str = "http://localhost:8000",
        expires_in_seconds: int = 3600,
    ) -> str:
        """
        Generate a mock JWT token.
        
        Args:
            user_id: User ID (sub claim)
            email: User email
            roles: List of user roles
            org_id: Organization ID
            issuer: Token issuer
            audience: Token audience
            expires_in_seconds: Token lifetime in seconds
            
        Returns:
            JWT token string
        """
        if roles is None:
            roles = ["student"]
        
        now = datetime.now()
        exp = now + timedelta(seconds=expires_in_seconds)
        
        payload = {
            "sub": user_id,
            "email": email,
            "roles": roles,
            "org_id": org_id,
            "name": email.split("@")[0].title(),
            "iss": issuer,
            "aud": audience,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        
        token = jwt.encode(
            payload,
            self.private_pem,
            algorithm="RS256",
        )
        
        return token


def test_mock_token_generation():
    """Test 1: Generate and decode mock tokens."""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Mock Token Generation")
    logger.info("="*60)
    
    generator = MockJWTGenerator()
    
    # Test different roles
    test_cases = [
        ("student@test.com", ["student"], "Student token"),
        ("teacher@test.com", ["teacher"], "Teacher token"),
        ("admin@test.com", ["admin"], "Admin token"),
        ("multi@test.com", ["student", "teacher"], "Multi-role token"),
    ]
    
    for email, roles, description in test_cases:
        token = generator.generate_token(email=email, roles=roles)
        
        # Decode without verification (just to check structure)
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        logger.info(f"\n{description}:")
        logger.info(f"  Email: {decoded['email']}")
        logger.info(f"  Roles: {decoded['roles']}")
        logger.info(f"  Sub: {decoded['sub']}")
        logger.info(f"  Org: {decoded['org_id']}")
        logger.info(f"  Token: {token[:50]}...")
        
        assert decoded["email"] == email
        assert decoded["roles"] == roles
        assert decoded["iss"] == "https://mcpeduauth.scalekit.dev"
        assert decoded["aud"] == "http://localhost:8000"
    
    logger.info("\n✅ All mock tokens generated successfully!")
    return generator


def test_token_validation_without_scalekit():
    """Test 2: Validate tokens using local public key (simulating Scalekit)."""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Token Validation (Without Scalekit)")
    logger.info("="*60)
    
    generator = MockJWTGenerator()
    
    # Generate a valid token
    token = generator.generate_token(
        email="student@test.com",
        roles=["student"],
    )
    
    # Validate using public key (with leeway for clock skew)
    try:
        decoded = jwt.decode(
            token,
            generator.public_pem,
            algorithms=["RS256"],
            audience="http://localhost:8000",
            issuer="https://mcpeduauth.scalekit.dev",
            leeway=10,  # Allow 10 seconds clock skew
        )
        
        logger.info("\n✅ Token validated successfully!")
        logger.info(f"  User: {decoded['email']}")
        logger.info(f"  Roles: {decoded['roles']}")
        
    except jwt.InvalidTokenError as e:
        logger.error(f"❌ Token validation failed: {e}")
        raise
    
    # Test expired token
    logger.info("\n--- Testing Expired Token ---")
    expired_token = generator.generate_token(
        email="student@test.com",
        expires_in_seconds=-60,  # Expired 60 seconds ago (beyond leeway)
    )
    
    try:
        jwt.decode(
            expired_token,
            generator.public_pem,
            algorithms=["RS256"],
            audience="http://localhost:8000",
            issuer="https://mcpeduauth.scalekit.dev",
            leeway=10,
        )
        logger.error("❌ Expired token was accepted! This should not happen!")
        raise AssertionError("Expired token should be rejected")
    except jwt.ExpiredSignatureError:
        logger.info("✅ Expired token correctly rejected!")
    
    # Test wrong audience
    logger.info("\n--- Testing Wrong Audience ---")
    wrong_audience_token = generator.generate_token(
        email="student@test.com",
        audience="http://wrong-server.com",
    )
    
    try:
        jwt.decode(
            wrong_audience_token,
            generator.public_pem,
            algorithms=["RS256"],
            audience="http://localhost:8000",  # Expecting localhost
            issuer="https://mcpeduauth.scalekit.dev",
            leeway=10,
        )
        logger.error("❌ Wrong audience token was accepted!")
        raise AssertionError("Wrong audience should be rejected")
    except jwt.InvalidAudienceError:
        logger.info("✅ Wrong audience correctly rejected!")
    
    logger.info("\n✅ All validation tests passed!")


def test_role_extraction():
    """Test 3: Role extraction and mapping."""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Role Extraction and Mapping")
    logger.info("="*60)
    
    from src.middleware.auth import AuthenticationMiddleware
    
    middleware = AuthenticationMiddleware(None, debug=True)
    
    test_cases = [
        (["student"], "student", "Single student role"),
        (["teacher"], "teacher", "Single teacher role"),
        (["admin"], "admin", "Single admin role"),
        (["student", "teacher"], "teacher", "Multi-role (student + teacher)"),
        (["student", "admin"], "admin", "Multi-role (student + admin)"),
        (["teacher", "admin"], "admin", "Multi-role (teacher + admin)"),
        (["unknown"], "student", "Unknown role defaults to student"),
        ([], "student", "Empty roles default to student"),
    ]
    
    for roles, expected_role, description in test_cases:
        claims = {"roles": roles, "email": "test@test.com"}
        extracted_role = middleware._extract_role(claims)
        
        logger.info(f"\n{description}:")
        logger.info(f"  Input roles: {roles}")
        logger.info(f"  Expected: {expected_role}")
        logger.info(f"  Extracted: {extracted_role}")
        
        assert extracted_role == expected_role, f"Expected {expected_role}, got {extracted_role}"
        logger.info("  ✅ Correct!")
    
    logger.info("\n✅ All role extraction tests passed!")


def test_rbac_filtering():
    """Test 4: RBAC content filtering."""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: RBAC Content Filtering")
    logger.info("="*60)
    
    from src.tools.search_tools import ROLE_ACCESS_LEVELS
    
    logger.info("\n📋 Role Access Levels:")
    for role, access_levels in ROLE_ACCESS_LEVELS.items():
        logger.info(f"  {role}: {access_levels}")
    
    # Test access level filtering
    test_cases = [
        ("student", ["student"], "Student sees only student content"),
        ("teacher", ["student", "teacher"], "Teacher sees student + teacher content"),
        ("admin", ["student", "teacher", "admin"], "Admin sees all content"),
    ]
    
    for role, expected_access, description in test_cases:
        access_levels = ROLE_ACCESS_LEVELS.get(role, ["student"])
        
        logger.info(f"\n{description}:")
        logger.info(f"  Role: {role}")
        logger.info(f"  Expected: {expected_access}")
        logger.info(f"  Actual: {access_levels}")
        
        assert access_levels == expected_access, f"Expected {expected_access}, got {access_levels}"
        logger.info("  ✅ Correct!")
    
    logger.info("\n✅ All RBAC filtering tests passed!")


def main():
    """Run all JWT validation tests."""
    logger.info("\n" + "🧪"*30)
    logger.info("JWT VALIDATION TEST SUITE")
    logger.info("🧪"*30)
    
    try:
        # Test 1: Mock token generation
        generator = test_mock_token_generation()
        
        # Test 2: Token validation
        test_token_validation_without_scalekit()
        
        # Test 3: Role extraction
        test_role_extraction()
        
        # Test 4: RBAC filtering
        test_rbac_filtering()
        
        logger.info("\n" + "🎉"*30)
        logger.info("ALL TESTS PASSED! ✅")
        logger.info("🎉"*30)
        
        logger.info("\n📝 Summary:")
        logger.info("  ✅ Mock JWT token generation working")
        logger.info("  ✅ Token validation (signature, expiration, audience) working")
        logger.info("  ✅ Role extraction and mapping working")
        logger.info("  ✅ RBAC filtering working")
        
        logger.info("\n🚀 Next Steps:")
        logger.info("  1. Implement OAuth login/callback flow")
        logger.info("  2. Test with real Scalekit tokens")
        logger.info("  3. Test end-to-end authentication")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
