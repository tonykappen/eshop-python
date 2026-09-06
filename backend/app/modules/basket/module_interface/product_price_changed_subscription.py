"""RabbitMQ subscription for catalog product price-changed integration events."""

import logging
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)

CATALOG_EVENTS_EXCHANGE = "catalog.events"
PRODUCT_PRICE_CHANGED_QUEUE = "basket-product-price-changed-queue"


def coerce_product_price_changed_payload(event_data: dict[str, Any]) -> dict[str, Any]:
    """Normalise JSON-decoded catalog price-change payload for Pydantic."""
    if not isinstance(event_data, dict):
        return event_data

    event_id = event_data.get("event_id")
    if isinstance(event_id, str):
        try:
            event_data["event_id"] = UUID(event_id)
        except (ValueError, AttributeError):
            pass

    product_id = event_data.get("product_id")
    if isinstance(product_id, str):
        try:
            event_data["product_id"] = UUID(product_id)
        except (ValueError, AttributeError):
            pass

    return event_data


async def subscribe_product_price_changed_consumer() -> None:
    """
    Subscribe basket to catalog product price changes on RabbitMQ.

    Declares ``basket-product-price-changed-queue`` bound to ``catalog.events``.
    """
    from app.core.mediator.fastapi_integration import get_mediator
    from app.modules.basket.application.integration_event_handlers.products.product_price_changed_integration_event_handler import \
        ProductPriceChangedIntegrationEventHandler
    from app.modules.basket.module_interface.di.basket.basket_providers import \
        get_basket_message_bus
    from app.modules.catalog.contracts.products.integration_events.v1.product_price_changed_integration_event import \
        ProductPriceChangedIntegrationEventV1

    main_mediator = get_mediator()
    price_changed_handler = ProductPriceChangedIntegrationEventHandler(main_mediator)

    routing_key = ProductPriceChangedIntegrationEventV1.model_fields[
        "event_type"
    ].default

    async def _consume(event_data: Any) -> None:
        try:
            payload = coerce_product_price_changed_payload(event_data)
            event = ProductPriceChangedIntegrationEventV1(**payload)
            await price_changed_handler.handle(event)
        except Exception:
            logger.exception(
                "Basket product-price-changed consumer failed to handle message"
            )
            raise

    message_bus = get_basket_message_bus()
    if hasattr(message_bus, "connect") and (
        not hasattr(message_bus, "_connection") or message_bus._connection is None
    ):
        await message_bus.connect()

    await message_bus.subscribe_to_exchange(
        exchange=CATALOG_EVENTS_EXCHANGE,
        routing_key=routing_key,
        queue_name=PRODUCT_PRICE_CHANGED_QUEUE,
        handler=_consume,
    )

    logger.info(
        "Subscribed ProductPriceChangedIntegrationEventHandler to RabbitMQ "
        "(exchange=%s, routing_key=%s, queue=%s)",
        CATALOG_EVENTS_EXCHANGE,
        routing_key,
        PRODUCT_PRICE_CHANGED_QUEUE,
    )
