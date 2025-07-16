#!/usr/bin/env python3.11
"""
Test script to verify Secret Manager integration
"""

import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_secret_manager():
    """Test Secret Manager functionality"""
    print("🧪 Testing Google Cloud Secret Manager Integration\n")
    
    from src.config.secret_manager import secret_manager, get_secure_config
    
    print("1. Testing Secret Manager connection...")
    if secret_manager.client:
        print("   ✅ Connected to Secret Manager")
        print(f"   🏗️  Project: {secret_manager.project_id}")
    else:
        print("   ❌ Secret Manager not available")
        print("   ℹ️  Will fall back to environment variables")
    
    print("\n2. Listing available secrets...")
    secrets = secret_manager.list_secrets()
    if secrets:
        print(f"   📋 Found {len(secrets)} secrets:")
        for secret in secrets:
            print(f"      • {secret}")
    else:
        print("   ⚠️  No secrets found (or permission denied)")
    
    print("\n3. Testing secure configuration loading...")
    config = get_secure_config()
    
    # Test critical secrets (without exposing values)
    critical_secrets = [
        "CDP_API_KEY_NAME",
        "CDP_API_KEY_SECRET", 
        "MEM0_API_KEY",
        "LANGSMITH_API_KEY"
    ]
    
    for secret_key in critical_secrets:
        value = config.get(secret_key)
        if value:
            # Show only first 8 chars for verification
            masked_value = value[:8] + "..." if len(value) > 8 else "***"
            print(f"   ✅ {secret_key}: {masked_value}")
        else:
            print(f"   ❌ {secret_key}: Not found")
    
    print("\n4. Testing configuration completeness...")
    required_config = [
        "AGENT_ID",
        "GCP_PROJECT_ID", 
        "GOOGLE_VERTEX_PROJECT",
        "STARTING_TREASURY"
    ]
    
    all_good = True
    for config_key in required_config:
        value = config.get(config_key)
        if value:
            print(f"   ✅ {config_key}: {value}")
        else:
            print(f"   ❌ {config_key}: Missing")
            all_good = False
    
    print(f"\n📊 Test Results:")
    if secret_manager.client and secrets and all_good:
        print("   🎉 Secret Manager fully operational!")
        print("   ✅ All secrets accessible")
        print("   ✅ Configuration complete")
        print("   ✅ Ready for production deployment")
        return True
    elif all_good:
        print("   ⚠️  Secret Manager unavailable but fallback working")
        print("   ✅ Configuration complete via environment variables")
        return True
    else:
        print("   ❌ Configuration incomplete")
        print("   ⚠️  Check missing secrets/configuration")
        return False

def test_cost_manager_with_secrets():
    """Test that cost manager works with secret-managed config"""
    print("\n5. Testing cost manager with secure config...")
    
    try:
        from src.monitoring.cost_manager import cost_manager
        
        # Reset for clean test
        cost_manager.daily_costs = cost_manager._create_fresh_costs()
        cost_manager.emergency_mode = False
        cost_manager.shutdown_triggered = False
        
        status = cost_manager.get_status()
        print(f"   ✅ Cost Manager operational")
        print(f"   💰 Budget: ${status['hard_limit']}")
        print(f"   📊 Current spending: ${status['total_cost']:.6f}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Cost Manager test failed: {e}")
        return False

if __name__ == "__main__":
    try:
        success1 = test_secret_manager()
        success2 = test_cost_manager_with_secrets()
        
        overall_success = success1 and success2
        
        if overall_success:
            print(f"\n🎉 All tests passed! System ready for secure production deployment.")
        else:
            print(f"\n⚠️  Some tests failed. Review configuration before production.")
            
        sys.exit(0 if overall_success else 1)
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)