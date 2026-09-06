"""CreateProduct endpoint - FastAPI endpoint for product creation."""

from typing import Any

from app.core.auth.rbac import require_command_access
from app.core.repr.base import CQRSEndpointFactory
from app.modules.catalog.application.features.products.commands.create_product.create_product_command import (
    CreateProductCommand, CreateProductResult)
from app.modules.catalog.utils import get_endpoint_factory
from fastapi import APIRouter, Depends, Request

router = APIRouter()


@router.post("/", response_model=CreateProductResult, status_code=201)
async def create_product(
    request: CreateProductCommand,
    http_request: Request,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Command access required (admin, manager only)
    _: Any = Depends(require_command_access()),
) -> CreateProductResult:
    """
    Create a new product.

    Demonstrates: HTTP Request -> Command -> Result -> HTTP Response
    RBAC: Requires command access (admin, manager roles only)
    """
    # Create command endpoint using factory
    endpoint: Any = factory.create_command_endpoint(
        command_factory=CreateProductCommand,
        result_mapper=None,  # Will use default response mapper
    )

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, request)

    # Extract the result and return CreateProductResult
    result = response.data  # This will be CreateProductResult
    return CreateProductResult(id=result.id)
