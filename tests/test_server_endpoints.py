#!/usr/bin/env python3
"""
Quick Test Script for MCP Educational Server

This script tests all public endpoints to ensure the server is working
correctly before attempting Claude Desktop integration.

Usage:
    python tests/test_server_endpoints.py
"""

import sys
import json
import requests
from colorama import init, Fore, Style

# Initialize colorama for Windows
init()

SERVER_URL = "http://localhost:8000"

def print_header(text):
    """Print a formatted header."""
    print(f"\n{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{text.center(70)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}\n")

def print_success(text):
    """Print success message."""
    print(f"{Fore.GREEN}[OK] {text}{Style.RESET_ALL}")

def print_error(text):
    """Print error message."""
    print(f"{Fore.RED}[ERROR] {text}{Style.RESET_ALL}")

def print_info(text):
    """Print info message."""
    print(f"{Fore.YELLOW}[INFO] {text}{Style.RESET_ALL}")

def test_health_endpoint():
    """Test the /health endpoint."""
    print_header("Test 1: Health Check Endpoint")
    
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        
        if response.status_code == 200:
            print_success(f"Status Code: {response.status_code} OK")
            
            data = response.json()
            print_info(f"Response: {json.dumps(data, indent=2)}")
            
            # Verify expected fields
            expected_fields = ["status", "server", "version", "authentication", "rbac"]
            for field in expected_fields:
                if field in data:
                    print_success(f"Field '{field}': {data[field]}")
                else:
                    print_error(f"Missing field: {field}")
            
            return data.get("status") == "healthy"
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Connection failed! Is the server running?")
        print_info(f"Make sure the server is running on {SERVER_URL}")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_oauth_discovery_endpoint():
    """Test the /.well-known/oauth-protected-resource endpoint."""
    print_header("Test 2: OAuth Discovery Endpoint")
    
    try:
        response = requests.get(
            f"{SERVER_URL}/.well-known/oauth-protected-resource",
            timeout=5
        )
        
        if response.status_code == 200:
            print_success(f"Status Code: {response.status_code} OK")
            
            data = response.json()
            print_info(f"Response: {json.dumps(data, indent=2)}")
            
            # Verify expected fields
            expected_fields = [
                "authorization_servers",
                "bearer_methods_supported",
                "resource",
                "resource_documentation",
                "scopes_supported"
            ]
            
            for field in expected_fields:
                if field in data:
                    print_success(f"Field '{field}': {data[field]}")
                else:
                    print_error(f"Missing field: {field}")
            
            # Verify authorization server URL
            if data.get("authorization_servers"):
                auth_server = data["authorization_servers"][0]
                if "scalekit.dev" in auth_server:
                    print_success(f"Scalekit authorization server configured: {auth_server}")
                else:
                    print_error(f"Unexpected authorization server: {auth_server}")
            
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Connection failed! Is the server running?")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_protected_endpoint():
    """Test a protected endpoint (should return 401 without auth)."""
    print_header("Test 3: Protected Endpoint (No Auth)")
    
    try:
        response = requests.post(f"{SERVER_URL}/", timeout=5)
        
        if response.status_code == 401:
            print_success(f"Status Code: {response.status_code} Unauthorized (Expected)")
            
            # Check for WWW-Authenticate header
            if "WWW-Authenticate" in response.headers:
                print_success(f"WWW-Authenticate header present: {response.headers['WWW-Authenticate']}")
            else:
                print_error("Missing WWW-Authenticate header")
            
            try:
                data = response.json()
                print_info(f"Response: {json.dumps(data, indent=2)}")
                
                if "error" in data and data["error"] == "invalid_token":
                    print_success("OAuth 2.1 error response format is correct")
                else:
                    print_error("Unexpected error response format")
            except:
                print_error("Response is not valid JSON")
            
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code} (expected 401)")
            print_info(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Connection failed! Is the server running?")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_qdrant_connection():
    """Test connection to Qdrant."""
    print_header("Test 4: Qdrant Vector Database")
    
    try:
        response = requests.get("http://localhost:6334/collections/educational_content", timeout=5)
        
        if response.status_code == 200:
            print_success("Qdrant is running and accessible")
            
            data = response.json()
            if "result" in data:
                result = data["result"]
                print_success(f"Collection: educational_content")
                print_info(f"  Points count: {result.get('points_count', 'N/A')}")
                print_info(f"  Vectors count: {result.get('vectors_count', 'N/A')}")
                print_info(f"  Status: {result.get('status', 'N/A')}")
            
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Connection failed! Is Qdrant running?")
        print_info("Start Qdrant with: docker start qdrant-mcp-edu")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def main():
    """Run all tests."""
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}")
    print("="*70)
    print("   MCP EDUCATIONAL SERVER - ENDPOINT TESTING SUITE")
    print("="*70)
    print(f"{Style.RESET_ALL}")
    
    print_info(f"Testing server at: {SERVER_URL}")
    print_info("This will verify all endpoints are working correctly\n")
    
    # Run tests
    results = {
        "Health Check": test_health_endpoint(),
        "OAuth Discovery": test_oauth_discovery_endpoint(),
        "Protected Endpoint": test_protected_endpoint(),
        "Qdrant Connection": test_qdrant_connection(),
    }
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    print(f"\n{Fore.CYAN}{'-' * 70}{Style.RESET_ALL}")
    
    if passed == total:
        print(f"\n{Fore.GREEN}{Style.BRIGHT}SUCCESS! ALL TESTS PASSED! ({passed}/{total}){Style.RESET_ALL}")
        print(f"{Fore.GREEN}Your server is ready for Claude Desktop integration!{Style.RESET_ALL}\n")
        return 0
    else:
        print(f"\n{Fore.RED}{Style.BRIGHT}WARNING: SOME TESTS FAILED ({passed}/{total}){Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Please fix the issues before proceeding.{Style.RESET_ALL}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
