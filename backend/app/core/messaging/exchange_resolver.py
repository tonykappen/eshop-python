"""Exchange name resolver for event types.

This module provides a configurable way to map event types to RabbitMQ exchange names.
Supports configuration via environment variables and provides sensible defaults.
"""

import json
import logging

logger = logging.getLogger(__name__)


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
            logger.debug(f"Found custom exchange mapping for {event_type}: {exchange}")
            return exchange

        # Check prefix patterns (e.g., "product.*" -> "catalog.events")
        for pattern, exchange in custom_mappings.items():
            if pattern.endswith(".*") and event_type.startswith(pattern[:-2]):
                logger.debug(f"Found custom pattern mapping {pattern} for {event_type}: {exchange}")
                return exchange

    # 2. Check default module-based mappings
    default_exchange = _get_default_exchange_for_event_type(event_type)
    if default_exchange:
        logger.debug(f"Using default exchange mapping for {event_type}: {default_exchange}")
        return default_exchange

    # 3. No mapping found, use default exchange
    logger.debug(f"No exchange mapping found for {event_type}, using default exchange")
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
                logger.warning(
                    "EVENT_EXCHANGE_MAPPINGS must be a JSON object, ignoring invalid value"
                )
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse EVENT_EXCHANGE_MAPPINGS: {e}")
    except Exception as e:
        logger.debug(f"Could not load custom exchange mappings: {e}")

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
    # Default module-based mappings
    default_mappings = {
        "product.": "catalog.events",
        "order.": "ordering.events",
        "basket.": "basket.events",
        "payment.": "payment.events",
        "inventory.": "inventory.events",
    }

    # Check if event type matches any module prefix
    for prefix, exchange in default_mappings.items():
        if event_type.startswith(prefix):
            return exchange

    return None
