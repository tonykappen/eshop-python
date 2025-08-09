"""Application settings configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application
    name: str = Field(default="eShop Modular Monolith", alias="APP_NAME")
    version: str = Field(default="0.1.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    environment: str = Field(default="development", alias="ENVIRONMENT")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")  # nosec B104
    port: int = Field(default=8000, alias="PORT")

    # Security
    secret_key: str = Field(default="your-secret-key-here", alias="SECRET_KEY")

    # Database
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(default="eshop", alias="DB_NAME")
    db_user: str = Field(default="postgres", alias="DB_USER")
    db_password: str = Field(default="postgres", alias="DB_PASSWORD")

    @property
    def database_connection_string(self) -> str:
        """Get database connection string."""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # Redis
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")

    @property
    def redis_connection_string(self) -> str:
        """Get Redis connection string."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # RabbitMQ
    rabbitmq_host: str = Field(default="localhost", alias="RABBITMQ_HOST")
    rabbitmq_port: int = Field(default=5672, alias="RABBITMQ_PORT")
    rabbitmq_user: str = Field(default="guest", alias="RABBITMQ_USER")
    rabbitmq_password: str = Field(default="guest", alias="RABBITMQ_PASSWORD")

    @property
    def rabbitmq_connection_string(self) -> str:
        """Get RabbitMQ connection string."""
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}/"

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
        default="http://localhost:8000/auth/callback", alias="KEYCLOAK_CALLBACK_URI"
    )

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_enable_seq: bool = Field(default=False, alias="LOG_ENABLE_SEQ")
    seq_url: str = Field(default="http://localhost:5341", alias="SEQ_URL")
    log_enable_file: bool = Field(default=True, alias="LOG_ENABLE_FILE")
    log_directory: str = Field(default="logs", alias="LOG_DIRECTORY")
    log_separate_server_logs: bool = Field(
        default=True, alias="LOG_SEPARATE_SERVER_LOGS"
    )
    log_enable_request_logging: bool = Field(
        default=True, alias="LOG_ENABLE_REQUEST_LOGGING"
    )
    log_request_body: bool = Field(default=False, alias="LOG_REQUEST_BODY")
    log_response_body: bool = Field(default=False, alias="LOG_RESPONSE_BODY")

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
