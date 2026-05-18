"""Exchange name resolver for event types.

This module provides a configurable way to map event types to RabbitMQ exchange names.
Supports configuration via environment variables and provides sensible defaults.
"""

import json

from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


def get_exchange_for_event_type(event_type: str | None) -> str | None:
    """
    Get the exchange name for a given event type.

    Priority order:
    1. Custom mappings from environment variable EVENT_EXCHANGE_MAPPINGS
    2. Default module-based mappings (e.g., product.* -> catalog.events)
    3. None (use default exchange)

    Args:
        event_type: The event type (e.g., "product.deleted.v1", "order.created.v1")

    Returns:
        Exchange name or None to use default exchange

    Examples:
        >>> get_exchange_for_event_type("product.deleted.v1")
        'catalog.events'
        >>> get_exchange_for_event_type("order.created.v1")
        'ordering.events'
        >>> get_exchange_for_event_type("unknown.event")
        None
    """
    if not event_type:
        return None

    # 1. Check custom mappings from environment variable
    custom_mappings = _get_custom_exchange_mappings()
    if custom_mappings:
        # Check exact match first
        if event_type in custom_mappings:
            exchange = custom_mappings[event_type]
            logger.log_debug_with_context(
                "Found custom exchange mapping",
                context={"event_type": event_type, "exchange": exchange}
            )
            return exchange

        # Check prefix patterns (e.g., "product.*" -> "catalog.events")
        for pattern, exchange in custom_mappings.items():
            if pattern.endswith(".*") and event_type.startswith(pattern[:-2]):
                logger.log_debug_with_context(
                    "Found custom pattern mapping",
                    context={"pattern": pattern, "event_type": event_type, "exchange": exchange}
                )
                return exchange

    # 2. Check default module-based mappings
    default_exchange = _get_default_exchange_for_event_type(event_type)
    if default_exchange:
        logger.log_debug_with_context(
            "Using default exchange mapping",
            context={"event_type": event_type, "exchange": default_exchange}
        )
        return default_exchange

    # 3. No mapping found, use default exchange
    logger.log_debug_with_context(
        "No exchange mapping found, using default exchange",
        context={"event_type": event_type}
    )
    return None


def _get_custom_exchange_mappings() -> dict[str, str]:
    """
    Get custom exchange mappings from environment variable.

    Environment variable: EVENT_EXCHANGE_MAPPINGS
    Format: JSON object mapping event types/patterns to exchange names
    Example: {"product.deleted.*": "catalog.events", "order.*": "ordering.events"}

    Returns:
        Dictionary mapping event types/patterns to exchange names
    """
    try:
        from app.config.env import get_env

        mappings_json = get_env("EVENT_EXCHANGE_MAPPINGS", None)
        if mappings_json:
            mappings = json.loads(mappings_json)
            if isinstance(mappings, dict):
                return mappings
            else:
                logger.log_warning_with_context(
                    "EVENT_EXCHANGE_MAPPINGS must be a JSON object, ignoring invalid value"
                )
    except json.JSONDecodeError as e:
        logger.log_warning_with_context(
            "Failed to parse EVENT_EXCHANGE_MAPPINGS",
            context={"error": str(e)}
        )
    except Exception as e:
        logger.log_debug_with_context(
            "Could not load custom exchange mappings",
            context={"error": str(e)}
        )

    return {}


def _get_default_exchange_for_event_type(event_type: str) -> str | None:
    """
    Get default exchange name based on event type patterns.

    Default mappings:
    - product.* -> catalog.events
    - order.* -> ordering.events
    - basket.* -> basket.events
    - payment.* -> payment.events

    Args:
        event_type: The event type

    Returns:
        Exchange name or None
    """
    # Default module-based mappings. Both dotted ("basket.") and snake_case
    # ("basket_") forms are accepted because IntegrationEvent._generate_event_type
    # converts CamelCase class names to snake_case (e.g.
    # ``BasketCheckoutIntegrationEvent`` -> ``basket_checkout_integration``).
    default_mappings = {
        "product.": "catalog.events",
        "product_": "catalog.events",
        "order.": "ordering.events",
        "order_": "ordering.events",
        "basket.": "basket.events",
        "basket_": "basket.events",
        "payment.": "payment.events",
        "payment_": "payment.events",
        "inventory.": "inventory.events",
        "inventory_": "inventory.events",
    }

    # Check if event type matches any module prefix
    for prefix, exchange in default_mappings.items():
        if event_type.startswith(prefix):
            return exchange

    return None
