"""
TravelMate AI - Configuration Management
Follows OWASP security best practices
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "TravelMate AI"
    environment: str = "development"
    api_port: int = 8080
    log_level: str = "DEBUG"
    
    # LLM Configuration
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"  # Updated: using latest available model
    
    # Database
    database_url: str = "sqlite:///./travelmate.db"
    
    # DynamoDB (for payments)
    payments_db_endpoint: str = "http://localhost:8000"
    payments_db_table: str = "lea-payments-local"
    aws_region: str = "ap-southeast-1"
    aws_access_key_id: str = "dummy"
    aws_secret_access_key: str = "dummy"
    
    # Stripe
    stripe_api_key: str
    stripe_webhook_secret: str
    
    # MSIG API (optional)
    msig_api_base_url: str = "https://api.msig.com.sg/v1"
    msig_api_key: str = ""
    
    # Security
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8085"]
    rate_limit_per_minute: int = 60
    
    # Paths
    @property
    def project_root(self) -> Path:
        return Path(__file__).parent.parent.parent
    
    @property
    def assets_dir(self) -> Path:
        return self.project_root / "assets"
    
    @property
    def policy_wordings_dir(self) -> Path:
        return self.assets_dir / "Policy_Wordings"
    
    @property
    def taxonomy_file(self) -> Path:
        return self.assets_dir / "Taxonomy" / "Taxonomy_Hackathon.json"
    
    @property
    def claims_data_file(self) -> Path:
        return self.assets_dir / "Claims_Data_DB.pdf"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

