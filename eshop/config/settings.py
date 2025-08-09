"""Application settings and configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Main application settings."""

    # Application
    name: str = Field(default="eShop Modular Monolith", alias="APP_NAME")
    version: str = Field(default="0.1.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Security
    secret_key: str = Field(default="your-secret-key-here", alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # Database
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(default="eshop", alias="DB_NAME")
    db_user: str = Field(default="postgres", alias="DB_USER")
    db_password: str = Field(default="postgres", alias="DB_PASSWORD")

    # Redis
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_password: str | None = Field(default=None, alias="REDIS_PASSWORD")
    redis_db: int = Field(default=0, alias="REDIS_DB")

    # RabbitMQ
    rabbitmq_host: str = Field(default="localhost", alias="RABBITMQ_HOST")
    rabbitmq_port: int = Field(default=5672, alias="RABBITMQ_PORT")
    rabbitmq_user: str = Field(default="guest", alias="RABBITMQ_USER")
    rabbitmq_password: str = Field(default="guest", alias="RABBITMQ_PASSWORD")
    rabbitmq_vhost: str = Field(default="/", alias="RABBITMQ_VHOST")

    # Keycloak
    keycloak_server_url: str = Field(
        default="http://localhost:8080", alias="KEYCLOAK_SERVER_URL"
    )
    keycloak_realm: str = Field(default="eshop", alias="KEYCLOAK_REALM")
    keycloak_client_id: str = Field(default="eshop-api", alias="KEYCLOAK_CLIENT_ID")
    keycloak_client_secret: str = Field(
        default="your-client-secret", alias="KEYCLOAK_CLIENT_SECRET"
    )
    keycloak_callback_uri: str = Field(
        default="http://localhost:8000/callback", alias="KEYCLOAK_CALLBACK_URI"
    )

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    seq_url: str = Field(default="http://localhost:5341", alias="SEQ_URL")
    log_enable_console: bool = Field(default=True, alias="LOG_ENABLE_CONSOLE")
    log_enable_seq: bool = Field(default=False, alias="LOG_ENABLE_SEQ")
    log_enable_file: bool = Field(default=True, alias="LOG_ENABLE_FILE")
    log_directory: str = Field(default="logs", alias="LOG_DIRECTORY")
    log_separate_server_logs: bool = Field(default=True, alias="LOG_SEPARATE_SERVER_LOGS")
    log_enable_request_logging: bool = Field(default=True, alias="LOG_ENABLE_REQUEST_LOGGING")
    log_request_body: bool = Field(default=False, alias="LOG_REQUEST_BODY")
    log_response_body: bool = Field(default=False, alias="LOG_RESPONSE_BODY")

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
