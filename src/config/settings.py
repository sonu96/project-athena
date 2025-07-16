"""
Configuration settings for Athena Agent

Uses pydantic-settings for environment variable management
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    # Agent Configuration
    agent_id: str = Field(default="athena-v1", env="AGENT_ID")
    starting_treasury: float = Field(default=100.0, env="STARTING_TREASURY")
    observation_mode: bool = Field(default=True, env="OBSERVATION_MODE")
    
    # CDP Configuration
    cdp_api_key_name: str = Field(..., env="CDP_API_KEY_NAME")
    cdp_api_key_secret: str = Field(..., env="CDP_API_KEY_SECRET")
    network: str = Field(default="base-sepolia", env="NETWORK")
    
    # Memory System
    mem0_api_key: str = Field(..., env="MEM0_API_KEY")
    
    # Google Cloud Platform
    gcp_project_id: str = Field(..., env="GCP_PROJECT_ID")
    google_application_credentials: str = Field(..., env="GOOGLE_APPLICATION_CREDENTIALS")
    firestore_database: str = Field(default="(default)", env="FIRESTORE_DATABASE")
    bigquery_dataset: str = Field(default="athena_analytics", env="BIGQUERY_DATASET")
    
    # LLM Configuration (Optional)
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # Monitoring (Optional)
    langsmith_api_key: Optional[str] = Field(default=None, env="LANGSMITH_API_KEY")
    langsmith_project: str = Field(default="athena-v1", env="LANGSMITH_PROJECT")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8080, env="API_PORT")
    api_workers: int = Field(default=1, env="API_WORKERS")
    
    # Operational Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    environment: str = Field(default="development", env="ENV")
    
    # Feature Flags
    enable_websocket: bool = Field(default=True, env="ENABLE_WEBSOCKET")
    enable_monitoring: bool = Field(default=True, env="ENABLE_MONITORING")
    enable_cost_tracking: bool = Field(default=True, env="ENABLE_COST_TRACKING")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"
    
    @property
    def is_testnet(self) -> bool:
        """Check if using testnet"""
        return "sepolia" in self.network.lower() or "testnet" in self.network.lower()
    
    def get_llm_api_key(self, provider: str) -> Optional[str]:
        """Get API key for LLM provider"""
        if provider.lower() == "openai":
            return self.openai_api_key
        elif provider.lower() == "anthropic":
            return self.anthropic_api_key
        return None
    
    def validate_required_keys(self) -> bool:
        """Validate all required API keys are present"""
        required = [
            ("CDP API Key", self.cdp_api_key_name),
            ("CDP Secret", self.cdp_api_key_secret),
            ("Mem0 API Key", self.mem0_api_key),
            ("GCP Project", self.gcp_project_id)
        ]
        
        missing = []
        for name, value in required:
            if not value:
                missing.append(name)
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True


# Create singleton instance
settings = Settings()