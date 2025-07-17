#!/usr/bin/env python3
"""Test direct CDP API calls without SDK"""

import os
import requests
import json
import jwt
import time
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

# CDP API configuration
CDP_API_KEY_ID = "af84cba4-2ffb-4296-9634-8696199216d7"
CDP_API_KEY_SECRET = """-----BEGIN EC PRIVATE KEY-----
MHcCAQEEII3xPX7RRCsIIqOQh0YQfZMcZNr/FPAuVXXOYAavJ7F6oAoGCCqGSM49
AwEHoUQDQgAEB0GXkxspJmFXmAtIDeyLLjNOa4rOy50vgH6T7NyVMfM3pU+sQQyS
P5Fu1doJXJr3GfAOX6P9bFtQMx0fPAr88Q==
-----END EC PRIVATE KEY-----"""

CDP_BASE_URL = "https://api.cdp.coinbase.com"

def create_jwt_token(uri_path: str, method: str = "GET"):
    """Create JWT token for CDP API authentication"""
    
    # JWT claims
    claims = {
        "sub": CDP_API_KEY_ID,
        "iss": "cdp",
        "aud": ["cdp_service"],
        "nbf": int(time.time()),
        "exp": int(time.time()) + 120,  # 2 minutes
        "uris": [f"{method} {CDP_BASE_URL}{uri_path}"]
    }
    
    # Sign with private key
    # Note: This is simplified - actual implementation needs proper key loading
    token = jwt.encode(claims, CDP_API_KEY_SECRET, algorithm="ES256", headers={"kid": CDP_API_KEY_ID})
    
    return token

def test_cdp_api():
    """Test CDP API calls"""
    
    # Test 1: List accounts
    print("Testing CDP API...")
    
    uri = "/platform/v2/evm/accounts"
    token = create_jwt_token(uri)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    response = requests.get(f"{CDP_BASE_URL}{uri}", headers=headers)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success! Found {len(data.get('accounts', []))} accounts")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_cdp_api()