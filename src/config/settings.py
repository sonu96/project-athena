"""
Application settings and configuration management
"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # GCP Configuration
    google_application_credentials: Optional[str] = Field(None, env="GOOGLE_APPLICATION_CREDENTIALS")
    gcp_project_id: str = Field("athena-defi-agent", env="GCP_PROJECT_ID")
    firestore_database: str = Field("(default)", env="FIRESTORE_DATABASE")
    bigquery_dataset: str = Field("athena_agent", env="BIGQUERY_DATASET")
    
    # API Keys
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    cdp_api_key_name: Optional[str] = Field(None, env="CDP_API_KEY_NAME")
    cdp_api_key_secret: Optional[str] = Field(None, env="CDP_API_KEY_SECRET")
    
    # Agent Configuration
    agent_starting_treasury: float = Field(100.0, env="AGENT_STARTING_TREASURY")
    agent_id: str = Field("athena_agent_001", env="AGENT_ID")
    network: str = Field("base-sepolia", env="NETWORK")
    
    # Mem0 Configuration
    mem0_api_key: Optional[str] = Field(None, env="MEM0_API_KEY")
    vector_db_url: Optional[str] = Field(None, env="VECTOR_DB_URL")
    
    # LangSmith Configuration
    langsmith_api_key: Optional[str] = Field(None, env="LANGSMITH_API_KEY")
    langsmith_project: str = Field("athena-defi-phase1", env="LANGSMITH_PROJECT")
    
    # Market Data APIs
    coingecko_api_key: Optional[str] = Field(None, env="COINGECKO_API_KEY")
    etherscan_api_key: Optional[str] = Field(None, env="ETHERSCAN_API_KEY")
    
    # Agent Behavior Configuration
    observation_interval_seconds: int = Field(3600, env="OBSERVATION_INTERVAL_SECONDS")
    memory_update_interval_seconds: int = Field(86400, env="MEMORY_UPDATE_INTERVAL_SECONDS")
    survival_check_interval_seconds: int = Field(3600, env="SURVIVAL_CHECK_INTERVAL_SECONDS")
    max_daily_costs_usd: float = Field(15.0, env="MAX_DAILY_COSTS_USD")
    critical_treasury_threshold_usd: float = Field(25.0, env="CRITICAL_TREASURY_THRESHOLD_USD")
    warning_treasury_threshold_usd: float = Field(50.0, env="WARNING_TREASURY_THRESHOLD_USD")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create global settings instance
settings = Settings()