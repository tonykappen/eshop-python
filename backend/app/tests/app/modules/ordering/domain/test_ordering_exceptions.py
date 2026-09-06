"""Tests for ordering domain exceptions."""

from uuid import uuid4

from app.modules.ordering.domain.exceptions.definitions import (
    InventoryReservationError,
    OrderCancellationError,
    OrderCreationError,
    OrderItemNotFoundError,
    OrderStatusTransitionError,
    OrderUpdateError,
    OrderValidationError,
    PaymentProcessingError,
)


class TestOrderingExceptions:
    def test_order_item_not_found(self) -> None:
        item_id = uuid4()
        err = OrderItemNotFoundError(item_id)
        assert err.item_id == item_id
        assert "OrderItem" in str(err)

    def test_order_validation_error(self) -> None:
        err = OrderValidationError("invalid", field="quantity")
        assert err.field == "quantity"

    def test_order_lifecycle_errors(self) -> None:
        assert OrderCreationError("fail", "details").details == "details"
        assert OrderUpdateError("fail").message == "fail"
        assert OrderCancellationError("cancel").message == "cancel"

    def test_order_status_transition_error(self) -> None:
        order_id = uuid4()
        err = OrderStatusTransitionError("pending", "shipped", order_id)
        assert err.current_status == "pending"
        assert str(order_id) in str(err)

    def test_payment_processing_error(self) -> None:
        payment_id = uuid4()
        err = PaymentProcessingError("declined", payment_id=payment_id)
        assert err.payment_id == payment_id

    def test_inventory_reservation_error(self) -> None:
        product_id = uuid4()
        err = InventoryReservationError("out of stock", product_id=product_id)
        assert err.product_id == product_id
