"""
Google Cloud Secret Manager integration for secure credential management
"""

import os
import logging
from typing import Optional, Dict, Any
from google.cloud import secretmanager
from google.api_core import exceptions

logger = logging.getLogger(__name__)


class SecretManager:
    """
    Secure secret management using Google Cloud Secret Manager
    """
    
    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.getenv('GCP_PROJECT_ID')
        
        if not self.project_id:
            logger.warning("No GCP project ID found - falling back to environment variables")
            self.client = None
        else:
            try:
                self.client = secretmanager.SecretManagerServiceClient()
                logger.info(f"✅ Secret Manager initialized for project: {self.project_id}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Secret Manager: {e}")
                self.client = None
    
    def get_secret(self, secret_name: str, fallback_env_var: Optional[str] = None) -> Optional[str]:
        """
        Get secret from Google Cloud Secret Manager with local fallback
        
        Args:
            secret_name: Name of the secret in Secret Manager
            fallback_env_var: Environment variable to use as fallback
            
        Returns:
            Secret value or None if not found
        """
        # Try Secret Manager first
        if self.client and self.project_id:
            try:
                secret_path = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
                response = self.client.access_secret_version(request={"name": secret_path})
                secret_value = response.payload.data.decode("UTF-8")
                logger.debug(f"✅ Retrieved secret '{secret_name}' from Secret Manager")
                return secret_value
                
            except exceptions.NotFound:
                logger.warning(f"⚠️  Secret '{secret_name}' not found in Secret Manager")
            except exceptions.PermissionDenied:
                logger.warning(f"⚠️  Permission denied accessing secret '{secret_name}'")
            except Exception as e:
                logger.error(f"❌ Error accessing secret '{secret_name}': {e}")
        
        # Fallback to environment variable
        if fallback_env_var:
            env_value = os.getenv(fallback_env_var)
            if env_value:
                logger.debug(f"✅ Using environment variable '{fallback_env_var}' as fallback")
                return env_value
            else:
                logger.warning(f"⚠️  Environment variable '{fallback_env_var}' not found")
        
        logger.error(f"❌ Could not retrieve secret '{secret_name}'")
        return None
    
    def create_secret(self, secret_name: str, secret_value: str) -> bool:
        """
        Create a new secret in Google Cloud Secret Manager
        
        Args:
            secret_name: Name of the secret
            secret_value: Value to store
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client or not self.project_id:
            logger.error("❌ Secret Manager not available for secret creation")
            return False
        
        try:
            # Create the secret
            parent = f"projects/{self.project_id}"
            secret = {"replication": {"automatic": {}}}
            
            created_secret = self.client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_name,
                    "secret": secret
                }
            )
            
            # Add the secret version
            self.client.add_secret_version(
                request={
                    "parent": created_secret.name,
                    "payload": {"data": secret_value.encode("UTF-8")}
                }
            )
            
            logger.info(f"✅ Created secret '{secret_name}' in Secret Manager")
            return True
            
        except exceptions.AlreadyExists:
            logger.warning(f"⚠️  Secret '{secret_name}' already exists")
            return self.update_secret(secret_name, secret_value)
        except Exception as e:
            logger.error(f"❌ Failed to create secret '{secret_name}': {e}")
            return False
    
    def update_secret(self, secret_name: str, secret_value: str) -> bool:
        """
        Update an existing secret with a new version
        
        Args:
            secret_name: Name of the secret
            secret_value: New value to store
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client or not self.project_id:
            logger.error("❌ Secret Manager not available for secret update")
            return False
        
        try:
            parent = f"projects/{self.project_id}/secrets/{secret_name}"
            
            self.client.add_secret_version(
                request={
                    "parent": parent,
                    "payload": {"data": secret_value.encode("UTF-8")}
                }
            )
            
            logger.info(f"✅ Updated secret '{secret_name}' in Secret Manager")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update secret '{secret_name}': {e}")
            return False
    
    def list_secrets(self) -> list:
        """
        List all secrets in the project
        
        Returns:
            List of secret names
        """
        if not self.client or not self.project_id:
            return []
        
        try:
            parent = f"projects/{self.project_id}"
            secrets = []
            
            for secret in self.client.list_secrets(request={"parent": parent}):
                secret_name = secret.name.split('/')[-1]
                secrets.append(secret_name)
            
            return secrets
            
        except Exception as e:
            logger.error(f"❌ Failed to list secrets: {e}")
            return []


# Global instance
secret_manager = SecretManager()


def get_secure_config() -> Dict[str, Any]:
    """
    Get all configuration using secure secret management
    
    Returns:
        Dictionary of configuration values
    """
    config = {}
    
    # Define secrets mapping: secret_name -> (env_var_fallback, description)
    secrets_map = {
        "cdp-api-key-name": ("CDP_API_KEY_NAME", "CDP API Key Name"),
        "cdp-api-key-secret": ("CDP_API_KEY_SECRET", "CDP API Secret"),
        "cdp-wallet-secret": ("CDP_WALLET_SECRET", "CDP Wallet Private Key"),
        "mem0-api-key": ("MEM0_API_KEY", "Mem0 Memory Service API Key"),
        "langsmith-api-key": ("LANGSMITH_API_KEY", "LangSmith Monitoring API Key"),
        "openai-api-key": ("OPENAI_API_KEY", "OpenAI API Key (optional)"),
    }
    
    # Get all secrets
    for secret_name, (env_var, description) in secrets_map.items():
        value = secret_manager.get_secret(secret_name, env_var)
        if value:
            # Store using the environment variable name for compatibility
            config[env_var] = value
            logger.debug(f"✅ Loaded {description}")
        else:
            logger.warning(f"⚠️  Missing {description}")
            config[env_var] = None
    
    # Add non-secret configuration from environment
    config.update({
        "AGENT_ID": os.getenv("AGENT_ID", "athena-v1-mainnet"),
        "NETWORK": os.getenv("NETWORK", "base"),
        "NETWORK_ID": os.getenv("NETWORK_ID", "8453"),
        "GCP_PROJECT_ID": os.getenv("GCP_PROJECT_ID"),
        "GOOGLE_VERTEX_PROJECT": os.getenv("GOOGLE_VERTEX_PROJECT"),
        "GOOGLE_VERTEX_LOCATION": os.getenv("GOOGLE_VERTEX_LOCATION", "us-central1"),
        "LANGSMITH_PROJECT": os.getenv("LANGSMITH_PROJECT", "athena-mainnet-v1"),
        "STARTING_TREASURY": float(os.getenv("STARTING_TREASURY", "100.0")),
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "production"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
    })
    
    return config