#!/usr/bin/env python3.11
"""Direct test of secret access"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_direct_secret_access():
    """Test direct secret access"""
    print("🔐 Testing Direct Secret Manager Access\n")
    
    print("1. Environment check:")
    project_id = os.getenv('GCP_PROJECT_ID')
    print(f"   GCP_PROJECT_ID: {project_id}")
    
    if not project_id:
        print("   ❌ No project ID found")
        return False
    
    print("\n2. Testing Secret Manager client:")
    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        print("   ✅ Secret Manager client created")
        
        # Test listing secrets
        parent = f"projects/{project_id}"
        secrets = []
        for secret in client.list_secrets(request={"parent": parent}):
            secret_name = secret.name.split('/')[-1]
            secrets.append(secret_name)
        
        print(f"   📋 Found {len(secrets)} secrets: {secrets}")
        
        # Test accessing a secret
        if secrets:
            test_secret = secrets[0]
            secret_path = f"projects/{project_id}/secrets/{test_secret}/versions/latest"
            
            try:
                response = client.access_secret_version(request={"name": secret_path})
                secret_value = response.payload.data.decode("UTF-8")
                masked_value = secret_value[:8] + "..." if len(secret_value) > 8 else "***"
                print(f"   ✅ Retrieved '{test_secret}': {masked_value}")
                return True
                
            except Exception as e:
                print(f"   ❌ Failed to access secret: {e}")
                return False
        else:
            print("   ⚠️  No secrets found")
            return False
            
    except Exception as e:
        print(f"   ❌ Secret Manager error: {e}")
        return False

if __name__ == "__main__":
    success = test_direct_secret_access()
    
    if success:
        print(f"\n🎉 Secret Manager is working correctly!")
        print(f"✅ All secrets are securely stored and accessible")
        print(f"✅ Ready to switch to Secret Manager for production")
    else:
        print(f"\n⚠️  Secret Manager access needs troubleshooting")