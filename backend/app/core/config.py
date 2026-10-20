"""
Axiom Lens - AI-assisted Reverse Engineering Analysis Platform
Backend configuration module.
"""
from functools import lru_cache
from typing import Optional
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Application
    app_name: str = "Axiom Lens"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", description="development|production")
    debug: bool = Field(default=True, description="Enable debug mode")
    
    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    
    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./axiom_lens.db",
        description="SQLite database URL"
    )
    
    # Security
    secret_key: str = Field(
        default="dev-secret-change-in-production-min-32-chars",
        description="Secret key for JWT tokens (min 32 chars in production)"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # OIDC / Keycloak
    oidc_enabled: bool = Field(default=True, description="Enable OIDC authentication")
    oidc_issuer_url: str = Field(
        default="http://localhost:8080/realms/axiom-lens",
        description="Keycloak issuer URL"
    )
    oidc_client_id: str = Field(default="axiom-lens", description="OIDC client ID")
    oidc_client_secret: str = Field(default="", description="OIDC client secret")
    oidc_redirect_uri: str = Field(
        default="http://localhost:8000/api/v1/auth/callback",
        description="OIDC redirect URI"
    )
    oidc_scopes: str = Field(default="openid profile email", description="OIDC scopes")
    
    # Demo mode (localhost only)
    demo_mode: bool = Field(
        default=True,
        description="Enable demo mode (binds to localhost, refuses in production)"
    )
    
    # CORS
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        description="Comma-separated CORS origins"
    )
    
    # LLM (optional, opt-in)
    llm_enabled: bool = Field(default=False, description="Enable LLM features")
    llm_provider: str = Field(default="openai-compatible", description="LLM provider")
    llm_model: str = Field(default="", description="LLM model name")
    llm_base_url: str = Field(default="", description="LLM base URL")
    llm_api_key: str = Field(default="", description="LLM API key (server-side only)")
    
    @computed_field
    @property
    def cors_origin_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    @computed_field
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @computed_field
    @property
    def demo_mode_effective(self) -> bool:
        """Demo mode is only effective in development."""
        return self.demo_mode and not self.is_production


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()