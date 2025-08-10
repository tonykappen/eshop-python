"""Comprehensive tests for middleware behaviors."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eshop.core.middleware.behaviors import (
    AuditableEntityInterceptor,
    DispatchDomainEventsInterceptor,
    PerformanceLoggingMixin,
    auto_log_async,
    auto_log_database_operation,
    auto_log_sync,
    logging_behavior,
    validation_behavior,
)


class TestLoggingBehavior:
    """Test logging behavior decorator."""

    @pytest.mark.asyncio
    async def test_logging_behavior_success(self) -> None:
        """Test logging behavior with successful execution."""
        mock_logger = MagicMock()

        @logging_behavior
        async def test_function() -> str:
            return "success"

        with patch(
            "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
        ):
            result = await test_function()

            assert result == "success"
            assert mock_logger.info.call_count == 2  # Start and complete
            assert mock_logger.error.call_count == 0

            # Check start log
            start_call = mock_logger.info.call_args_list[0]
            assert "Starting test_function" in start_call[0][0]
            assert start_call[1]["extra"]["function"] == "test_function"

            # Check complete log
            complete_call = mock_logger.info.call_args_list[1]
            assert "Completed test_function" in complete_call[0][0]
            assert complete_call[1]["extra"]["function"] == "test_function"
            assert "execution_time" in complete_call[1]["extra"]

    @pytest.mark.asyncio
    async def test_logging_behavior_exception(self) -> None:
        """Test logging behavior with exception."""
        mock_logger = MagicMock()

        @logging_behavior
        async def test_function() -> str:
            raise ValueError("Test error")

        with patch(
            "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
        ):
            with pytest.raises(ValueError, match="Test error"):
                await test_function()

            assert mock_logger.info.call_count == 1  # Start only
            assert mock_logger.error.call_count == 1  # Error log

            # Check error log
            error_call = mock_logger.error.call_args
            assert "Error in test_function" in error_call[0][0]
            assert error_call[1]["extra"]["function"] == "test_function"
            assert error_call[1]["extra"]["error"] == "Test error"
            assert "execution_time" in error_call[1]["extra"]

    @pytest.mark.asyncio
    async def test_logging_behavior_with_arguments(self) -> None:
        """Test logging behavior with function arguments."""
        mock_logger = MagicMock()

        @logging_behavior
        async def test_function(arg1: str, arg2: int, kwarg: str = "default") -> str:
            return f"{arg1}_{arg2}_{kwarg}"

        with patch(
            "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
        ):
            result = await test_function("test", 42, kwarg="custom")

            assert result == "test_42_custom"
            assert mock_logger.info.call_count == 2


class TestValidationBehavior:
    """Test validation behavior decorator."""

    @pytest.mark.asyncio
    async def test_validation_behavior_success(self) -> None:
        """Test validation behavior with successful execution."""
        mock_logger = MagicMock()

        @validation_behavior
        async def test_function() -> str:
            return "success"

        with patch(
            "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
        ):
            result = await test_function()

            assert result == "success"
            assert mock_logger.debug.call_count == 2  # Input and output validation

            # Check input validation log
            input_call = mock_logger.debug.call_args_list[0]
            assert "Validating input for test_function" in input_call[0][0]

            # Check output validation log
            output_call = mock_logger.debug.call_args_list[1]
            assert "Validating output for test_function" in output_call[0][0]

    @pytest.mark.asyncio
    async def test_validation_behavior_with_annotations(self) -> None:
        """Test validation behavior with function annotations."""
        mock_logger = MagicMock()

        @validation_behavior
        async def test_function(name: str, age: int) -> str:
            return f"{name}_{age}"

        with patch(
            "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
        ):
            result = await test_function("test", 25)

            assert result == "test_25"
            assert mock_logger.debug.call_count == 2

    @pytest.mark.asyncio
    async def test_validation_behavior_without_annotations(self) -> None:
        """Test validation behavior without function annotations."""
        mock_logger = MagicMock()

        @validation_behavior
        async def test_function(*_args, **_kwargs):
            return "success"

        with patch(
            "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
        ):
            result = await test_function("arg1", kwarg="value")

            assert result == "success"
            assert mock_logger.debug.call_count == 2


class TestAuditableEntityInterceptor:
    """Test auditable entity interceptor."""

    def test_auditable_entity_interceptor_initialization(self) -> None:
        """Test AuditableEntityInterceptor initialization."""
        mock_logger = MagicMock()

        with patch(
            "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
        ):
            interceptor = AuditableEntityInterceptor()

            assert interceptor.logger == mock_logger

    @pytest.mark.asyncio
    async def test_before_save(self) -> None:
        """Test before_save method."""
        mock_logger = MagicMock()
        mock_entity = MagicMock()
        mock_entity.__class__.__name__ = "TestEntity"

        with patch(
            "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
        ):
            interceptor = AuditableEntityInterceptor()
            await interceptor.before_save(mock_entity)

            mock_logger.debug.assert_called_once_with("Before save: TestEntity")

    @pytest.mark.asyncio
    async def test_after_save(self) -> None:
        """Test after_save method."""
        mock_logger = MagicMock()
        mock_entity = MagicMock()
        mock_entity.__class__.__name__ = "TestEntity"

        with patch(
            "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
        ):
            interceptor = AuditableEntityInterceptor()
            await interceptor.after_save(mock_entity)

            mock_logger.debug.assert_called_once_with("After save: TestEntity")


class TestDispatchDomainEventsInterceptor:
    """Test dispatch domain events interceptor."""

    def test_dispatch_domain_events_interceptor_initialization(self) -> None:
        """Test DispatchDomainEventsInterceptor initialization."""
        mock_logger = MagicMock()
        mock_event_publisher = MagicMock()

        with patch(
            "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
        ):
            interceptor = DispatchDomainEventsInterceptor(mock_event_publisher)

            assert interceptor.event_publisher == mock_event_publisher
            assert interceptor.logger == mock_logger

    @pytest.mark.asyncio
    async def test_dispatch_events_with_events(self) -> None:
        """Test dispatch_events with domain events."""
        mock_logger = MagicMock()
        mock_event_publisher = MagicMock()
        mock_event_publisher.publish_domain_event = AsyncMock()

        mock_entity = MagicMock()
        mock_entity.__class__.__name__ = "TestEntity"
        mock_entity.domain_events = [MagicMock(), MagicMock()]
        mock_entity.clear_domain_events = MagicMock()

        with (
            patch(
                "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
            ),
            patch("eshop.core.middleware.behaviors.AutoLogContext") as mock_context,
        ):
            mock_context.return_value.__aenter__ = AsyncMock()
            mock_context.return_value.__aexit__ = AsyncMock()

            interceptor = DispatchDomainEventsInterceptor(mock_event_publisher)
            await interceptor.dispatch_events(mock_entity)

            # Check that events were published
            assert mock_event_publisher.publish_domain_event.call_count == 2

            # Check that domain events were cleared
            mock_entity.clear_domain_events.assert_called_once()

            # Check logging
            mock_logger.debug.assert_called_with("Dispatching event: MagicMock")

    @pytest.mark.asyncio
    async def test_dispatch_events_without_events(self) -> None:
        """Test dispatch_events without domain events."""
        mock_logger = MagicMock()
        mock_event_publisher = MagicMock()
        mock_event_publisher.publish_domain_event = AsyncMock()

        mock_entity = MagicMock()
        mock_entity.__class__.__name__ = "TestEntity"
        mock_entity.domain_events = []
        mock_entity.clear_domain_events = MagicMock()

        with patch(
            "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
        ):
            interceptor = DispatchDomainEventsInterceptor(mock_event_publisher)
            await interceptor.dispatch_events(mock_entity)

            # Check that no events were published
            mock_event_publisher.publish_domain_event.assert_not_called()

            # Check that domain events were not cleared
            mock_entity.clear_domain_events.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_events_without_domain_events_attribute(self) -> None:
        """Test dispatch_events with entity without domain_events attribute."""
        mock_logger = MagicMock()
        mock_event_publisher = MagicMock()
        mock_event_publisher.publish_domain_event = AsyncMock()

        mock_entity = MagicMock()
        mock_entity.__class__.__name__ = "TestEntity"
        # No domain_events attribute

        with patch(
            "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
        ):
            interceptor = DispatchDomainEventsInterceptor(mock_event_publisher)
            await interceptor.dispatch_events(mock_entity)

            # Check that no events were published
            mock_event_publisher.publish_domain_event.assert_not_called()


class TestAutoLogAsync:
    """Test auto_log_async decorator."""

    @pytest.mark.asyncio
    async def test_auto_log_async_default_operation_name(self) -> None:
        """Test auto_log_async with default operation name."""
        mock_logger = MagicMock()

        @auto_log_async()
        async def test_function() -> str:
            return "success"

        with (
            patch(
                "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
            ),
            patch("eshop.core.middleware.behaviors.AutoLogContext") as mock_context,
        ):
            mock_context.return_value.__aenter__ = AsyncMock()
            mock_context.return_value.__aexit__ = AsyncMock()

            result = await test_function()

            assert result == "success"
            mock_context.assert_called_once_with(mock_logger, "test_function")

    @pytest.mark.asyncio
    async def test_auto_log_async_custom_operation_name(self) -> None:
        """Test auto_log_async with custom operation name."""
        mock_logger = MagicMock()

        @auto_log_async("custom_operation")
        async def test_function() -> str:
            return "success"

        with (
            patch(
                "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
            ),
            patch("eshop.core.middleware.behaviors.AutoLogContext") as mock_context,
        ):
            mock_context.return_value.__aenter__ = AsyncMock()
            mock_context.return_value.__aexit__ = AsyncMock()

            result = await test_function()

            assert result == "success"
            mock_context.assert_called_once_with(mock_logger, "custom_operation")

    @pytest.mark.asyncio
    async def test_auto_log_async_with_arguments(self) -> None:
        """Test auto_log_async with function arguments."""
        mock_logger = MagicMock()

        @auto_log_async()
        async def test_function(arg1: str, arg2: int) -> str:
            return f"{arg1}_{arg2}"

        with (
            patch(
                "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
            ),
            patch("eshop.core.middleware.behaviors.AutoLogContext") as mock_context,
        ):
            mock_context.return_value.__aenter__ = AsyncMock()
            mock_context.return_value.__aexit__ = AsyncMock()

            result = await test_function("test", 42)

            assert result == "test_42"
            mock_context.assert_called_once_with(mock_logger, "test_function")


class TestAutoLogSync:
    """Test auto_log_sync decorator."""

    def test_auto_log_sync_default_operation_name(self) -> None:
        """Test auto_log_sync with default operation name."""
        mock_logger = MagicMock()

        @auto_log_sync()
        def test_function() -> str:
            return "success"

        with patch(
            "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
        ):
            result = test_function()

            assert result == "success"
            assert mock_logger.info.call_count == 2  # Start and complete

            # Check start log
            start_call = mock_logger.info.call_args_list[0]
            assert "Starting test_function" in start_call[0][0]

            # Check complete log
            complete_call = mock_logger.info.call_args_list[1]
            assert "Completed test_function" in complete_call[0][0]
            assert complete_call[1]["execution_time"] > 0

    def test_auto_log_sync_custom_operation_name(self) -> None:
        """Test auto_log_sync with custom operation name."""
        mock_logger = MagicMock()

        @auto_log_sync("custom_operation")
        def test_function() -> str:
            return "success"

        with patch(
            "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
        ):
            result = test_function()

            assert result == "success"
            assert mock_logger.info.call_count == 2

            # Check start log
            start_call = mock_logger.info.call_args_list[0]
            assert "Starting custom_operation" in start_call[0][0]

            # Check complete log
            complete_call = mock_logger.info.call_args_list[1]
            assert "Completed custom_operation" in complete_call[0][0]

    def test_auto_log_sync_exception(self) -> None:
        """Test auto_log_sync with exception."""
        mock_logger = MagicMock()

        @auto_log_sync()
        def test_function() -> str:
            raise ValueError("Test error")

        with patch(
            "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
        ):
            with pytest.raises(ValueError, match="Test error"):
                test_function()

            assert mock_logger.info.call_count == 1  # Start only
            assert mock_logger.error.call_count == 1  # Error log

            # Check error log
            error_call = mock_logger.error.call_args
            assert "Failed test_function" in error_call[0][0]
            assert error_call[1]["error_type"] == "ValueError"
            assert error_call[1]["error_message"] == "Test error"
            assert error_call[1]["execution_time"] > 0

    def test_auto_log_sync_with_arguments(self) -> None:
        """Test auto_log_sync with function arguments."""
        mock_logger = MagicMock()

        @auto_log_sync()
        def test_function(arg1: str, arg2: int) -> str:
            return f"{arg1}_{arg2}"

        with patch(
            "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
        ):
            result = test_function("test", 42)

            assert result == "test_42"
            assert mock_logger.info.call_count == 2


class TestAutoLogDatabaseOperation:
    """Test auto_log_database_operation decorator."""

    @pytest.mark.asyncio
    async def test_auto_log_database_operation_default_name(self) -> None:
        """Test auto_log_database_operation with default operation name."""
        mock_logger = MagicMock()

        @auto_log_database_operation()
        async def test_function(_self) -> str:
            return "success"

        mock_self = MagicMock()
        mock_self.__class__.__name__ = "TestClass"

        with (
            patch(
                "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
            ),
            patch("eshop.core.middleware.behaviors.AutoLogContext") as mock_context,
        ):
            mock_context.return_value.__aenter__ = AsyncMock()
            mock_context.return_value.__aexit__ = AsyncMock()

            result = await test_function(mock_self)

            assert result == "success"
            mock_context.assert_called_once_with(mock_logger, "database.test_function")

            # Check debug log for class name
            mock_logger.debug.assert_called_once_with(
                "Database operation on: TestClass"
            )

    @pytest.mark.asyncio
    async def test_auto_log_database_operation_custom_name(self) -> None:
        """Test auto_log_database_operation with custom operation name."""
        mock_logger = MagicMock()

        @auto_log_database_operation("custom_db_operation")
        async def test_function(_self) -> str:
            return "success"

        mock_self = MagicMock()

        with (
            patch(
                "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
            ),
            patch("eshop.core.middleware.behaviors.AutoLogContext") as mock_context,
        ):
            mock_context.return_value.__aenter__ = AsyncMock()
            mock_context.return_value.__aexit__ = AsyncMock()

            result = await test_function(mock_self)

            assert result == "success"
            mock_context.assert_called_once_with(mock_logger, "custom_db_operation")

    @pytest.mark.asyncio
    async def test_auto_log_database_operation_without_self(self) -> None:
        """Test auto_log_database_operation without self argument."""
        mock_logger = MagicMock()

        @auto_log_database_operation()
        async def test_function() -> str:
            return "success"

        with (
            patch(
                "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
            ),
            patch("eshop.core.middleware.behaviors.AutoLogContext") as mock_context,
        ):
            mock_context.return_value.__aenter__ = AsyncMock()
            mock_context.return_value.__aexit__ = AsyncMock()

            result = await test_function()

            # The function should work but return None due to the mock context
            assert result is None
            mock_context.assert_called_once_with(mock_logger, "database.test_function")

            # No debug log since no self argument (args[0] doesn't exist)
            mock_logger.debug.assert_not_called()


class TestPerformanceLoggingMixin:
    """Test PerformanceLoggingMixin."""

    def test_performance_logging_mixin_initialization(self) -> None:
        """Test PerformanceLoggingMixin initialization."""
        mock_logger = MagicMock()

        class TestClass(PerformanceLoggingMixin):
            pass

        with patch(
            "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
        ):
            instance = TestClass()

            assert instance.logger == mock_logger

    def test_log_performance_normal_operation(self) -> None:
        """Test log_performance with normal operation duration."""
        mock_logger = MagicMock()

        class TestClass(PerformanceLoggingMixin):
            pass

        with patch(
            "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
        ):
            instance = TestClass()
            instance.log_performance("test_operation", 0.5, user_id="123")

            # Check info log
            info_call = mock_logger.info.call_args
            assert "Performance: test_operation" in info_call[0][0]
            assert info_call[1]["duration_ms"] == 500.0
            assert info_call[1]["user_id"] == "123"

            # Check no warning log for normal duration
            mock_logger.warning.assert_not_called()

    def test_log_performance_slow_operation(self) -> None:
        """Test log_performance with slow operation duration."""
        mock_logger = MagicMock()

        class TestClass(PerformanceLoggingMixin):
            pass

        with patch(
            "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
        ):
            instance = TestClass()
            instance.log_performance("slow_operation", 1.5, user_id="123")

            # Check info log
            info_call = mock_logger.info.call_args
            assert "Performance: slow_operation" in info_call[0][0]
            assert info_call[1]["duration_ms"] == 1500.0
            assert info_call[1]["user_id"] == "123"

            # Check warning log for slow operation
            warning_call = mock_logger.warning.call_args
            assert "Slow operation detected: slow_operation" in warning_call[0][0]
            assert warning_call[1]["duration_ms"] == 1500.0
            assert warning_call[1]["user_id"] == "123"

    def test_log_performance_with_multiple_context(self) -> None:
        """Test log_performance with multiple context parameters."""
        mock_logger = MagicMock()

        class TestClass(PerformanceLoggingMixin):
            pass

        with patch(
            "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
        ):
            instance = TestClass()
            instance.log_performance(
                "test_operation",
                0.5,
                user_id="123",
                operation_type="read",
                table_name="users",
            )

            # Check info log with all context
            info_call = mock_logger.info.call_args
            assert "Performance: test_operation" in info_call[0][0]
            assert info_call[1]["duration_ms"] == 500.0
            assert info_call[1]["user_id"] == "123"
            assert info_call[1]["operation_type"] == "read"
            assert info_call[1]["table_name"] == "users"


class TestMiddlewareBehaviorsIntegration:
    """Integration tests for middleware behaviors."""

    @pytest.mark.asyncio
    async def test_logging_and_validation_behaviors_combined(self) -> None:
        """Test combining logging and validation behaviors."""
        mock_logger = MagicMock()

        @logging_behavior
        @validation_behavior
        async def test_function() -> str:
            return "success"

        with patch(
            "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
        ):
            result = await test_function()

            assert result == "success"
            # Should have both logging and validation calls
            assert mock_logger.info.call_count == 2  # Start and complete
            assert mock_logger.debug.call_count == 2  # Input and output validation

    def test_auto_log_sync_and_performance_mixin_combined(self) -> None:
        """Test combining auto_log_sync with PerformanceLoggingMixin."""
        mock_logger = MagicMock()

        class TestClass(PerformanceLoggingMixin):
            @auto_log_sync()
            def test_method(self) -> str:
                return "success"

        with patch(
            "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
        ):
            instance = TestClass()
            result = instance.test_method()

            assert result == "success"
            # Should have both auto_log_sync and PerformanceLoggingMixin logs
            assert (
                mock_logger.info.call_count == 2
            )  # Start and complete from auto_log_sync

    @pytest.mark.asyncio
    async def test_auditable_entity_with_domain_events(self) -> None:
        """Test AuditableEntityInterceptor with DispatchDomainEventsInterceptor."""
        mock_logger = MagicMock()
        mock_event_publisher = MagicMock()
        mock_event_publisher.publish_domain_event = AsyncMock()

        mock_entity = MagicMock()
        mock_entity.__class__.__name__ = "TestEntity"
        mock_entity.domain_events = [MagicMock()]
        mock_entity.clear_domain_events = MagicMock()

        with (
            patch(
                "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
            ),
            patch("eshop.core.middleware.behaviors.AutoLogContext") as mock_context,
        ):
            mock_context.return_value.__aenter__ = AsyncMock()
            mock_context.return_value.__aexit__ = AsyncMock()

            auditable_interceptor = AuditableEntityInterceptor()
            domain_events_interceptor = DispatchDomainEventsInterceptor(
                mock_event_publisher
            )

            # Simulate save operation
            await auditable_interceptor.before_save(mock_entity)
            await domain_events_interceptor.dispatch_events(mock_entity)
            await auditable_interceptor.after_save(mock_entity)

            # Check all logging occurred
            assert (
                mock_logger.debug.call_count == 3
            )  # before_save, dispatch, after_save
            mock_event_publisher.publish_domain_event.assert_called_once()
            mock_entity.clear_domain_events.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_operation_with_auto_logging(self) -> None:
        """Test database operation with auto_log_database_operation."""
        mock_logger = MagicMock()

        class TestRepository:
            @auto_log_database_operation("save_user")
            async def save_user(self, user_data: dict) -> str:
                return f"user_{user_data['id']}"

        with (
            patch(
                "eshop.core.middleware.behaviors.get_logger", return_value=mock_logger
            ),
            patch("eshop.core.middleware.behaviors.AutoLogContext") as mock_context,
        ):
            mock_context.return_value.__aenter__ = AsyncMock()
            mock_context.return_value.__aexit__ = AsyncMock()

            repo = TestRepository()
            result = await repo.save_user({"id": "123"})

            assert result == "user_123"
            mock_context.assert_called_once_with(mock_logger, "save_user")
            mock_logger.debug.assert_called_once_with(
                "Database operation on: TestRepository"
            )
