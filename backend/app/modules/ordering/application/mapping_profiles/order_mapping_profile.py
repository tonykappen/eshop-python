"""Order mapping profile for core mapping engine."""

from app.core.mapping.profiles.base_mapping_profile import BaseMappingProfile
from app.modules.ordering.application.dtos.order_dto import OrderDto
from app.modules.ordering.domain.entities.order.order import Order


class OrderMappingProfile(BaseMappingProfile):
    """Mapping profile for Order domain ↔ DTO ↔ ORM conversions."""

    def configure_mappings(self) -> None:
        """Configure mapping rules for Order types."""
        # Order domain → DTO mapping is handled by OrderMapper
        # This profile can be extended for more complex mappings if needed
        pass
