#!/usr/bin/env python3
"""Pre-deployment checklist for Phase 1 production"""

import os
import json
import subprocess
from pathlib import Path

def check_item(description, check_func):
    """Run a check and display result"""
    try:
        result, details = check_func()
        if result:
            print(f"✅ {description}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {description}")
            if details:
                print(f"   {details}")
        return result
    except Exception as e:
        print(f"❌ {description}")
        print(f"   Error: {e}")
        return False

def check_files():
    """Check required files exist"""
    required_files = [
        "Dockerfile",
        "requirements.txt",
        "src/main.py",
        "src/api/server.py",
        "src/core/agent.py",
        "cloud_functions/pool_collector/main.py",
        "service-account-key.json",
        ".env.production"
    ]
    
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
    
    if missing:
        return False, f"Missing files: {', '.join(missing)}"
    return True, "All required files present"

def check_docker():
    """Check Docker is running"""
    try:
        result = subprocess.run(["docker", "info"], capture_output=True)
        if result.returncode == 0:
            return True, "Docker is running"
        return False, "Docker is not running"
    except:
        return False, "Docker not found"

def check_gcloud():
    """Check gcloud is configured"""
    try:
        result = subprocess.run(["gcloud", "config", "get-value", "project"], 
                              capture_output=True, text=True)
        project = result.stdout.strip()
        if project:
            return True, f"Project: {project}"
        return False, "No project set"
    except:
        return False, "gcloud not found"

def check_credentials():
    """Check service account credentials"""
    try:
        with open("service-account-key.json", "r") as f:
            sa_data = json.load(f)
            project_id = sa_data.get("project_id")
            return True, f"Project ID: {project_id}"
    except:
        return False, "Cannot read service account key"

def check_bigquery():
    """Check BigQuery tables exist"""
    try:
        from google.cloud import bigquery
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account-key.json"
        
        with open("service-account-key.json", "r") as f:
            project_id = json.load(f)["project_id"]
        
        client = bigquery.Client(project=project_id)
        tables = list(client.list_tables("athena_analytics"))
        
        if tables:
            return True, f"{len(tables)} tables found"
        return False, "No tables found"
    except Exception as e:
        return False, str(e)

def check_secrets():
    """Check required environment variables"""
    required_vars = [
        "CDP_API_KEY_NAME",
        "CDP_API_KEY_SECRET",
        "MEM0_API_KEY",
        "LANGSMITH_API_KEY"
    ]
    
    # Check .env file
    if Path(".env").exists():
        from dotenv import dotenv_values
        config = dotenv_values(".env")
        
        missing = []
        for var in required_vars:
            if var not in config or not config[var] or config[var].startswith("your_"):
                missing.append(var)
        
        if missing:
            return False, f"Missing/invalid: {', '.join(missing)}"
        return True, "All secrets configured"
    
    return False, ".env file not found"

def main():
    """Run all pre-deployment checks"""
    print("🔍 Athena Agent Phase 1 - Pre-Deployment Checklist\n")
    
    checks = [
        ("Required files", check_files),
        ("Docker daemon", check_docker),
        ("Google Cloud CLI", check_gcloud),
        ("Service account", check_credentials),
        ("BigQuery setup", check_bigquery),
        ("Environment secrets", check_secrets)
    ]
    
    passed = 0
    total = len(checks)
    
    for description, check_func in checks:
        if check_item(description, check_func):
            passed += 1
        print()
    
    print("="*50)
    print(f"Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n✅ Ready for deployment!")
        print("\nRun: python scripts/deploy_production.py")
    else:
        print("\n❌ Please fix the issues above before deploying")
        return False
    
    return True

if __name__ == "__main__":
    main()