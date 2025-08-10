from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://oidc_user:oidc_password@localhost:5432/oidc_db"
    
    # Security
    secret_key: str = "your-super-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # Application
    app_title: str = "OIDC Authentication Server"
    app_description: str = "OpenID Connect compliant authentication and authorization server"
    app_version: str = "1.0.0"
    
    # OIDC
    issuer: str = "http://localhost:8000"
    supported_scopes: List[str] = ["openid", "profile", "email"]
    supported_response_types: List[str] = ["code"]
    supported_response_modes: List[str] = ["query"]
    supported_grant_types: List[str] = ["authorization_code", "refresh_token"]
    supported_subject_types: List[str] = ["public"]
    supported_id_token_signing_algs: List[str] = ["HS256"]
    supported_token_endpoint_auth_methods: List[str] = ["client_secret_post", "client_secret_basic"]
    supported_code_challenge_methods: List[str] = ["S256", "plain"]
    supported_claims: List[str] = [
        "sub", "iss", "aud", "exp", "iat", "auth_time",
        "name", "given_name", "family_name", "email", "email_verified"
    ]
    
    # Sample Client Configuration
    sample_client_id: str = "sample-client"
    sample_client_secret: str = "sample-secret"
    sample_client_name: str = "Sample OIDC Client"
    sample_client_redirect_uris: List[str] = ["http://localhost:3000/callback", "http://localhost:8080/callback"]
    sample_client_scopes: List[str] = ["openid", "profile", "email"]
    sample_client_type: str = "confidential"
    
    # Client Example Configuration
    client_example_port: int = 3000
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # UI Configuration
    alert_auto_hide_seconds: int = 5
    form_loading_timeout_seconds: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
