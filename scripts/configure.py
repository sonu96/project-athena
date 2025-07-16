#!/usr/bin/env python3
"""
Configuration helper for Athena Agent

Helps set up API keys and test connections.
"""

import os
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

def setup_env():
    """Interactive setup for .env file"""
    
    print("🏛️ Athena Agent Configuration Setup\n")
    
    env_path = Path(".env")
    if env_path.exists():
        print("⚠️  .env file already exists!")
        response = input("Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Keeping existing .env file")
            return
    
    # Read example
    example_path = Path("deployment/.env.example")
    if not example_path.exists():
        print("❌ deployment/.env.example not found")
        return
    
    with open(example_path) as f:
        content = f.read()
    
    print("\nConfiguring services:")
    print("1. LangSmith (for monitoring) - Optional")
    print("2. CDP AgentKit (for blockchain) - Required for real trading")
    print("3. Mem0 Cloud (for memory) - Required")
    print("4. Google Cloud Platform - Required for production")
    print("5. LLM APIs - At least one required")
    
    # LangSmith
    print("\n📊 LangSmith Configuration")
    langsmith_key = input("Enter LangSmith API key (or press Enter to skip): ").strip()
    if langsmith_key:
        content = content.replace('LANGSMITH_API_KEY=""', f'LANGSMITH_API_KEY="{langsmith_key}"')
        print("✅ LangSmith configured")
    
    # CDP
    print("\n🔗 CDP Configuration")
    print("Get API keys from: https://portal.cdp.coinbase.com/")
    cdp_key = input("Enter CDP API key name (or press Enter for simulation mode): ").strip()
    if cdp_key:
        cdp_secret = input("Enter CDP API key secret: ").strip()
        content = content.replace('CDP_API_KEY_NAME=""', f'CDP_API_KEY_NAME="{cdp_key}"')
        content = content.replace('CDP_API_KEY_SECRET=""', f'CDP_API_KEY_SECRET="{cdp_secret}"')
        print("✅ CDP configured")
    else:
        print("ℹ️  CDP will run in simulation mode")
    
    # Mem0
    print("\n🧠 Mem0 Cloud Configuration")
    print("Get API key from: https://app.mem0.ai/")
    mem0_key = input("Enter Mem0 API key (or press Enter to skip): ").strip()
    if mem0_key:
        content = content.replace('MEM0_API_KEY=""', f'MEM0_API_KEY="{mem0_key}"')
        print("✅ Mem0 configured")
    
    # GCP
    print("\n☁️  Google Cloud Platform Configuration")
    use_gcp = input("Configure GCP? (y/N): ").strip().lower() == 'y'
    if use_gcp:
        project_id = input("Enter GCP project ID: ").strip()
        creds_path = input("Enter path to service account JSON: ").strip()
        content = content.replace('GCP_PROJECT_ID=""', f'GCP_PROJECT_ID="{project_id}"')
        content = content.replace('GOOGLE_APPLICATION_CREDENTIALS=""', f'GOOGLE_APPLICATION_CREDENTIALS="{creds_path}"')
        print("✅ GCP configured")
    
    # LLMs
    print("\n🤖 LLM Configuration (at least one required)")
    openai_key = input("Enter OpenAI API key (or press Enter to skip): ").strip()
    if openai_key:
        content = content.replace('OPENAI_API_KEY=""', f'OPENAI_API_KEY="{openai_key}"')
        print("✅ OpenAI configured")
    
    anthropic_key = input("Enter Anthropic API key (or press Enter to skip): ").strip()
    if anthropic_key:
        content = content.replace('ANTHROPIC_API_KEY=""', f'ANTHROPIC_API_KEY="{anthropic_key}"')
        print("✅ Anthropic configured")
    
    # Write .env
    with open(env_path, 'w') as f:
        f.write(content)
    
    print("\n✅ Configuration saved to .env")
    print("\nTo test your setup, run:")
    print("  python test_setup.py")


def test_connections():
    """Test configured services"""
    print("\n🧪 Testing connections...\n")
    
    from src.config import settings
    
    # Test LangSmith
    if settings.langsmith_api_key:
        print("✅ LangSmith API key found")
        print(f"   Project: {settings.langsmith_project}")
    else:
        print("ℹ️  LangSmith not configured (optional)")
    
    # Test CDP
    if settings.cdp_api_key_name:
        print("✅ CDP credentials found")
        print(f"   Network: {settings.network}")
    else:
        print("ℹ️  CDP not configured (will use simulation)")
    
    # Test Mem0
    if settings.mem0_api_key:
        print("✅ Mem0 API key found")
    else:
        print("⚠️  Mem0 not configured (required for memory)")
    
    # Test GCP
    if settings.gcp_project_id:
        print("✅ GCP project configured")
        print(f"   Project: {settings.gcp_project_id}")
    else:
        print("ℹ️  GCP not configured (required for production)")
    
    # Test LLMs
    if settings.openai_api_key or settings.anthropic_api_key:
        print("✅ LLM API keys found")
    else:
        print("❌ No LLM API keys configured (at least one required)")
    
    print("\n" + "="*50)
    print("Configuration test complete!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Configure Athena Agent")
    parser.add_argument("--test", action="store_true", help="Test connections")
    
    args = parser.parse_args()
    
    if args.test:
        test_connections()
    else:
        setup_env()
        print("\nNow testing connections...")
        test_connections()