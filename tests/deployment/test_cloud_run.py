"""
Test deployment configurations and Cloud Run readiness
"""

import pytest
import os
import json
from pathlib import Path


class TestDeploymentConfig:
    """Test deployment configuration files"""
    
    def test_dockerfile_exists(self):
        """Test that Dockerfile exists and is valid"""
        dockerfile_path = Path(__file__).parent.parent.parent / "Dockerfile"
        assert dockerfile_path.exists(), "Dockerfile not found"
        
        # Check basic Dockerfile content
        content = dockerfile_path.read_text()
        assert "FROM python:3.11-slim" in content
        assert "EXPOSE 8080" in content
        assert "CMD" in content
    
    def test_dockerignore_exists(self):
        """Test that .dockerignore exists"""
        dockerignore_path = Path(__file__).parent.parent.parent / ".dockerignore"
        assert dockerignore_path.exists(), ".dockerignore not found"
    
    def test_github_actions_workflow(self):
        """Test GitHub Actions workflow configuration"""
        workflow_path = Path(__file__).parent.parent.parent / ".github/workflows/deploy.yml"
        assert workflow_path.exists(), "GitHub Actions workflow not found"
        
        # Could add YAML validation here
    
    def test_environment_variables(self):
        """Test that required environment variables are documented"""
        env_example = Path(__file__).parent.parent.parent / ".env.example"
        assert env_example.exists(), ".env.example not found"
        
        content = env_example.read_text()
        required_vars = [
            "OPENAI_API_KEY",
            "MEM0_API_KEY",
            "BASE_RPC_URL",
            "AGENT_PRIVATE_KEY",
            "AGENT_ADDRESS"
        ]
        
        for var in required_vars:
            assert var in content, f"Required environment variable {var} not in .env.example"
    
    def test_production_env_template(self):
        """Test production environment template exists"""
        prod_env = Path(__file__).parent.parent.parent / ".env.production"
        assert prod_env.exists(), ".env.production template not found"


class TestCloudRunRequirements:
    """Test Cloud Run specific requirements"""
    
    def test_port_configuration(self):
        """Test that app listens on PORT environment variable"""
        # This would be tested in integration tests
        pass
    
    def test_health_endpoint(self):
        """Test that health endpoint exists"""
        # This would be tested with the running app
        pass
    
    def test_memory_limits(self):
        """Test that app can run within Cloud Run memory limits"""
        # Check that requirements don't exceed reasonable memory
        requirements_path = Path(__file__).parent.parent.parent / "requirements.txt"
        assert requirements_path.exists(), "requirements.txt not found"
        
        # Could analyze requirements for known memory-heavy packages


class TestDeploymentGuide:
    """Test deployment documentation"""
    
    def test_deployment_guide_exists(self):
        """Test that deployment guide exists"""
        guide_path = Path(__file__).parent.parent.parent / "deployment/deployment_guide.md"
        assert guide_path.exists(), "Deployment guide not found"
    
    def test_cloudbuild_config(self):
        """Test Cloud Build configuration"""
        cloudbuild_path = Path(__file__).parent.parent.parent / "deployment/cloudbuild.yaml"
        assert cloudbuild_path.exists(), "Cloud Build config not found"


@pytest.mark.skipif(
    os.getenv("CI") != "true",
    reason="Only run in CI environment"
)
class TestCICD:
    """Test CI/CD pipeline (only runs in CI)"""
    
    def test_docker_build(self):
        """Test that Docker image builds successfully"""
        import subprocess
        
        result = subprocess.run(
            ["docker", "build", "-t", "test-athena", "."],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Docker build failed: {result.stderr}"
    
    def test_docker_run(self):
        """Test that Docker container starts"""
        import subprocess
        import time
        
        # Start container
        result = subprocess.run(
            ["docker", "run", "-d", "--name", "test-athena", "-p", "8080:8080", "test-athena"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Docker run failed: {result.stderr}"
        
        # Give it time to start
        time.sleep(5)
        
        # Check if healthy
        health_result = subprocess.run(
            ["curl", "-f", "http://localhost:8080/health"],
            capture_output=True,
            text=True
        )
        
        # Cleanup
        subprocess.run(["docker", "stop", "test-athena"])
        subprocess.run(["docker", "rm", "test-athena"])
        
        assert health_result.returncode == 0, "Health check failed"