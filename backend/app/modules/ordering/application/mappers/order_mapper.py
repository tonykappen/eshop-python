"""Order mapper for converting between domain, DTO, and ORM models."""

from app.modules.ordering.application.dtos.address_dto import AddressDto
from app.modules.ordering.application.dtos.order_dto import OrderDto
from app.modules.ordering.application.dtos.order_item_dto import OrderItemDto
from app.modules.ordering.application.dtos.payment_dto import PaymentDto
from app.modules.ordering.domain.entities.order.order import Order


class OrderMapper:
    """Mapper for Order domain ↔ DTO conversions."""

    @staticmethod
    def to_dto(order: Order) -> OrderDto:
        """
        Convert Order domain entity to OrderDto.

        Args:
            order: Order domain entity

        Returns:
            OrderDto
        """
        return OrderDto(
            id=order.id,
            customer_id=order.customer_id,
            order_name=order.order_name,
            shipping_address=AddressDto(
                first_name=order.shipping_address.first_name,
                last_name=order.shipping_address.last_name,
                email_address=order.shipping_address.email_address or "",
                address_line=order.shipping_address.address_line,
                country=order.shipping_address.country,
                state=order.shipping_address.state,
                zip_code=order.shipping_address.zip_code,
            ),
            billing_address=AddressDto(
                first_name=order.billing_address.first_name,
                last_name=order.billing_address.last_name,
                email_address=order.billing_address.email_address or "",
                address_line=order.billing_address.address_line,
                country=order.billing_address.country,
                state=order.billing_address.state,
                zip_code=order.billing_address.zip_code,
            ),
            payment=PaymentDto(
                card_name=order.payment.card_name or "",
                card_number=order.payment.card_number,
                expiration=order.payment.expiration,
                cvv=order.payment.cvv,
                payment_method=order.payment.payment_method,
            ),
            items=[
                OrderItemDto(
                    order_id=item.order_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=item.price,
                )
                for item in order.items
            ],
        )
