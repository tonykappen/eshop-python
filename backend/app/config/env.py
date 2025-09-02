"""Environment variable configuration with fallback strategy."""

import os
from typing import Any, Optional
from pathlib import Path


class EnvConfig:
    """Environment configuration with fallback strategy.
    
    Fallback order:
    1. launch.json environment variables (if running in VS Code)
    2. .env file
    3. os.environ
    4. Fail if no value found
    """
    
    def __init__(self):
        self._env_file_path = Path(__file__).parent.parent.parent / ".env"
        self._launch_json_path = Path(__file__).parent.parent.parent.parent / ".vscode" / "launch.json"
        self._launch_env = self._load_launch_json_env()
    
    def _load_launch_json_env(self) -> dict[str, str]:
        """Load environment variables from launch.json if available."""
        try:
            import json
            if self._launch_json_path.exists():
                with open(self._launch_json_path, 'r') as f:
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
                with open(self._env_file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
            except Exception:
                pass
        return env_vars
    
    def get(self, key: str, default: Optional[Any] = None) -> str:
        """Get environment variable with fallback strategy.
        
        Args:
            key: Environment variable key
            default: Default value if not found anywhere
            
        Returns:
            Environment variable value
            
        Raises:
            ValueError: If no value found and no default provided
        """
        # 1. Check launch.json environment variables
        if key in self._launch_env:
            return self._launch_env[key]
        
        # 2. Check .env file
        env_file_vars = self._load_env_file()
        if key in env_file_vars:
            return env_file_vars[key]
        
        # 3. Check os.environ
        if key in os.environ:
            return os.environ[key]
        
        # 4. Check with common variations
        variations = [
            key.upper(),
            key.lower(),
            key.replace('_', ''),
            key.replace('-', '_'),
            key.replace('_', '-')
        ]
        
        for var_key in variations:
            if var_key in self._launch_env:
                return self._launch_env[var_key]
            if var_key in env_file_vars:
                return env_file_vars[var_key]
            if var_key in os.environ:
                return os.environ[var_key]
        
        # 5. Return default or fail
        if default is not None:
            return str(default)
        
        raise ValueError(f"Environment variable '{key}' not found in any source (launch.json, .env, os.environ)")
    
    def get_bool(self, key: str, default: Optional[bool] = None) -> bool:
        """Get boolean environment variable."""
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        return str(value).lower() in ('true', '1', 'yes', 'on')
    
    def get_int(self, key: str, default: Optional[int] = None) -> int:
        """Get integer environment variable."""
        value = self.get(key, default)
        if isinstance(value, int):
            return value
        return int(value)
    
    def get_float(self, key: str, default: Optional[float] = None) -> float:
        """Get float environment variable."""
        value = self.get(key, default)
        if isinstance(value, float):
            return value
        return float(value)
    
    def get_list(self, key: str, default: Optional[list] = None, separator: str = ',') -> list[str]:
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
        """Get all environment variables from all sources."""
        all_vars = {}
        
        # Start with os.environ
        all_vars.update(os.environ)
        
        # Override with .env file
        env_file_vars = self._load_env_file()
        all_vars.update(env_file_vars)
        
        # Override with launch.json (highest priority)
        all_vars.update(self._launch_env)
        
        return all_vars


# Global environment configuration instance
env_config = EnvConfig()


def get_env(key: str, default: Optional[Any] = None) -> str:
    """Get environment variable with fallback strategy."""
    return env_config.get(key, default)


def get_env_bool(key: str, default: Optional[bool] = None) -> bool:
    """Get boolean environment variable."""
    return env_config.get_bool(key, default)


def get_env_int(key: str, default: Optional[int] = None) -> int:
    """Get integer environment variable."""
    return env_config.get_int(key, default)


def get_env_float(key: str, default: Optional[float] = None) -> float:
    """Get float environment variable."""
    return env_config.get_float(key, default)


def get_env_list(key: str, default: Optional[list] = None, separator: str = ',') -> list[str]:
    """Get list environment variable."""
    return env_config.get_list(key, default, separator)


def has_env(key: str) -> bool:
    """Check if environment variable exists."""
    return env_config.has(key)


def get_all_env() -> dict[str, str]:
    """Get all environment variables from all sources."""
    return env_config.all()
