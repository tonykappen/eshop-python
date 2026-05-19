"""Application settings configuration."""

from pathlib import Path

from app.config.env import get_env, get_env_bool, get_env_int, get_env_list
from pydantic import Field
from pydantic_settings import BaseSettings

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_PROJECT_ROOT = _BACKEND_DIR.parent
_ENV_FILE = (
    _BACKEND_DIR / ".env"
    if (_BACKEND_DIR / ".env").exists()
    else _PROJECT_ROOT / ".env"
)


class Settings(BaseSettings):
    """Application settings."""

    # Application
    name: str = Field(
        default_factory=lambda: get_env("APP_NAME", "eShop Modular Monolith")
    )
    version: str = Field(default_factory=lambda: get_env("APP_VERSION", "0.1.0"))
    debug: bool = Field(default_factory=lambda: get_env_bool("DEBUG", False))
    environment: str = Field(
        default_factory=lambda: get_env("ENVIRONMENT", "development")
    )

    # Service metadata for CLEF logging
    service_name: str = Field(
        default_factory=lambda: get_env("SERVICE_NAME", "eshop-api")
    )
    service_version: str = Field(
        default_factory=lambda: get_env("SERVICE_VERSION", "1.0.0")
    )

    # Server
    host: str = Field(default_factory=lambda: get_env("HOST", "0.0.0.0"))  # nosec B104
    port: int = Field(default_factory=lambda: get_env_int("PORT", 8000))

    # Security
    secret_key: str = Field(
        default_factory=lambda: get_env("SECRET_KEY", "your-secret-key-here")
    )
    algorithm: str = Field(default_factory=lambda: get_env("ALGORITHM", "HS256"))
    access_token_expire_minutes: int = Field(
        default_factory=lambda: get_env_int("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
    )

    # Database
    database_url: str = Field(
        default_factory=lambda: get_env(
            "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/eshop"
        )
    )
    database_host: str = Field(
        default_factory=lambda: get_env("DATABASE_HOST", "localhost")
    )
    database_port: int = Field(
        default_factory=lambda: get_env_int("DATABASE_PORT", 5432)
    )
    database_name: str = Field(
        default_factory=lambda: get_env("DATABASE_NAME", "eshop")
    )
    database_user: str = Field(
        default_factory=lambda: get_env("DATABASE_USER", "postgres")
    )
    database_password: str = Field(
        default_factory=lambda: get_env("DATABASE_PASSWORD", "postgres")
    )

    # Database pool configuration (all configurable via env vars)
    db_pool_size: int = Field(default_factory=lambda: get_env_int("DB_POOL_SIZE", 10))
    db_max_overflow: int = Field(
        default_factory=lambda: get_env_int("DB_MAX_OVERFLOW", 20)
    )
    db_pool_recycle: int = Field(
        default_factory=lambda: get_env_int("DB_POOL_RECYCLE", 300)
    )
    db_pool_timeout: int = Field(
        default_factory=lambda: get_env_int("DB_POOL_TIMEOUT", 30)
    )
    db_echo: bool = Field(default_factory=lambda: get_env_bool("DB_ECHO", False))

    # Legacy database fields for backward compatibility
    @property
    def db_host(self) -> str:
        """Get database host."""
        return self.database_host

    @property
    def db_port(self) -> int:
        """Get database port."""
        return self.database_port

    @property
    def db_name(self) -> str:
        """Get database name."""
        return self.database_name

    @property
    def db_user(self) -> str:
        """Get database user."""
        return self.database_user

    @property
    def db_password(self) -> str:
        """Get database password."""
        return self.database_password

    @property
    def database_connection_string(self) -> str:
        """Get database connection string."""
        return f"postgresql+asyncpg://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"

    # Redis
    redis_url: str = Field(
        default_factory=lambda: get_env("REDIS_URL", "redis://localhost:6379")
    )
    redis_host: str = Field(default_factory=lambda: get_env("REDIS_HOST", "localhost"))
    redis_port: int = Field(default_factory=lambda: get_env_int("REDIS_PORT", 6379))
    redis_db: int = Field(default_factory=lambda: get_env_int("REDIS_DB", 0))

    @property
    def redis_connection_string(self) -> str:
        """Get Redis connection string."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # RabbitMQ
    rabbitmq_url: str = Field(
        default_factory=lambda: get_env(
            "RABBITMQ_URL", "amqp://guest:guest@localhost:5672/"
        )
    )
    rabbitmq_host: str = Field(
        default_factory=lambda: get_env("RABBITMQ_HOST", "localhost")
    )
    rabbitmq_port: int = Field(
        default_factory=lambda: get_env_int("RABBITMQ_PORT", 5672)
    )
    rabbitmq_user: str = Field(
        default_factory=lambda: get_env("RABBITMQ_USER", "guest")
    )
    rabbitmq_password: str = Field(
        default_factory=lambda: get_env("RABBITMQ_PASSWORD", "guest")
    )

    @property
    def rabbitmq_connection_string(self) -> str:
        """Get RabbitMQ connection string."""
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}/"

    # Keycloak
    keycloak_server_url: str = Field(
        default_factory=lambda: get_env("KEYCLOAK_SERVER_URL", "http://localhost:8080")
    )
    keycloak_realm: str = Field(
        default_factory=lambda: get_env("KEYCLOAK_REALM", "eshop")
    )
    keycloak_client_id: str = Field(
        default_factory=lambda: get_env("KEYCLOAK_CLIENT_ID", "eshop-api")
    )
    keycloak_client_secret: str = Field(
        default_factory=lambda: get_env(
            "KEYCLOAK_CLIENT_SECRET", "eshop-secure-client-secret-2024"
        )
    )
    keycloak_callback_uri: str = Field(
        default_factory=lambda: get_env(
            "KEYCLOAK_CALLBACK_URI", "http://localhost:8000/auth/callback"
        )
    )
    keycloak_grant_type: str = Field(
        default_factory=lambda: get_env("KEYCLOAK_GRANT_TYPE", "password")
    )
    keycloak_jwt_algorithms: list[str] = Field(
        default_factory=lambda: get_env_list("KEYCLOAK_JWT_ALGORITHMS", ["RS256"])
    )

    # Keycloak Credentials File
    keycloak_credentials_path: str | None = Field(default=None)

    # Keycloak Admin (for provisioning) - can be overridden by credentials file
    keycloak_admin_username: str = Field(
        default_factory=lambda: get_env("KEYCLOAK_ADMIN_USERNAME", "admin")
    )
    keycloak_admin_password: str = Field(
        default_factory=lambda: get_env("KEYCLOAK_ADMIN_PASSWORD", "admin")
    )

    # Keycloak Provisioning
    keycloak_auto_provision: bool = Field(
        default_factory=lambda: get_env_bool("KEYCLOAK_AUTO_PROVISION", False)
    )

    # Logging
    log_level: str = Field(default_factory=lambda: get_env("LOG_LEVEL", "INFO"))
    log_enable_seq: bool = Field(
        default_factory=lambda: get_env_bool("LOG_ENABLE_SEQ", True)
    )
    seq_url: str = Field(default_factory=lambda: get_env("SEQ_URL", "http://seq:80"))
    seq_api_key: str = Field(
        default_factory=lambda: get_env(
            "SEQ_API_KEY", "your-seq-api-key-change-in-production"
        )
    )
    log_enable_file: bool = Field(
        default_factory=lambda: get_env_bool("LOG_ENABLE_FILE", True)
    )
    log_directory: str = Field(
        default_factory=lambda: get_env("LOG_DIRECTORY", "run_time/logs")
    )
    log_separate_server_logs: bool = Field(
        default_factory=lambda: get_env_bool("LOG_SEPARATE_SERVER_LOGS", True)
    )
    log_enable_request_logging: bool = Field(
        default_factory=lambda: get_env_bool("LOG_ENABLE_REQUEST_LOGGING", True)
    )
    log_request_body: bool = Field(
        default_factory=lambda: get_env_bool("LOG_REQUEST_BODY", False)
    )
    log_response_body: bool = Field(
        default_factory=lambda: get_env_bool("LOG_RESPONSE_BODY", False)
    )

    class Config:
        """Pydantic configuration."""

        env_file = str(_ENV_FILE)
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"


# Global settings instance
settings = Settings()
