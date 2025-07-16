#!/usr/bin/env python3.11
"""
Script to migrate secrets from .env to Google Cloud Secret Manager
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def migrate_secrets():
    """Migrate secrets from .env to Google Cloud Secret Manager"""
    print("🔐 Migrating Secrets to Google Cloud Secret Manager\n")
    
    # Load current .env file
    load_dotenv()
    
    # Import after setting up path
    from src.config.secret_manager import secret_manager
    
    if not secret_manager.client:
        print("❌ Google Cloud Secret Manager not available")
        print("Make sure you have:")
        print("1. Enabled Secret Manager API")
        print("2. Proper authentication (gcloud auth application-default login)")
        print("3. Correct project ID in GCP_PROJECT_ID")
        return False
    
    # Define secrets to migrate
    secrets_to_migrate = {
        "cdp-api-key-name": {
            "env_var": "CDP_API_KEY_NAME",
            "description": "CDP API Key Name"
        },
        "cdp-api-key-secret": {
            "env_var": "CDP_API_KEY_SECRET", 
            "description": "CDP API Secret (SENSITIVE)"
        },
        "cdp-wallet-secret": {
            "env_var": "CDP_WALLET_SECRET",
            "description": "CDP Wallet Private Key (HIGHLY SENSITIVE)"
        },
        "mem0-api-key": {
            "env_var": "MEM0_API_KEY",
            "description": "Mem0 Memory Service API Key (SENSITIVE)"
        },
        "langsmith-api-key": {
            "env_var": "LANGSMITH_API_KEY",
            "description": "LangSmith Monitoring API Key (SENSITIVE)"
        }
    }
    
    print("📋 Secrets to migrate:")
    for secret_name, info in secrets_to_migrate.items():
        env_value = os.getenv(info["env_var"])
        status = "✅ Available" if env_value else "❌ Missing"
        print(f"   {secret_name}: {info['description']} - {status}")
    
    print(f"\n🚀 Starting migration...")
    
    migrated_count = 0
    for secret_name, info in secrets_to_migrate.items():
        env_var = info["env_var"]
        description = info["description"]
        env_value = os.getenv(env_var)
        
        if not env_value:
            print(f"⚠️  Skipping {secret_name} - no value in environment")
            continue
        
        print(f"📤 Migrating {secret_name}...")
        
        # Create/update the secret
        success = secret_manager.create_secret(secret_name, env_value)
        
        if success:
            print(f"   ✅ {description} migrated successfully")
            migrated_count += 1
        else:
            print(f"   ❌ Failed to migrate {description}")
    
    print(f"\n📊 Migration Summary:")
    print(f"   Total secrets: {len(secrets_to_migrate)}")
    print(f"   Migrated: {migrated_count}")
    print(f"   Failed: {len(secrets_to_migrate) - migrated_count}")
    
    if migrated_count > 0:
        print(f"\n✅ Migration completed!")
        print(f"\n🔒 Security Recommendations:")
        print(f"   1. Update your deployment to use Secret Manager")
        print(f"   2. Remove sensitive values from .env file") 
        print(f"   3. Add .env to .gitignore (if not already)")
        print(f"   4. Use .env.example for new deployments")
        print(f"   5. Grant minimal IAM permissions for production")
        
        # Show how to test
        print(f"\n🧪 Test retrieval:")
        print(f"   python scripts/test_secrets.py")
        
        return True
    else:
        print(f"\n❌ No secrets were migrated")
        return False

if __name__ == "__main__":
    try:
        success = migrate_secrets()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n⚠️  Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)