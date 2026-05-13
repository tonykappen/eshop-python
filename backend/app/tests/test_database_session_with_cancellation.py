"""Comprehensive tests for database session with cancellation token."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session_with_cancellation import (
    db_transaction_with_cancellation,
    get_cancellation_token_for_session,
    get_db_session_with_cancellation,
)


class TestGetDbSessionWithCancellation:
    """Test get_db_session_with_cancellation function."""

    @pytest.mark.asyncio
    async def test_get_db_session_with_cancellation_success(self):
        """Test successful database session retrieval with cancellation token."""
        mock_request = MagicMock(spec=Request)
        mock_session = AsyncMock(spec=AsyncSession)
        mock_cancellation_token = AsyncMock()
        mock_cancellation_token.cleanup = AsyncMock()

        with patch(
            "app.core.database.session_with_cancellation.AsyncSessionLocal"
        ) as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            with patch(
                "app.core.database.session_with_cancellation.get_cancellation_token_with_session"
            ) as mock_get_token:
                mock_get_token.return_value = mock_cancellation_token

                async for session, token in get_db_session_with_cancellation(
                    mock_request
                ):
                    assert session == mock_session
                    assert token == mock_cancellation_token

                mock_cancellation_token.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_session_with_cancellation_rollback_on_error(self):
        """Test database session rollback on exception."""
        mock_request = MagicMock(spec=Request)
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.rollback = AsyncMock()
        mock_cancellation_token = AsyncMock()
        mock_cancellation_token.cleanup = AsyncMock()

        with patch(
            "app.core.database.session_with_cancellation.AsyncSessionLocal"
        ) as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            with patch(
                "app.core.database.session_with_cancellation.get_cancellation_token_with_session"
            ) as mock_get_token:
                mock_get_token.return_value = mock_cancellation_token

                with pytest.raises(ValueError):
                    async for session, token in get_db_session_with_cancellation(
                        mock_request
                    ):
                        # Simulate an error
                        raise ValueError("Test error")

                mock_session.rollback.assert_called_once()
                mock_cancellation_token.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_session_with_cancellation_cleanup_always_called(self):
        """Test that cleanup is always called even if no exception."""
        mock_request = MagicMock(spec=Request)
        mock_session = AsyncMock(spec=AsyncSession)
        mock_cancellation_token = AsyncMock()
        mock_cancellation_token.cleanup = AsyncMock()

        with patch(
            "app.core.database.session_with_cancellation.AsyncSessionLocal"
        ) as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            with patch(
                "app.core.database.session_with_cancellation.get_cancellation_token_with_session"
            ) as mock_get_token:
                mock_get_token.return_value = mock_cancellation_token

                async for session, token in get_db_session_with_cancellation(
                    mock_request
                ):
                    pass  # Normal flow

                mock_cancellation_token.cleanup.assert_called_once()


class TestDbTransactionWithCancellation:
    """Test db_transaction_with_cancellation context manager."""

    @pytest.mark.asyncio
    async def test_db_transaction_with_cancellation_success(self):
        """Test successful transaction commit."""
        mock_request = MagicMock(spec=Request)
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.begin = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_cancellation_token = AsyncMock()
        mock_cancellation_token.is_cancellation_requested = False
        mock_cancellation_token.cleanup = AsyncMock()

        with patch(
            "app.core.database.session_with_cancellation.AsyncSessionLocal"
        ) as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            with patch(
                "app.core.database.session_with_cancellation.get_cancellation_token_with_session"
            ) as mock_get_token:
                mock_get_token.return_value = mock_cancellation_token

                async with db_transaction_with_cancellation(mock_request) as (
                    session,
                    token,
                ):
                    assert session == mock_session
                    assert token == mock_cancellation_token

                mock_session.begin.assert_called_once()
                mock_session.commit.assert_called_once()
                mock_cancellation_token.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_db_transaction_with_cancellation_rollback_on_cancellation(self):
        """Test transaction rollback when cancellation is requested."""
        mock_request = MagicMock(spec=Request)
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.begin = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_cancellation_token = AsyncMock()
        mock_cancellation_token.is_cancellation_requested = True
        mock_cancellation_token.cleanup = AsyncMock()

        with patch(
            "app.core.database.session_with_cancellation.AsyncSessionLocal"
        ) as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            with patch(
                "app.core.database.session_with_cancellation.get_cancellation_token_with_session"
            ) as mock_get_token:
                mock_get_token.return_value = mock_cancellation_token

                async with db_transaction_with_cancellation(mock_request) as (
                    session,
                    token,
                ):
                    assert session == mock_session
                    assert token == mock_cancellation_token

                mock_session.begin.assert_called_once()
                mock_session.rollback.assert_called_once()
                mock_cancellation_token.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_db_transaction_with_cancellation_rollback_on_exception(self):
        """Test transaction rollback on exception."""
        mock_request = MagicMock(spec=Request)
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.begin = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_cancellation_token = AsyncMock()
        mock_cancellation_token.is_cancellation_requested = False
        mock_cancellation_token.cleanup = AsyncMock()

        with patch(
            "app.core.database.session_with_cancellation.AsyncSessionLocal"
        ) as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            with patch(
                "app.core.database.session_with_cancellation.get_cancellation_token_with_session"
            ) as mock_get_token:
                mock_get_token.return_value = mock_cancellation_token

                with pytest.raises(ValueError):
                    async with db_transaction_with_cancellation(mock_request) as (
                        session,
                        token,
                    ):
                        raise ValueError("Test error")

                mock_session.begin.assert_called_once()
                mock_session.rollback.assert_called_once()
                mock_cancellation_token.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_db_transaction_with_cancellation_cleanup_always_called(self):
        """Test that cleanup is always called even on exception."""
        mock_request = MagicMock(spec=Request)
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.begin = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_cancellation_token = AsyncMock()
        mock_cancellation_token.is_cancellation_requested = False
        mock_cancellation_token.cleanup = AsyncMock()

        with patch(
            "app.core.database.session_with_cancellation.AsyncSessionLocal"
        ) as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            with patch(
                "app.core.database.session_with_cancellation.get_cancellation_token_with_session"
            ) as mock_get_token:
                mock_get_token.return_value = mock_cancellation_token

                try:
                    async with db_transaction_with_cancellation(mock_request) as (
                        session,
                        token,
                    ):
                        raise ValueError("Test error")
                except ValueError:
                    pass

                mock_cancellation_token.cleanup.assert_called_once()


class TestGetCancellationTokenForSession:
    """Test get_cancellation_token_for_session function."""

    @pytest.mark.asyncio
    async def test_get_cancellation_token_for_session(self):
        """Test getting cancellation token for existing session."""
        mock_request = MagicMock(spec=Request)
        mock_session = AsyncMock(spec=AsyncSession)
        mock_token = AsyncMock()

        with patch(
            "app.core.database.session_with_cancellation.get_cancellation_token_with_session"
        ) as mock_get_token:
            mock_get_token.return_value = mock_token

            result = get_cancellation_token_for_session(mock_request, mock_session)

            assert result == mock_token
            mock_get_token.assert_called_once_with(mock_request, mock_session)
