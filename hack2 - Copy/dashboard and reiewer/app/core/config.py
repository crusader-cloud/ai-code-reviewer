from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # GitHub OAuth
    github_client_id: str
    github_client_secret: str
    github_webhook_secret: str
    
    # LLM Configuration
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    
    # Application
    app_secret_key: str
    database_url: str = "sqlite:///./pr_reviewer.db"
    environment: str = "development"
    
    # LLM Provider
    llm_provider: str = "openai"
    llm_model: str = "gpt-4-turbo-preview"
    
    # Application URL
    app_url: str = "http://localhost:8000"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
