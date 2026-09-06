"""Tests for mediator cancellation token."""

import pytest
from app.core.mediator.cancellation import CancellationError, CancellationToken


class TestCancellationToken:
    def test_manual_cancel(self) -> None:
        token = CancellationToken()
        assert token.is_cancellation_requested is False
        token.cancel()
        assert token.is_cancellation_requested is True

    def test_throw_if_cancellation_requested(self) -> None:
        token = CancellationToken()
        token.cancel()
        with pytest.raises(CancellationError):
            token.throw_if_cancellation_requested()

    def test_mark_completed_prevents_cancel_flag_meaning_change(self) -> None:
        token = CancellationToken()
        token.mark_completed()
        assert token.is_cancellation_requested is False

    @pytest.mark.asyncio
    async def test_register_rollback_callback(self) -> None:
        token = CancellationToken()
        called = {"value": False}

        async def rollback() -> None:
            called["value"] = True

        token.register_rollback_callback(rollback)
        token.cancel()
        await token.cleanup()
        assert called["value"] is True
