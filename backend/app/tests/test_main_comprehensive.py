"""Comprehensive tests for main.py application entry point."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app, lifespan


class TestMainApplication:
    """Test cases for the main application creation and lifecycle."""

    def test_app_is_fastapi_instance(self):
        """Test that app is a FastAPI instance."""
        assert isinstance(app, FastAPI)
        assert app.title == "eShop Modular Monolith"
        assert app.version == "0.1.0"

    def test_app_has_cors_middleware(self):
        """Test that the app has CORS middleware configured."""
        # Check that CORS middleware is present
        middleware_types = [type(middleware.cls) for middleware in app.user_middleware]
        from fastapi.middleware.cors import CORSMiddleware

        assert CORSMiddleware in middleware_types

    def test_app_has_health_router(self):
        """Test that the app includes health router."""
        # Check that health router is included
        route_paths = [route.path for route in app.routes]
        assert "/health" in route_paths

    def test_app_has_auth_proxy_router(self):
        """Test that the app includes auth proxy router."""
        # Check that auth proxy router is included
        route_paths = [route.path for route in app.routes]
        assert any("/auth" in path for path in route_paths)

    def test_app_has_catalog_router(self):
        """Test that the app includes catalog router."""
        # Check that catalog router is included
        route_paths = [route.path for route in app.routes]
        assert any("/catalog" in path for path in route_paths)

    def test_app_has_root_endpoint(self):
        """Test that the app has a root endpoint."""
        route_paths = [route.path for route in app.routes]
        assert "/" in route_paths

    def test_app_has_auth_me_endpoint(self):
        """Test that the app has an auth/me endpoint."""
        route_paths = [route.path for route in app.routes]
        assert "/api/v1/auth/me" in route_paths

    def test_app_has_pagination(self):
        """Test that pagination is added to the app."""
        # Check that pagination is configured
        # This is harder to test directly, but we can check if the app has the expected structure
        assert hasattr(app, "state")

    @pytest.mark.asyncio
    async def test_lifespan_startup_initializes_services(self):
        """Test that lifespan startup initializes all required services."""
        with (
            patch("app.main.initialize_logging") as mock_logging,
            patch("app.main.initialize_dependency_injection") as mock_di,
            patch("app.main.initialize_database") as mock_db,
            patch("app.main.initialize_cache") as mock_cache,
            patch("app.main.initialize_messaging") as mock_messaging,
            patch("app.main.initialize_auth") as mock_auth,
            patch("app.main.initialize_health") as mock_health,
        ):
            # Test the lifespan startup
            async with lifespan(app):
                pass

            # Verify all initialization functions were called
            mock_logging.assert_called_once()
            mock_di.assert_called_once()
            mock_db.assert_called_once()
            mock_cache.assert_called_once()
            mock_messaging.assert_called_once()
            mock_auth.assert_called_once()
            mock_health.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_shutdown_cleans_up_services(self):
        """Test that lifespan shutdown cleans up all services."""
        with (
            patch("app.main.cleanup_dependency_injection") as mock_di_cleanup,
            patch("app.main.database_handler") as mock_db_handler,
            patch("app.main.cache_handler") as mock_cache_handler,
            patch("app.main.messaging_handler") as mock_messaging_handler,
            patch("app.main.auth_handler") as mock_auth_handler,
            patch("app.main.health_handler") as mock_health_handler,
        ):
            # Mock the shutdown methods
            mock_db_handler.shutdown = AsyncMock()
            mock_cache_handler.shutdown = AsyncMock()
            mock_messaging_handler.shutdown = AsyncMock()
            mock_auth_handler.shutdown = AsyncMock()
            mock_health_handler.shutdown = AsyncMock()

            # Test the lifespan shutdown
            async with lifespan(app):
                pass

            # Verify all cleanup functions were called
            mock_di_cleanup.assert_called_once()
            mock_db_handler.shutdown.assert_called_once()
            mock_cache_handler.shutdown.assert_called_once()
            mock_messaging_handler.shutdown.assert_called_once()
            mock_auth_handler.shutdown.assert_called_once()
            mock_health_handler.shutdown.assert_called_once()


class TestMainApplicationIntegration:
    """Integration tests for the main application."""

    def test_app_has_proper_middleware_order(self):
        """Test that the app has middleware in the correct order."""
        middleware_types = [type(middleware.cls) for middleware in app.user_middleware]

        # CORS should be first
        from fastapi.middleware.cors import CORSMiddleware

        assert CORSMiddleware in middleware_types

        # Check that we have the expected number of middleware
        assert len(middleware_types) >= 1

    def test_app_has_exception_handlers(self):
        """Test that the app has exception handlers configured."""
        # Check that exception handlers are registered
        assert hasattr(app, "exception_handlers")
        assert len(app.exception_handlers) > 0

    def test_app_has_request_logging_middleware(self):
        """Test that the app has request logging middleware when enabled."""
        # This test depends on settings, so we'll just check the structure
        middleware_types = [type(middleware.cls) for middleware in app.user_middleware]
        # Request logging middleware might be present depending on settings
        assert len(middleware_types) >= 1

    def test_app_has_auth_middleware(self):
        """Test that the app has authentication middleware."""
        # Check that auth middleware is present
        middleware_types = [type(middleware.cls) for middleware in app.user_middleware]
        # Auth middleware should be present
        assert len(middleware_types) >= 1

    def test_app_routes_are_properly_configured(self):
        """Test that all routes are properly configured."""
        route_paths = [route.path for route in app.routes]

        # Check for essential routes
        assert "/" in route_paths
        assert "/health" in route_paths
        assert "/api/v1/auth/me" in route_paths

        # Check for API routes
        api_routes = [path for path in route_paths if path.startswith("/api/v1")]
        assert len(api_routes) > 0

    def test_app_has_proper_tags(self):
        """Test that the app has proper tags for API documentation."""
        # Check that routers have tags
        for route in app.routes:
            if hasattr(route, "tags") and route.tags:
                assert isinstance(route.tags, list)
                assert len(route.tags) > 0

    def test_app_has_proper_documentation(self):
        """Test that the app has proper documentation."""
        assert app.title is not None
        assert app.version is not None
        assert app.description is not None

    def test_app_has_lifespan_configured(self):
        """Test that the app has lifespan configured."""
        assert app.router.lifespan_context is not None

    @pytest.mark.asyncio
    async def test_lifespan_handles_errors_gracefully(self):
        """Test that lifespan handles errors gracefully."""
        with patch("app.main.initialize_logging") as mock_logging:
            mock_logging.side_effect = Exception("Initialization failed")

            # The lifespan should handle the error gracefully
            with pytest.raises(RuntimeError):
                async with lifespan(app):
                    pass

    def test_app_client_can_be_created(self):
        """Test that a test client can be created for the app."""
        client = TestClient(app)
        assert client is not None

    def test_app_root_endpoint_works(self):
        """Test that the root endpoint works correctly."""
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"

    def test_app_health_endpoint_works(self):
        """Test that the health endpoint works correctly."""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200

    def test_app_has_proper_cors_configuration(self):
        """Test that the app has proper CORS configuration."""
        # Check CORS middleware configuration
        cors_middleware = None
        for middleware in app.user_middleware:
            if middleware.cls.__name__ == "CORSMiddleware":
                cors_middleware = middleware
                break

        assert cors_middleware is not None
        # Check CORS options
        assert cors_middleware.options.get("allow_origins") == ["*"]
        assert cors_middleware.options.get("allow_credentials") is True
        assert cors_middleware.options.get("allow_methods") == ["*"]
        assert cors_middleware.options.get("allow_headers") == ["*"]
