"""Catalog module integration events with auto-naming."""

from typing import Any
from uuid import UUID

from pydantic import Field

from app.core.messaging.integration_event import (
    CatalogIntegrationEvent,
    IntegrationEvent,
)


class ProductCreatedIntegrationEvent(CatalogIntegrationEvent):
    """Integration event published when a product is created."""

    # These will be auto-generated:
    # event_type: "product_created" (from class name)
    # topic: "app.catalog.product_created"
    # routing_key: "app.catalog.product_created"
    # source_module: "catalog"

    product_id: UUID = Field(..., description="ID of the created product")
    product_name: str = Field(..., description="Name of the created product")
    price: float = Field(..., description="Price of the created product")
    category_id: UUID | None = Field(None, description="Category ID if applicable")


class ProductPriceChangedIntegrationEvent(CatalogIntegrationEvent):
    """Integration event published when a product price changes."""

    # Auto-generated metadata:
    # event_type: "product_price_changed"
    # topic: "app.catalog.product_price_changed"
    # routing_key: "app.catalog.product_price_changed"

    product_id: UUID = Field(..., description="ID of the product")
    old_price: float = Field(..., description="Previous price")
    new_price: float = Field(..., description="New price")
    price_change_reason: str | None = Field(None, description="Reason for price change")


class ProductInventoryUpdatedIntegrationEvent(CatalogIntegrationEvent):
    """Integration event published when product inventory is updated."""

    # Auto-generated metadata:
    # event_type: "product_inventory_updated"
    # topic: "app.catalog.product_inventory_updated"
    # routing_key: "app.catalog.product_inventory_updated"

    product_id: UUID = Field(..., description="ID of the product")
    old_quantity: int = Field(..., description="Previous quantity")
    new_quantity: int = Field(..., description="New quantity")
    warehouse_id: UUID | None = Field(
        None, description="Warehouse where inventory changed"
    )


class ProductDiscontinuedIntegrationEvent(CatalogIntegrationEvent):
    """Integration event published when a product is discontinued."""

    # Auto-generated metadata:
    # event_type: "product_discontinued"
    # topic: "app.catalog.product_discontinued"
    # routing_key: "app.catalog.product_discontinued"

    product_id: UUID = Field(..., description="ID of the discontinued product")
    discontinuation_date: str = Field(
        ..., description="Date when product was discontinued"
    )
    reason: str | None = Field(None, description="Reason for discontinuation")
    replacement_product_id: UUID | None = Field(
        None, description="ID of replacement product if any"
    )


# Example usage showing how to create integration events from domain events
def create_integration_event_from_domain(domain_event: Any) -> IntegrationEvent:
    """
    Example function showing how to create integration events from domain events.

    This demonstrates the auto-capture of event names from triggering classes.
    """
    # This will automatically capture:
    # - event_type from domain_event class name
    # - source_module from domain_event module path
    # - routing_key following the pattern
    integration_event = IntegrationEvent.from_domain_event(
        domain_event, additional_context="Generated from catalog domain event"
    )

    return integration_event


# Example showing explicit event creation with custom routing
class CustomRoutingEvent(CatalogIntegrationEvent):
    """Example event with custom routing pattern."""

    # Override the default routing pattern
    _routing_pattern = "custom.{module}.priority.{event_type}"

    priority_level: str = Field(default="normal", description="Priority level")
    custom_data: dict = Field(default_factory=dict, description="Custom event data")
