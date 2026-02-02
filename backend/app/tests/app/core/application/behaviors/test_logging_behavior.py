"""Tests for logging behavior."""

import importlib.util
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import directly from file to avoid circular import issues
# Use absolute path to avoid path calculation issues
# Test file is at: backend/app/tests/app/core/application/behaviors/test_logging_behavior.py
# Target file is at: backend/app/core/application/behaviors/logging_behavior.py
# Need to go up 7 levels to get to backend/, then add app/core/...
logging_behavior_path = Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent / "app" / "core" / "application" / "behaviors" / "logging_behavior.py"

spec = importlib.util.spec_from_file_location(
    "logging_behavior",
    logging_behavior_path,
)
logging_behavior_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logging_behavior_module)  # type: ignore[union-attr]
LoggingBehavior = logging_behavior_module.LoggingBehavior


class TestLoggingBehavior:
    """Test LoggingBehavior."""

    @pytest.fixture
    def logging_behavior(self) -> LoggingBehavior:
        """Provide LoggingBehavior instance."""
        return LoggingBehavior()

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """Provide mock logger."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_handle_logs_start_and_completion(
        self,
        logging_behavior: LoggingBehavior,
        mock_logger: MagicMock,
    ) -> None:
        """Test that handle logs start and completion."""
        with patch.object(logging_behavior, "logger", mock_logger), patch(
            "app.core.application.behaviors.logging_behavior.get_trace_id",
            return_value="trace-123",
        ), patch(
            "app.core.application.behaviors.logging_behavior.get_request_id",
            return_value="request-456",
        ):
            mock_request = MagicMock()
            mock_request.__class__.__name__ = "TestCommand"
            
            next_handler = AsyncMock(return_value=MagicMock())
            
            await logging_behavior.handle(mock_request, next_handler)
            
            # Verify logs were called
            assert mock_logger.log_with_context.call_count >= 2
            
            # Check start log
            start_call = mock_logger.log_with_context.call_args_list[0]
            assert "Starting request handling" in start_call[0][0]
            assert start_call[1]["context"]["request_type"] == "TestCommand"
            assert start_call[1]["context"]["trace_id"] == "trace-123"
            assert start_call[1]["context"]["request_id"] == "request-456"
            
            # Check completion log
            complete_call = mock_logger.log_with_context.call_args_list[1]
            assert "Request handling completed" in complete_call[0][0]
            assert "elapsed_time" in complete_call[1]["context"]

    @pytest.mark.asyncio
    async def test_handle_logs_performance_warning(
        self,
        logging_behavior: LoggingBehavior,
        mock_logger: MagicMock,
    ) -> None:
        """Test that handle logs performance warning for slow requests."""
        with patch.object(logging_behavior, "logger", mock_logger), patch(
            "app.core.application.behaviors.logging_behavior.get_trace_id",
            return_value="trace-123",
        ), patch(
            "app.core.application.behaviors.logging_behavior.get_request_id",
            return_value="request-456",
        ), patch("time.time", side_effect=[0, 4]):  # 4 seconds elapsed
            mock_request = MagicMock()
            mock_request.__class__.__name__ = "TestCommand"
            
            next_handler = AsyncMock(return_value=MagicMock())
            
            await logging_behavior.handle(mock_request, next_handler)
            
            # Verify performance warning was logged
            mock_logger.log_warning_with_context.assert_called_once()
            warning_call = mock_logger.log_warning_with_context.call_args
            assert "Request performance warning" in warning_call[0][0]
            assert warning_call[1]["context"]["elapsed_time"] > 3

    @pytest.mark.asyncio
    async def test_handle_logs_errors(
        self,
        logging_behavior: LoggingBehavior,
        mock_logger: MagicMock,
    ) -> None:
        """Test that handle logs errors."""
        with patch.object(logging_behavior, "logger", mock_logger), patch(
            "app.core.application.behaviors.logging_behavior.get_trace_id",
            return_value="trace-123",
        ), patch(
            "app.core.application.behaviors.logging_behavior.get_request_id",
            return_value="request-456",
        ):
            mock_request = MagicMock()
            mock_request.__class__.__name__ = "TestCommand"
            
            test_exception = ValueError("Test error")
            next_handler = AsyncMock(side_effect=test_exception)
            
            with pytest.raises(ValueError, match="Test error"):
                await logging_behavior.handle(mock_request, next_handler)
            
            # Verify error was logged
            mock_logger.log_error_with_context.assert_called_once()
            error_call = mock_logger.log_error_with_context.call_args
            assert "Request handling failed" in error_call[0][0]
            assert error_call[1]["error"] == test_exception

    @pytest.mark.asyncio
    async def test_handle_measures_elapsed_time(
        self,
        logging_behavior: LoggingBehavior,
        mock_logger: MagicMock,
    ) -> None:
        """Test that handle measures elapsed time."""
        with patch.object(logging_behavior, "logger", mock_logger), patch(
            "app.core.application.behaviors.logging_behavior.get_trace_id",
            return_value=None,
        ), patch(
            "app.core.application.behaviors.logging_behavior.get_request_id",
            return_value=None,
        ):
            mock_request = MagicMock()
            mock_request.__class__.__name__ = "TestCommand"
            
            # Simulate some processing time
            async def slow_handler():
                await asyncio.sleep(0.1)
                return MagicMock()
            
            import asyncio
            next_handler = slow_handler
            
            await logging_behavior.handle(mock_request, next_handler)
            
            # Verify elapsed time was logged
            complete_call = mock_logger.log_with_context.call_args_list[1]
            elapsed_time = complete_call[1]["context"]["elapsed_time"]
            assert elapsed_time >= 0.1

    def test_get_response_type_from_query(
        self, logging_behavior: LoggingBehavior
    ) -> None:
        """Test _get_response_type for Query requests."""
        class TestQuery:
            pass
        
        mock_request = TestQuery()
        response_type = logging_behavior._get_response_type(mock_request)
        
        assert response_type == "TestResult"

    def test_get_response_type_from_command(
        self, logging_behavior: LoggingBehavior
    ) -> None:
        """Test _get_response_type for Command requests."""
        class TestCommand:
            pass
        
        mock_request = TestCommand()
        response_type = logging_behavior._get_response_type(mock_request)
        
        assert response_type == "TestResult"

    def test_get_response_type_fallback(
        self, logging_behavior: LoggingBehavior
    ) -> None:
        """Test _get_response_type fallback."""
        class TestRequest:
            pass
        
        mock_request = TestRequest()
        response_type = logging_behavior._get_response_type(mock_request)
        
        assert response_type == "Response"

    @pytest.mark.asyncio
    async def test_handle_with_none_trace_context(
        self,
        logging_behavior: LoggingBehavior,
        mock_logger: MagicMock,
    ) -> None:
        """Test handle with None trace context."""
        with patch.object(logging_behavior, "logger", mock_logger), patch(
            "app.core.application.behaviors.logging_behavior.get_trace_id",
            return_value=None,
        ), patch(
            "app.core.application.behaviors.logging_behavior.get_request_id",
            return_value=None,
        ):
            mock_request = MagicMock()
            mock_request.__class__.__name__ = "TestCommand"
            
            next_handler = AsyncMock(return_value=MagicMock())
            
            await logging_behavior.handle(mock_request, next_handler)
            
            # Should still log successfully
            assert mock_logger.log_with_context.call_count >= 2
