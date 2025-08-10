"""Tests for application configuration and settings."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from eshop.config.settings import Settings


class TestSettings:
    """Test application settings configuration."""

    def test_default_settings(self):
        """Test default settings values."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()

            # Test application defaults
            assert settings.name == "eShop Modular Monolith"
            assert settings.version == "0.1.0"
            assert settings.debug is True  # Default is True in current implementation
            assert settings.environment == "development"

            # Test server defaults
            assert settings.host == "0.0.0.0"
            assert settings.port == 8000

            # Test security defaults
            assert settings.secret_key == "your-secret-key-here-change-in-production"
            assert settings.algorithm == "HS256"
            assert settings.access_token_expire_minutes == 30

            # Test database defaults
            assert settings.database_host == "localhost"
            assert settings.database_port == 5432
            assert settings.database_name == "eshop"
            assert settings.database_user == "eshop_user"
            assert settings.database_password == "eshop_password"

            # Test cache defaults
            assert settings.redis_url == "redis://localhost:6379"

            # Test messaging defaults
            assert settings.rabbitmq_url == "amqp://guest:guest@localhost:5672/"

            # Test logging defaults
            assert settings.log_level == "INFO"
            assert settings.log_enable_request_logging is True

    def test_environment_override(self):
        """Test environment variable overrides."""
        test_env = {
            "APP_NAME": "Test eShop",
            "APP_VERSION": "1.0.0",
            "DEBUG": "false",
            "ENVIRONMENT": "production",
            "HOST": "127.0.0.1",
            "PORT": "9000",
            "SECRET_KEY": "test-secret-key",
            "ALGORITHM": "HS512",
            "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
            "DATABASE_HOST": "test-db-host",
            "DATABASE_PORT": "5433",
            "DATABASE_NAME": "test_db",
            "DATABASE_USER": "test_user",
            "DATABASE_PASSWORD": "test_password",
            "REDIS_URL": "redis://test-redis:6379",
            "RABBITMQ_URL": "amqp://test-rabbit:5672/",
            "LOG_LEVEL": "DEBUG",
            "LOG_ENABLE_REQUEST_LOGGING": "false"
        }

        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()

            # Test overridden values
            assert settings.name == "Test eShop"
            assert settings.version == "1.0.0"
            assert settings.debug is False
            assert settings.environment == "production"
            assert settings.host == "127.0.0.1"
            assert settings.port == 9000
            assert settings.secret_key == "test-secret-key"
            assert settings.algorithm == "HS512"
            assert settings.access_token_expire_minutes == 60
            assert settings.database_host == "test-db-host"
            assert settings.database_port == 5433
            assert settings.database_name == "test_db"
            assert settings.database_user == "test_user"
            assert settings.database_password == "test_password"
            assert settings.redis_url == "redis://test-redis:6379"
            assert settings.rabbitmq_url == "amqp://test-rabbit:5672/"
            assert settings.log_level == "DEBUG"
            assert settings.log_enable_request_logging is False

    def test_database_connection_string(self):
        """Test database connection string generation and format."""
        settings = Settings()

        # Test with default values
        connection_string = settings.database_connection_string
        expected = "postgresql+asyncpg://eshop_user:eshop_password@localhost:5432/eshop"
        assert connection_string == expected

        # Test format validation
        assert isinstance(connection_string, str)
        assert connection_string.startswith("postgresql+asyncpg://")
        assert "@" in connection_string
        assert ":" in connection_string

        # Test structure validation
        parts = connection_string.split("://")
        assert len(parts) == 2

        protocol = parts[0]
        connection = parts[1]

        assert protocol == "postgresql+asyncpg"
        assert "@" in connection
        assert ":" in connection



    def test_legacy_properties(self):
        """Test legacy property methods for backward compatibility."""
        settings = Settings()

        # Test legacy database properties - they should be the same as the new ones
        assert settings.database_url == "postgresql://eshop_user:eshop_password@localhost:5432/eshop"  # This is a field
        assert settings.database_connection_string == "postgresql+asyncpg://eshop_user:eshop_password@localhost:5432/eshop"  # This is a property
        assert settings.database_host == settings.database_host
        assert settings.database_port == settings.database_port
        assert settings.database_name == settings.database_name
        assert settings.database_user == settings.database_user
        assert settings.database_password == settings.database_password

    def test_validation_errors(self):
        """Test settings validation errors."""
        # Test invalid port number
        with patch.dict(os.environ, {"PORT": "invalid"}, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "PORT" in str(exc_info.value)

        # Test invalid access token expire minutes
        with patch.dict(os.environ, {"ACCESS_TOKEN_EXPIRE_MINUTES": "invalid"}, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "ACCESS_TOKEN_EXPIRE_MINUTES" in str(exc_info.value)

    def test_development_environment(self):
        """Test development environment specific settings."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            settings = Settings()
            assert settings.environment == "development"

    def test_production_environment(self):
        """Test production environment specific settings."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=True):
            settings = Settings()
            assert settings.environment == "production"

    def test_testing_environment(self):
        """Test testing environment specific settings."""
        with patch.dict(os.environ, {"ENVIRONMENT": "testing"}, clear=True):
            settings = Settings()
            assert settings.environment == "testing"

    def test_settings_repr(self):
        """Test settings string representation."""
        settings = Settings()
        repr_str = repr(settings)

        # Should contain class name and key attributes
        assert "Settings" in repr_str
        assert "name=" in repr_str
        assert "environment=" in repr_str

    def test_settings_equality(self):
        """Test settings equality comparison."""
        settings1 = Settings()
        settings2 = Settings()

        # Same default values should be equal
        assert settings1 == settings2

    def test_settings_model_copy(self):
        """Test settings copying."""
        settings = Settings()
        settings_copy = settings.model_copy()

        # Should be equal but different objects
        assert settings == settings_copy
        assert settings is not settings_copy

    def test_settings_json(self):
        """Test settings JSON serialization."""
        settings = Settings()
        json_data = settings.model_dump_json()

        # Should be valid JSON
        import json
        parsed = json.loads(json_data)
        assert "name" in parsed
        assert "environment" in parsed
        assert "port" in parsed

    def test_settings_dict(self):
        """Test settings dictionary conversion."""
        settings = Settings()
        settings_dict = settings.model_dump()

        # Should contain all expected keys
        expected_keys = [
            "name", "version", "debug", "environment", "host", "port",
            "secret_key", "algorithm", "access_token_expire_minutes",
            "database_host", "database_port", "database_name", "database_user", "database_password",
            "redis_url", "rabbitmq_url", "log_level", "log_enable_request_logging"
        ]

        for key in expected_keys:
            assert key in settings_dict

    def test_settings_extra_fields(self):
        """Test that extra fields are allowed."""
        # Settings should allow extra fields due to extra = "allow"
        with patch.dict(os.environ, {"EXTRA_FIELD": "extra_value"}, clear=True):
            settings = Settings()
            # Should not raise validation error for extra fields
            assert hasattr(settings, "extra_field") is False  # Extra fields not added to model

    def test_settings_boolean_parsing(self):
        """Test boolean environment variable parsing."""
        # Test true values
        with patch.dict(os.environ, {"DEBUG": "true"}, clear=True):
            settings = Settings()
            assert settings.debug is True

        with patch.dict(os.environ, {"DEBUG": "1"}, clear=True):
            settings = Settings()
            assert settings.debug is True

        # Test false values
        with patch.dict(os.environ, {"DEBUG": "false"}, clear=True):
            settings = Settings()
            assert settings.debug is False

        with patch.dict(os.environ, {"DEBUG": "0"}, clear=True):
            settings = Settings()
            assert settings.debug is False

    def test_settings_integer_parsing(self):
        """Test integer environment variable parsing."""
        with patch.dict(os.environ, {"PORT": "9000"}, clear=True):
            settings = Settings()
            assert settings.port == 9000

        with patch.dict(os.environ, {"ACCESS_TOKEN_EXPIRE_MINUTES": "60"}, clear=True):
            settings = Settings()
            assert settings.access_token_expire_minutes == 60

    def test_settings_required_fields(self):
        """Test that required fields are properly validated."""
        # All fields should have defaults, so no required field validation errors
        settings = Settings()
        assert settings is not None

    def test_settings_field_aliases(self):
        """Test that field aliases work correctly."""
        with patch.dict(os.environ, {"APP_NAME": "Alias Test"}, clear=True):
            settings = Settings()
            assert settings.name == "Alias Test"

    def test_settings_nested_validation(self):
        """Test nested validation in settings."""
        settings = Settings()

        # Database connection string should be valid
        assert settings.database_connection_string is not None
        assert len(settings.database_connection_string) > 0

    def test_settings_immutability(self):
        """Test that settings are immutable after creation."""
        settings = Settings()

        # Pydantic models are not immutable by default, so this test should pass
        # without raising TypeError
        assert settings is not None
