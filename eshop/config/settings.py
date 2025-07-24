"""Application settings and configuration."""

import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Main application settings."""
    
    # Application
    name: str = Field(default="eShop Modular Monolith", env="APP_NAME")
    version: str = Field(default="0.1.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Security
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Database
    db_host: str = Field(default="localhost", env="DB_HOST")
    db_port: int = Field(default=5432, env="DB_PORT")
    db_name: str = Field(default="eshop", env="DB_NAME")
    db_user: str = Field(default="postgres", env="DB_USER")
    db_password: str = Field(default="password", env="DB_PASSWORD")
    
    # Redis
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    # RabbitMQ
    rabbitmq_host: str = Field(default="localhost", env="RABBITMQ_HOST")
    rabbitmq_port: int = Field(default=5672, env="RABBITMQ_PORT")
    rabbitmq_user: str = Field(default="guest", env="RABBITMQ_USER")
    rabbitmq_password: str = Field(default="guest", env="RABBITMQ_PASSWORD")
    rabbitmq_vhost: str = Field(default="/", env="RABBITMQ_VHOST")
    
    # Keycloak
    keycloak_server_url: str = Field(default="http://localhost:8080", env="KEYCLOAK_SERVER_URL")
    keycloak_realm: str = Field(default="eshop", env="KEYCLOAK_REALM")
    keycloak_client_id: str = Field(default="eshop-api", env="KEYCLOAK_CLIENT_ID")
    keycloak_client_secret: str = Field(default="", env="KEYCLOAK_CLIENT_SECRET")
    keycloak_admin_username: str = Field(default="admin", env="KEYCLOAK_ADMIN_USERNAME")
    keycloak_admin_password: str = Field(default="admin", env="KEYCLOAK_ADMIN_PASSWORD")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    seq_url: str = Field(default="http://localhost:5341", env="SEQ_URL")
    log_enable_console: bool = Field(default=True, env="LOG_ENABLE_CONSOLE")
    log_enable_seq: bool = Field(default=False, env="LOG_ENABLE_SEQ")
    
    @property
    def database_connection_string(self) -> str:
        """Get database connection string."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def redis_connection_string(self) -> str:
        """Get Redis connection string."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    @property
    def rabbitmq_connection_string(self) -> str:
        """Get RabbitMQ connection string."""
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}/{self.rabbitmq_vhost}"
    
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# Global settings instance
settings = AppSettings() 