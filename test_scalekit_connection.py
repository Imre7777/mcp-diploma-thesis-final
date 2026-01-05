"""
Test Scalekit Connection - Debug OAuth Configuration

This script tests if Scalekit is configured correctly.
"""

import sys
import httpx

# Configuration from .env
SCALEKIT_ENV_URL = "https://mcpeduauth.scalekit.dev"
SCALEKIT_CLIENT_ID = "skc_35934031996379566"
ORGANIZATION_ID = "org_106606852955439874"
REDIRECT_URI = "http://localhost:8000/auth/callback"

print("="*70)
print("Testing Scalekit OAuth Configuration")
print("="*70)
print(f"Scalekit URL: {SCALEKIT_ENV_URL}")
print(f"Client ID: {SCALEKIT_CLIENT_ID}")
print(f"Organization ID: {ORGANIZATION_ID}")
print(f"Redirect URI: {REDIRECT_URI}")
print("="*70)

# Build the authorization URL
auth_url = (
    f"{SCALEKIT_ENV_URL}/authorize?"
    f"response_type=code&"
    f"client_id={SCALEKIT_CLIENT_ID}&"
    f"redirect_uri={REDIRECT_URI}&"
    f"organization_id={ORGANIZATION_ID}&"
    f"state=test123&"
    f"scope=openid+profile+email"
)

print("\nAuthorization URL that would be generated:")
print(auth_url)
print("\n")

# Test if the URL is accessible
print("Testing if Scalekit authorization endpoint responds...")
try:
    response = httpx.get(auth_url, follow_redirects=False, timeout=10.0)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 404:
        print("\n[ERROR] 404 Error - Possible causes:")
        print("   1. Organization ID might not exist in Scalekit")
        print("   2. Magic Link & OTP might not be enabled for this organization")
        print("   3. Organization might not have any enabled connections")
        print("\n[NEXT STEPS]:")
        print("   - Go to Scalekit Dashboard -> Organizations")
        print(f"   - Find organization: {ORGANIZATION_ID}")
        print("   - Check if it has any enabled authentication methods")
        print("   - Make sure 'Magic Link & OTP' is enabled for this org")
    
    elif response.status_code == 302:
        print("[SUCCESS] Redirect working! This is expected.")
        print(f"   Redirects to: {response.headers.get('Location', 'N/A')}")
    
    elif response.status_code == 200:
        print("[SUCCESS] Page loads successfully!")
        print(f"   Content length: {len(response.content)} bytes")
    
    else:
        print(f"[WARNING] Unexpected status code: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
    
except httpx.RequestError as e:
    print(f"\n[ERROR] Connection error: {e}")
    print("   Make sure you have internet connection")
except Exception as e:
    print(f"\n[ERROR] Unexpected error: {e}")

print("\n" + "="*70)
print("Debug Complete")
print("="*70)
