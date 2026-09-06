"""Basket module utilities."""

from app.core.mediator.fastapi_integration import get_mediator
from app.core.repr.base import CQRSEndpointFactory
from fastapi import Depends


def get_endpoint_factory(
    mediator=Depends(get_mediator),
) -> CQRSEndpointFactory:
    """Get CQRS endpoint factory."""
    return CQRSEndpointFactory(mediator)
