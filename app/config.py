from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database Configuration
    # DATABASE_URL environment variable is automatically read by Pydantic Settings
    database_url: str = "postgresql://postgres:kanjay@localhost:5433/tools_module_db"
    
    # API Configuration
    api_v1_prefix: str = "/api/v1"
    debug: bool = False
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    
    # Rate Limiting
    default_rate_limit_requests: int = 100
    default_rate_limit_window_seconds: int = 60
    
    # Tool Execution
    default_execution_timeout_seconds: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

