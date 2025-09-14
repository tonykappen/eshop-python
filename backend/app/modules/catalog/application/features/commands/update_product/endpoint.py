"""UpdateProduct endpoint - FastAPI endpoint for product updates."""

from fastapi import APIRouter, Depends, Request
from typing import Any
from uuid import UUID

from app.core.repr.base import CQRSEndpointFactory
from app.modules.catalog.utils import get_endpoint_factory
from app.core.auth.rbac import require_command_access
from .command import UpdateProductCommand, UpdateProductResult

router = APIRouter()


@router.put("/{product_id}", response_model=UpdateProductResult)
async def update_product(
    product_id: UUID,
    request: UpdateProductCommand,
    http_request: Request,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Command access required (admin, manager only)
    _: Any = Depends(require_command_access()),
) -> UpdateProductResult:
    """
    Update an existing product.

    Demonstrates: HTTP Request -> Command -> Result -> HTTP Response
    RBAC: Requires command access (admin, manager roles only)
    """
    # Create command endpoint using factory
    endpoint: Any = factory.create_command_endpoint(
        command_factory=UpdateProductCommand,
        result_mapper=None,  # Will use default response mapper
    )

    # Create the command with product ID and request data
    command = UpdateProductCommand(
        id=product_id,
        name=request.name,
        description=request.description,
        price=request.price,
        picture_url=request.picture_url,
        category=request.category,
    )

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, command)

    # Extract the result and return UpdateProductResponse
    result = response.data  # This will be UpdateProductResult
    return UpdateProductResult(is_success=result.is_success)
