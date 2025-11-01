"""Comprehensive tests for environment configuration module."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from app.config.env import (
    EnvConfig,
    env_config,
    get_all_env,
    get_env,
    get_env_bool,
    get_env_float,
    get_env_int,
    get_env_list,
    has_env,
)


class TestEnvConfig:
    """Test EnvConfig class."""

    def test_get_from_os_environ(self):
        """Test getting environment variable from os.environ."""
        os.environ["TEST_VAR"] = "test_value"

        config = EnvConfig()
        value = config.get("TEST_VAR")

        assert value == "test_value"
        del os.environ["TEST_VAR"]

    def test_get_from_env_file(self, tmp_path, monkeypatch):
        """Test getting environment variable from .env file."""
        # Create temporary .env file
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=env_file_value\n")

        # Mock the path to point to our temporary file
        monkeypatch.setattr(
            "app.config.env.EnvConfig._env_file_path", env_file
        )

        config = EnvConfig()
        value = config.get("TEST_VAR")

        assert value == "env_file_value"

    def test_get_from_launch_json(self, tmp_path, monkeypatch):
        """Test getting environment variable from launch.json."""
        # Create temporary launch.json
        launch_json = tmp_path / ".vscode" / "launch.json"
        launch_json.parent.mkdir(parents=True)
        launch_json.write_text(
            json.dumps(
                {
                    "configurations": [
                        {
                            "name": "backend",
                            "env": {"TEST_VAR": "launch_json_value"},
                        }
                    ]
                }
            )
        )

        # Mock the path
        monkeypatch.setattr(
            "app.config.env.EnvConfig._launch_json_path", launch_json
        )

        config = EnvConfig()
        value = config.get("TEST_VAR")

        assert value == "launch_json_value"

    def test_get_priority_order(self, tmp_path, monkeypatch):
        """Test that os.environ takes priority over .env file."""
        # Set in both os.environ and .env file
        os.environ["PRIORITY_TEST"] = "os_environ_value"

        env_file = tmp_path / ".env"
        env_file.write_text("PRIORITY_TEST=env_file_value\n")

        monkeypatch.setattr(
            "app.config.env.EnvConfig._env_file_path", env_file
        )

        config = EnvConfig()
        value = config.get("PRIORITY_TEST")

        # os.environ should take priority
        assert value == "os_environ_value"

        del os.environ["PRIORITY_TEST"]

    def test_get_with_default(self):
        """Test getting environment variable with default value."""
        config = EnvConfig()
        value = config.get("NONEXISTENT_VAR", default="default_value")

        assert value == "default_value"

    def test_get_raises_error_without_default(self):
        """Test that get raises error when variable not found and no default."""
        config = EnvConfig()

        with pytest.raises(ValueError, match="not found"):
            config.get("NONEXISTENT_VAR_NO_DEFAULT")

    def test_get_bool(self):
        """Test get_bool method."""
        config = EnvConfig()

        # Test true values
        for true_val in ["true", "True", "TRUE", "1", "yes", "on"]:
            value = config.get_bool("TEST_BOOL", default=true_val)
            assert value is True

        # Test false values
        for false_val in ["false", "False", "FALSE", "0", "no", "off"]:
            value = config.get_bool("TEST_BOOL", default=false_val)
            assert value is False

    def test_get_int(self):
        """Test get_int method."""
        config = EnvConfig()
        value = config.get_int("TEST_INT", default="123")

        assert value == 123
        assert isinstance(value, int)

    def test_get_float(self):
        """Test get_float method."""
        config = EnvConfig()
        value = config.get_float("TEST_FLOAT", default="123.45")

        assert value == 123.45
        assert isinstance(value, float)

    def test_get_list(self):
        """Test get_list method."""
        config = EnvConfig()

        # Test with comma separator
        value = config.get_list("TEST_LIST", default="item1,item2,item3")
        assert value == ["item1", "item2", "item3"]

        # Test with custom separator
        value = config.get_list("TEST_LIST", default="item1|item2|item3", separator="|")
        assert value == ["item1", "item2", "item3"]

        # Test with empty string
        value = config.get_list("TEST_LIST", default="")
        assert value == []

    def test_has(self):
        """Test has method."""
        config = EnvConfig()

        # Test with existing variable
        os.environ["HAS_TEST_VAR"] = "test"
        assert config.has("HAS_TEST_VAR") is True
        del os.environ["HAS_TEST_VAR"]

        # Test with non-existent variable
        assert config.has("NONEXISTENT_VAR") is False

    def test_all(self):
        """Test all method returns merged environment variables."""
        config = EnvConfig()

        # Set a variable in os.environ
        os.environ["ALL_TEST_VAR"] = "os_value"

        all_vars = config.all()

        assert "ALL_TEST_VAR" in all_vars
        assert all_vars["ALL_TEST_VAR"] == "os_value"

        del os.environ["ALL_TEST_VAR"]

    def test_variations(self):
        """Test that get checks variations of key names."""
        os.environ["test_var_upper"] = "upper_value"
        config = EnvConfig()

        # Test with different case
        value = config.get("TEST_VAR_UPPER")
        assert value == "upper_value"

        del os.environ["test_var_upper"]


class TestEnvConfigEdgeCases:
    """Test edge cases for EnvConfig."""

    def test_env_file_with_comments(self, tmp_path, monkeypatch):
        """Test that .env file parsing ignores comments."""
        env_file = tmp_path / ".env"
        env_file.write_text("# This is a comment\nTEST_VAR=value\n# Another comment\n")

        monkeypatch.setattr(
            "app.config.env.EnvConfig._env_file_path", env_file
        )

        config = EnvConfig()
        value = config.get("TEST_VAR")

        assert value == "value"

    def test_env_file_with_empty_lines(self, tmp_path, monkeypatch):
        """Test that .env file parsing handles empty lines."""
        env_file = tmp_path / ".env"
        env_file.write_text("\nTEST_VAR=value\n\n")

        monkeypatch.setattr(
            "app.config.env.EnvConfig._env_file_path", env_file
        )

        config = EnvConfig()
        value = config.get("TEST_VAR")

        assert value == "value"

    def test_env_file_with_multiple_equals(self, tmp_path, monkeypatch):
        """Test that .env file parsing handles values with equals signs."""
        env_file = tmp_path / ".env"
        env_file.write_text('TEST_VAR=value=with=equals\n')

        monkeypatch.setattr(
            "app.config.env.EnvConfig._env_file_path", env_file
        )

        config = EnvConfig()
        value = config.get("TEST_VAR")

        assert value == "value=with=equals"

    def test_launch_json_malformed(self, tmp_path, monkeypatch):
        """Test that malformed launch.json doesn't crash."""
        launch_json = tmp_path / ".vscode" / "launch.json"
        launch_json.parent.mkdir(parents=True)
        launch_json.write_text("invalid json{")

        monkeypatch.setattr(
            "app.config.env.EnvConfig._launch_json_path", launch_json
        )

        # Should not raise an exception
        config = EnvConfig()
        # Should fall back to default or raise ValueError
        with pytest.raises(ValueError):
            config.get("NONEXISTENT_VAR")


