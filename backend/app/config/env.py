"""Environment variable configuration with fallback strategy."""

import os
from pathlib import Path
from typing import Any


class EnvConfig:
    """Environment configuration with fallback strategy.

    Priority order (highest to lowest):
    1. os.environ (system/production environment variables)
    2. .env file (local development configuration)
    3. launch.json environment variables (VS Code debug convenience)
    4. Default value or raise error

    Rationale:
    - Follows 12-Factor App methodology (environment variables are primary config)
    - Production-safe: System env vars always take precedence
    - Docker/Kubernetes friendly: Container env vars override local config
    - .env file is for local development convenience only
    - launch.json is lowest priority (IDE debugging convenience)
    """

    def __init__(self):
        self._env_file_path = Path(__file__).parent.parent.parent / ".env"
        self._launch_json_path = (
            Path(__file__).parent.parent.parent.parent / ".vscode" / "launch.json"
        )
        self._launch_env = self._load_launch_json_env()

    def _load_launch_json_env(self) -> dict[str, str]:
        """Load environment variables from launch.json if available."""
        try:
            import json

            if self._launch_json_path.exists():
                with open(self._launch_json_path) as f:
                    data = json.load(f)

                # Find the first backend configuration and extract env
                for config in data.get("configurations", []):
                    if "backend" in config.get("name", "").lower():
                        return config.get("env", {})
        except Exception:
            pass
        return {}

    def _load_env_file(self) -> dict[str, str]:
        """Load environment variables from .env file."""
        env_vars = {}
        if self._env_file_path.exists():
            try:
                with open(self._env_file_path) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            env_vars[key.strip()] = value.strip()
            except Exception:
                pass
        return env_vars

    def get(self, key: str, default: Any | None = None) -> str:
        """Get environment variable with standard fallback strategy.

        Priority order (highest to lowest):
        1. os.environ - System/production environment variables (HIGHEST)
        2. .env file - Local development configuration
        3. launch.json - VS Code debug convenience (LOWEST)
        4. default - Fallback value

        Args:
            key: Environment variable key
            default: Default value if not found anywhere

        Returns:
            Environment variable value

        Raises:
            ValueError: If no value found and no default provided
        """
        # 1. Check os.environ FIRST (highest priority - production/system env vars)
        if key in os.environ:
            return os.environ[key]

        # 2. Check .env file (local development)
        env_file_vars = self._load_env_file()
        if key in env_file_vars:
            return env_file_vars[key]

        # 3. Check launch.json (lowest priority - IDE convenience)
        if key in self._launch_env:
            return self._launch_env[key]

        # 4. Check with common variations (same priority order)
        variations = [
            key.upper(),
            key.lower(),
            key.replace("_", ""),
            key.replace("-", "_"),
            key.replace("_", "-"),
        ]

        for var_key in variations:
            # Check os.environ first
            if var_key in os.environ:
                return os.environ[var_key]
            # Then .env file
            if var_key in env_file_vars:
                return env_file_vars[var_key]
            # Finally launch.json
            if var_key in self._launch_env:
                return self._launch_env[var_key]

        # 5. Return default or fail
        if default is not None:
            return str(default)

        raise ValueError(
            f"Environment variable '{key}' not found in any source (os.environ, .env, launch.json)"
        )

    def get_bool(self, key: str, default: bool | None = None) -> bool:
        """Get boolean environment variable."""
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        return str(value).lower() in ("true", "1", "yes", "on")

    def get_int(self, key: str, default: int | None = None) -> int:
        """Get integer environment variable."""
        value = self.get(key, default)
        if isinstance(value, int):
            return value
        return int(value)

    def get_float(self, key: str, default: float | None = None) -> float:
        """Get float environment variable."""
        value = self.get(key, default)
        if isinstance(value, float):
            return value
        return float(value)

    def get_list(
        self, key: str, default: list | None = None, separator: str = ","
    ) -> list[str]:
        """Get list environment variable."""
        value = self.get(key, default)
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [item.strip() for item in value.split(separator) if item.strip()]
        return default or []

    def has(self, key: str) -> bool:
        """Check if environment variable exists in any source."""
        try:
            self.get(key)
            return True
        except ValueError:
            return False

    def all(self) -> dict[str, str]:
        """Get all environment variables from all sources.

        Variables are merged with correct priority order:
        - Start with launch.json (lowest priority)
        - Override with .env file
        - Override with os.environ (highest priority - takes precedence)
        """
        all_vars = {}

        # Start with launch.json (lowest priority)
        all_vars.update(self._launch_env)

        # Override with .env file
        env_file_vars = self._load_env_file()
        all_vars.update(env_file_vars)

        # Override with os.environ (highest priority)
        all_vars.update(os.environ)

        return all_vars


# Global environment configuration instance
env_config = EnvConfig()


def get_env(key: str, default: Any | None = None) -> str:
    """Get environment variable with fallback strategy."""
    return env_config.get(key, default)


def get_env_bool(key: str, default: bool | None = None) -> bool:
    """Get boolean environment variable."""
    return env_config.get_bool(key, default)


def get_env_int(key: str, default: int | None = None) -> int:
    """Get integer environment variable."""
    return env_config.get_int(key, default)


def get_env_float(key: str, default: float | None = None) -> float:
    """Get float environment variable."""
    return env_config.get_float(key, default)


def get_env_list(
    key: str, default: list | None = None, separator: str = ","
) -> list[str]:
    """Get list environment variable."""
    return env_config.get_list(key, default, separator)


def has_env(key: str) -> bool:
    """Check if environment variable exists."""
    return env_config.has(key)


def get_all_env() -> dict[str, str]:
    """Get all environment variables from all sources."""
    return env_config.all()
