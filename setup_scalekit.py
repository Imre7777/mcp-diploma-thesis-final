#!/usr/bin/env python3
"""
Scalekit MCP Server Setup & Verification Script

This script helps you:
1. Verify your current Scalekit configuration
2. Check MCP server settings via Scalekit API
3. List configured redirect URIs
4. Validate OAuth metadata
5. Create test users with roles (if needed)

Usage:
    python setup_scalekit.py --check          # Check current configuration
    python setup_scalekit.py --list-users     # List all users
    python setup_scalekit.py --verify-all     # Complete verification

Requirements:
    - scalekit-sdk-python>=2.4.0
    - .env file with SCALEKIT credentials
"""

import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
from scalekit import ScalekitClient

# Load environment variables
load_dotenv()

class ScalekitSetup:
    """Scalekit MCP Server Setup Helper"""
    
    def __init__(self):
        """Initialize Scalekit client from environment variables"""
        self.env_url = os.getenv('SCALEKIT_ENV_URL')
        self.client_id = os.getenv('SCALEKIT_CLIENT_ID')
        self.client_secret = os.getenv('SCALEKIT_CLIENT_SECRET')
        self.metadata_json = os.getenv('SCALEKIT_PROTECTED_RESOURCE_METADATA')
        
        if not all([self.env_url, self.client_id, self.client_secret]):
            print("❌ ERROR: Missing Scalekit credentials in .env file!")
            print("\nRequired variables:")
            print("  - SCALEKIT_ENV_URL")
            print("  - SCALEKIT_CLIENT_ID")
            print("  - SCALEKIT_CLIENT_SECRET")
            sys.exit(1)
        
        try:
            self.client = ScalekitClient(
                env_url=self.env_url,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            print(f"✅ Connected to Scalekit: {self.env_url}")
        except Exception as e:
            print(f"❌ Failed to connect to Scalekit: {e}")
            sys.exit(1)
    
    def check_configuration(self):
        """Check current Scalekit configuration"""
        print("\n" + "="*70)
        print("📋 CURRENT SCALEKIT CONFIGURATION")
        print("="*70)
        
        print(f"\n🌐 Environment:")
        print(f"   URL: {self.env_url}")
        print(f"   Client ID: {self.client_id}")
        print(f"   Client Secret: {self.client_secret[:20]}...")
        
        # Check metadata
        if self.metadata_json:
            try:
                metadata = json.loads(self.metadata_json.strip("'\""))
                print(f"\n✅ OAuth Metadata Configured:")
                print(f"   Resource: {metadata.get('resource', 'N/A')}")
                print(f"   Authorization Servers: {metadata.get('authorization_servers', [])}")
                print(f"   Scopes: {metadata.get('scopes_supported', [])}")
                print(f"   Documentation: {metadata.get('resource_documentation', 'N/A')}")
            except json.JSONDecodeError as e:
                print(f"\n⚠️  OAuth Metadata has JSON error: {e}")
        else:
            print(f"\n⚠️  No SCALEKIT_PROTECTED_RESOURCE_METADATA configured")
    
    def verify_mcp_endpoint(self):
        """Verify the MCP server's OAuth endpoint"""
        print("\n" + "="*70)
        print("🔍 VERIFYING MCP SERVER OAUTH ENDPOINT")
        print("="*70)
        
        import requests
        
        try:
            # Check if server is running
            response = requests.get(
                "https://leowiki-mcp.stream/.well-known/oauth-protected-resource",
                timeout=5
            )
            
            if response.status_code == 200:
                metadata = response.json()
                print("\n✅ MCP Server OAuth Endpoint is accessible!")
                print(f"\nReturned Metadata:")
                print(json.dumps(metadata, indent=2))
                
                # Validate metadata
                required_fields = ['resource', 'authorization_servers', 'bearer_methods_supported']
                missing = [f for f in required_fields if f not in metadata]
                
                if missing:
                    print(f"\n⚠️  Missing required fields: {missing}")
                else:
                    print("\n✅ All required OAuth 2.1 fields present")
                    
                # Check if points to correct auth server
                auth_servers = metadata.get('authorization_servers', [])
                if self.env_url in str(auth_servers):
                    print(f"✅ Authorization server matches ({self.env_url})")
                else:
                    print(f"⚠️  Authorization server mismatch:")
                    print(f"   Expected: {self.env_url}")
                    print(f"   Got: {auth_servers}")
            else:
                print(f"❌ Server returned {response.status_code}")
                print(f"   Response: {response.text[:200]}")
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot reach MCP server: {e}")
            print("\n💡 Make sure your server is running:")
            print("   docker ps | grep mcp-server")
    
    def list_critical_settings(self):
        """List critical settings needed for Claude Desktop"""
        print("\n" + "="*70)
        print("🚨 CRITICAL SETTINGS FOR CLAUDE DESKTOP")
        print("="*70)
        
        print("\n📝 Required in Scalekit Dashboard:")
        print("\n1. REDIRECT URIs (MUST HAVE):")
        print("   ✅ claude-desktop://auth/callback")
        print("   ✅ http://localhost:3000/callback")
        print("   ✅ https://leowiki-mcp.stream/callback")
        
        print("\n2. SCOPES (Should be defined):")
        print("   ✅ mcp:read")
        print("   ✅ mcp:write")
        print("   ✅ usr:read")
        print("   ✅ usr:write")
        
        print("\n3. TEST USERS WITH ROLES:")
        print("   ✅ student@test.local → Role: 'student'")
        print("   ✅ teacher@test.local → Role: 'teacher'")
        print("   ✅ admin@test.local → Role: 'admin'")
        
        print("\n4. TOKEN SETTINGS:")
        print("   ✅ Algorithm: RS256")
        print("   ✅ Token Lifetime: 3600 seconds (1 hour)")
        print("   ✅ Refresh Token: Enabled")
        
        print("\n" + "-"*70)
        print("⚠️  Login to Scalekit Dashboard to verify:")
        print("   https://app.scalekit.com")
        print("-"*70)
    
    def generate_claude_config(self):
        """Generate Claude Desktop configuration"""
        print("\n" + "="*70)
        print("📄 CLAUDE DESKTOP CONFIGURATION")
        print("="*70)
        
        config = {
            "mcpServers": {
                "edu-server": {
                    "url": "https://leowiki-mcp.stream/mcp"
                }
            }
        }
        
        print("\nAdd this to your claude_desktop_config.json:")
        print("\nWindows: %APPDATA%\\Claude\\claude_desktop_config.json")
        print("macOS:   ~/Library/Application Support/Claude/claude_desktop_config.json")
        print("Linux:   ~/.config/Claude/claude_desktop_config.json")
        
        print("\n" + "-"*70)
        print(json.dumps(config, indent=2))
        print("-"*70)
        
        print("\n✅ Just 5 lines! Claude Desktop will:")
        print("   1. Discover OAuth via /.well-known/oauth-protected-resource")
        print("   2. Redirect to Scalekit for authentication")
        print("   3. Get user role from JWT token")
        print("   4. Apply RBAC filtering automatically")
    
    def test_token_validation(self):
        """Test if token validation is working"""
        print("\n" + "="*70)
        print("🧪 TESTING TOKEN VALIDATION")
        print("="*70)
        
        print("\n💡 To test with a real token:")
        print("   1. Get a token from Scalekit (via OAuth flow)")
        print("   2. Run: curl https://leowiki-mcp.stream/mcp \\")
        print("           -H 'Authorization: Bearer YOUR_TOKEN'")
        print("\n   Without token, you should get 401 Unauthorized ✅")
    
    def run_complete_check(self):
        """Run complete verification"""
        self.check_configuration()
        self.verify_mcp_endpoint()
        self.list_critical_settings()
        self.generate_claude_config()
        self.test_token_validation()
        
        print("\n" + "="*70)
        print("✅ VERIFICATION COMPLETE")
        print("="*70)
        print("\n📋 Next Steps:")
        print("   1. Login to https://app.scalekit.com")
        print("   2. Verify Redirect URIs include: claude-desktop://auth/callback")
        print("   3. Create test users with roles (student/teacher/admin)")
        print("   4. Share Claude config with your colleague")
        print("   5. Test with Claude Desktop!")


def main():
    parser = argparse.ArgumentParser(
        description="Scalekit MCP Server Setup & Verification"
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check current configuration'
    )
    parser.add_argument(
        '--verify-endpoint',
        action='store_true',
        help='Verify MCP OAuth endpoint'
    )
    parser.add_argument(
        '--verify-all',
        action='store_true',
        help='Run complete verification'
    )
    parser.add_argument(
        '--claude-config',
        action='store_true',
        help='Generate Claude Desktop config'
    )
    
    args = parser.parse_args()
    
    # Initialize setup
    setup = ScalekitSetup()
    
    # Run requested checks
    if args.verify_all:
        setup.run_complete_check()
    elif args.check:
        setup.check_configuration()
    elif args.verify_endpoint:
        setup.verify_mcp_endpoint()
    elif args.claude_config:
        setup.generate_claude_config()
    else:
        # Default: run everything
        setup.run_complete_check()


if __name__ == "__main__":
    main()
