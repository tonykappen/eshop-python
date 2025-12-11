"""DeleteProduct endpoint - FastAPI endpoint for product deletion."""

from fastapi import APIRouter, Depends, Request
from typing import Any
from uuid import UUID

from app.core.repr.base import CQRSEndpointFactory
from app.modules.catalog.utils import get_endpoint_factory
from app.core.auth.rbac import require_command_access
from app.modules.catalog.application.features.products.commands.delete_product.command import DeleteProductCommand, DeleteProductResult

router = APIRouter()


@router.delete("/{product_id}", response_model=DeleteProductResult)
async def delete_product(
    product_id: UUID,
    http_request: Request,
    factory: CQRSEndpointFactory = Depends(get_endpoint_factory),
    # RBAC: Command access required (admin, manager only)
    _: Any = Depends(require_command_access()),
) -> DeleteProductResult:
    """
    Delete a product.

    Demonstrates: HTTP Request -> Command -> Result -> HTTP Response
    RBAC: Requires command access (admin, manager roles only)
    """
    # Create command endpoint using factory
    endpoint: Any = factory.create_command_endpoint(
        command_factory=DeleteProductCommand,
        result_mapper=None,  # Will use default response mapper
    )

    # Create the command with product ID
    command = DeleteProductCommand(product_id=product_id)

    # Execute the REPR pattern flow
    response = await endpoint.execute(http_request, command)

    # Extract the result and return DeleteProductResponse
    result = response.data  # This will be DeleteProductResult
    return DeleteProductResult(is_success=result.is_success)
