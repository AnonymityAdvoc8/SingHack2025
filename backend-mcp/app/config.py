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
    
    # Tavily Search API (Real-time Intelligence)
    tavily_api_key: str
    tavily_search_depth: str = "advanced"  # "basic" or "advanced"
    
    # Database (Policy & User Data)
    database_url: str = "sqlite:///./travelmate.db"
    
    # PostgreSQL Claims Database (MSIG Historical Data)
    claims_db_host: str = "hackathon-db.ceqjfmi6jhdd.ap-southeast-1.rds.amazonaws.com"
    claims_db_port: int = 5432
    claims_db_name: str = "hackathon_db"
    claims_db_user: str = "hackathon_user"
    claims_db_password: str = "Hackathon2025!"
    claims_db_schema: str = "hackathon"
    
    @property
    def claims_database_url(self) -> str:
        """PostgreSQL connection URL for claims data"""
        return f"postgresql://{self.claims_db_user}:{self.claims_db_password}@{self.claims_db_host}:{self.claims_db_port}/{self.claims_db_name}"
    
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
    msig_api_base_url: str = "https://dev.api.ancileo.com/v1"
    msig_api_key: str = ""
    
    # MSIG/Ancileo Travel Insurance API
    ancileo_pricing_url: str = "https://dev.api.ancileo.com/v1/travel/front/pricing"
    ancileo_purchase_url: str = "https://dev.api.ancileo.com/v1/travel/front/purchase"
    ancileo_api_key: str = ""  # Optional: Add API key to enable real MSIG pricing
    
    # Google OAuth (Gmail Integration)
    google_client_id: str = ""  # Optional: Google OAuth client ID for Gmail scanning
    google_client_secret: str = ""  # Optional: Google OAuth client secret
    
    # Risk Configuration
    high_risk_destinations: str = "USA,Canada,Japan,Switzerland"  # Comma-separated list
    high_risk_multiplier: float = 1.3  # Premium multiplier for high-risk destinations
    high_risk_activity_multiplier: float = 1.4  # Premium multiplier for high-risk activities
    
    @property
    def high_risk_destinations_list(self) -> list[str]:
        """Parse comma-separated destinations into a list"""
        if not self.high_risk_destinations:
            return []
        return [country.strip() for country in self.high_risk_destinations.split(",") if country.strip()]
    
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

