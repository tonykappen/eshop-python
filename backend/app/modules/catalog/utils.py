"""Common utilities for the catalog module."""

from app.core.mediator.fastapi_integration import get_mediator
from app.core.mediator.mediator import IMediator
from app.core.repr.base import CQRSEndpointFactory
from fastapi import Depends


def get_endpoint_factory(
    mediator: IMediator = Depends(get_mediator),
) -> CQRSEndpointFactory:
    """Get CQRS endpoint factory."""
    return CQRSEndpointFactory(mediator)