class TestModuleFunctions:
    """Test module-level convenience functions."""

    def test_get_env(self):
        """Test get_env function."""
        os.environ["MODULE_TEST_VAR"] = "module_test_value"
        value = get_env("MODULE_TEST_VAR")
        assert value == "module_test_value"
        del os.environ["MODULE_TEST_VAR"]

    def test_get_env_bool(self):
        """Test get_env_bool function."""
        value = get_env_bool("MODULE_TEST_BOOL", default="true")
        assert value is True

    def test_get_env_int(self):
        """Test get_env_int function."""
        value = get_env_int("MODULE_TEST_INT", default="456")
        assert value == 456

    def test_get_env_float(self):
        """Test get_env_float function."""
        value = get_env_float("MODULE_TEST_FLOAT", default="789.12")
        assert value == 789.12

    def test_get_env_list(self):
        """Test get_env_list function."""
        value = get_env_list("MODULE_TEST_LIST", default="a,b,c")
        assert value == ["a", "b", "c"]

    def test_has_env(self):
        """Test has_env function."""
        os.environ["MODULE_HAS_TEST"] = "test"
        assert has_env("MODULE_HAS_TEST") is True
        del os.environ["MODULE_HAS_TEST"]

    def test_get_all_env(self):
        """Test get_all_env function."""
        os.environ["MODULE_ALL_TEST"] = "test"
        all_vars = get_all_env()
        assert "MODULE_ALL_TEST" in all_vars
        del os.environ["MODULE_ALL_TEST"]

