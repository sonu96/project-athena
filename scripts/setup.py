#!/usr/bin/env python3
"""
Initial setup script for Athena Agent

Checks requirements and initializes necessary resources.
"""

import os
import sys
import json
import subprocess
from pathlib import Path


def check_python_version():
    """Check Python version"""
    print("Checking Python version...")
    
    if sys.version_info < (3, 10):
        print(f"❌ Python 3.10+ required. Current: {sys.version}")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]}")


def check_environment():
    """Check environment variables"""
    print("\nChecking environment variables...")
    
    required_vars = [
        "CDP_API_KEY_NAME",
        "CDP_API_KEY_SECRET",
        "MEM0_API_KEY",
        "GCP_PROJECT_ID",
        "GOOGLE_APPLICATION_CREDENTIALS"
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        print("\nPlease copy deployment/.env.example to .env and fill in your values")
        sys.exit(1)
    
    print("✅ All required environment variables found")


def check_gcp_credentials():
    """Check GCP credentials"""
    print("\nChecking GCP credentials...")
    
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path or not Path(creds_path).exists():
        print(f"❌ GCP credentials file not found: {creds_path}")
        sys.exit(1)
    
    try:
        with open(creds_path) as f:
            creds = json.load(f)
            project_id = creds.get("project_id")
            print(f"✅ GCP credentials valid for project: {project_id}")
    except Exception as e:
        print(f"❌ Invalid GCP credentials: {e}")
        sys.exit(1)


def create_directories():
    """Create necessary directories"""
    print("\nCreating directories...")
    
    dirs = ["wallet_data", "logs"]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✅ Created {dir_name}/")


def install_dependencies():
    """Install Python dependencies"""
    print("\nInstalling dependencies...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        sys.exit(1)


def main():
    """Run setup checks"""
    print("🏛️ Athena Agent Setup\n")
    
    check_python_version()
    check_environment()
    check_gcp_credentials()
    create_directories()
    install_dependencies()
    
    print("\n✅ Setup complete! You can now run:")
    print("   python -m src.core.agent")
    print("\nOr with Docker:")
    print("   docker-compose up")


if __name__ == "__main__":
    main()