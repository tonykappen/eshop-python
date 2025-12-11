"""Product deleted integration event."""

from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from pydantic import BaseModel, Field


class ProductDeletedIntegrationEvent(BaseModel):
    """Integration event published when a product is deleted."""

    # Event metadata
    event_id: UUID = Field(..., description="Unique event ID")
    event_type: str = Field(default="product.deleted.v1", description="Event type")
    event_version: str = Field(default="1.0", description="Event version")
    occurred_at: datetime = Field(..., description="When the event occurred")
    source: str = Field(default="catalog-service", description="Event source")
    
    # Event data
    product_id: UUID = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    product_sku: str = Field(..., description="Product SKU")
    deleted_at: datetime = Field(..., description="When the product was deleted")
    deletion_reason: str | None = Field(None, description="Reason for deletion")
    
    # Additional context
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @classmethod
    def create(
        cls,
        product_id: UUID,
        product_name: str,
        product_sku: str,
        deleted_at: datetime | None = None,
        deletion_reason: str | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> "ProductDeletedIntegrationEvent":
        """
        Create a new product deleted integration event.
        
        Args:
            product_id: Product ID
            product_name: Product name
            product_sku: Product SKU
            deleted_at: When the product was deleted (defaults to now)
            deletion_reason: Reason for deletion
            metadata: Additional metadata
            
        Returns:
            ProductDeletedIntegrationEvent instance
        """
        import uuid
        
        if deleted_at is None:
            deleted_at = datetime.utcnow()
        
        return cls(
            event_id=uuid.uuid4(),
            occurred_at=datetime.utcnow(),
            product_id=product_id,
            product_name=product_name,
            product_sku=product_sku,
            deleted_at=deleted_at,
            deletion_reason=deletion_reason,
            metadata=metadata or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "event_version": self.event_version,
            "occurred_at": self.occurred_at.isoformat(),
            "source": self.source,
            "product_id": str(self.product_id),
            "product_name": self.product_name,
            "product_sku": self.product_sku,
            "deleted_at": self.deleted_at.isoformat(),
            "deletion_reason": self.deletion_reason,
            "metadata": self.metadata,
        }

