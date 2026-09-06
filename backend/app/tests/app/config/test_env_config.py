"""Tests for environment configuration."""

from pathlib import Path

from app.config.env import EnvConfig


class TestEnvConfig:
    def test_get_with_default(self, monkeypatch) -> None:
        monkeypatch.delenv("NONEXISTENT_TEST_VAR_XYZ", raising=False)
        config = EnvConfig()
        assert config.get("NONEXISTENT_TEST_VAR_XYZ", default="fallback") == "fallback"

    def test_get_from_environ(self, monkeypatch) -> None:
        monkeypatch.setenv("ESHOP_TEST_VAR", "from-env")
        config = EnvConfig()
        assert config.get("ESHOP_TEST_VAR") == "from-env"

    def test_find_env_file_prefers_backend(self, tmp_path: Path) -> None:
        backend_dir = tmp_path / "backend"
        backend_dir.mkdir()
        (backend_dir / ".env").write_text("KEY=value\n", encoding="utf-8")
        project_root = tmp_path
        path = EnvConfig._find_env_file(backend_dir, project_root)
        assert path == backend_dir / ".env"

    def test_get_bool_and_int(self, monkeypatch) -> None:
        monkeypatch.setenv("BOOL_VAR", "true")
        monkeypatch.setenv("INT_VAR", "42")
        config = EnvConfig()
        assert config.get_bool("BOOL_VAR") is True
        assert config.get_int("INT_VAR") == 42

    def test_module_helpers(self, monkeypatch) -> None:
        from app.config import env as env_module

        monkeypatch.setenv("LIST_VAR", "a,b,c")
        assert env_module.get_env_list("LIST_VAR") == ["a", "b", "c"]
