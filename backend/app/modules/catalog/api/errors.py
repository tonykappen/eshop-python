"""HTTP error mapping for catalog module."""

import logging
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions.base import DomainException
from app.modules.catalog.domain.product.exceptions.invalid_price import InvalidPrice
from app.modules.catalog.domain.product.exceptions.product_already_exists import (
    ProductAlreadyExists,
    ProductWithNameAlreadyExists,
)
from app.modules.catalog.domain.product.exceptions.product_not_found import (
    ProductNotFound,
    ProductNotFoundByName,
    ProductNotFoundBySku,
)

logger = logging.getLogger(__name__)


class CatalogErrorResponse:
    """Catalog error response handler."""

    @staticmethod
    def create_error_response(
        status_code: int,
        error_type: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> JSONResponse:
        """
        Create standardized error response.

        Args:
            status_code: HTTP status code
            error_type: Error type
            message: Error message
            details: Additional error details

        Returns:
            JSONResponse: Error response
        """
        error_response = {
            "error": {
                "type": error_type,
                "message": message,
                "status_code": status_code,
            }
        }

        if details:
            error_response["error"]["details"] = details

        return JSONResponse(status_code=status_code, content=error_response)

    @staticmethod
    def handle_domain_exception(exc: DomainException) -> JSONResponse:
        """
        Handle domain exceptions.

        Args:
            exc: Domain exception

        Returns:
            JSONResponse: Error response
        """
        if isinstance(exc, ProductNotFound):
            return CatalogErrorResponse.create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                error_type="ProductNotFound",
                message=str(exc),
                details={"product_id": getattr(exc, "product_id", None)},
            )

        elif isinstance(exc, ProductNotFoundBySku):
            return CatalogErrorResponse.create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                error_type="ProductNotFoundBySku",
                message=str(exc),
                details={"sku": getattr(exc, "sku", None)},
            )

        elif isinstance(exc, ProductNotFoundByName):
            return CatalogErrorResponse.create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                error_type="ProductNotFoundByName",
                message=str(exc),
                details={"name": getattr(exc, "name", None)},
            )

        elif isinstance(exc, ProductAlreadyExists):
            return CatalogErrorResponse.create_error_response(
                status_code=status.HTTP_409_CONFLICT,
                error_type="ProductAlreadyExists",
                message=str(exc),
                details={"sku": getattr(exc, "sku", None)},
            )

        elif isinstance(exc, ProductWithNameAlreadyExists):
            return CatalogErrorResponse.create_error_response(
                status_code=status.HTTP_409_CONFLICT,
                error_type="ProductWithNameAlreadyExists",
                message=str(exc),
                details={"name": getattr(exc, "name", None)},
            )

        elif isinstance(exc, InvalidPrice):
            return CatalogErrorResponse.create_error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                error_type="InvalidPrice",
                message=str(exc),
                details={"price": getattr(exc, "price", None)},
            )

        else:
            # Generic domain exception
            return CatalogErrorResponse.create_error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                error_type="DomainException",
                message=str(exc),
            )

    @staticmethod
    def handle_validation_error(exc: Exception) -> JSONResponse:
        """
        Handle validation errors.

        Args:
            exc: Validation exception

        Returns:
            JSONResponse: Error response
        """
        return CatalogErrorResponse.create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_type="ValidationError",
            message="Validation failed",
            details={"error": str(exc)},
        )

    @staticmethod
    def handle_internal_error(exc: Exception) -> JSONResponse:
        """
        Handle internal server errors.

        Args:
            exc: Internal exception

        Returns:
            JSONResponse: Error response
        """
        logger.error(f"Internal server error: {exc}", exc_info=True)

        return CatalogErrorResponse.create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_type="InternalServerError",
            message="An internal server error occurred",
        )


async def catalog_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:  # noqa: ARG001
    """
    Global exception handler for catalog module.

    Args:
        request: FastAPI request
        exc: Exception

    Returns:
        JSONResponse: Error response
    """
    if isinstance(exc, DomainException):
        return CatalogErrorResponse.handle_domain_exception(exc)

    elif isinstance(exc, HTTPException):
        return CatalogErrorResponse.create_error_response(
            status_code=exc.status_code, error_type="HTTPException", message=exc.detail
        )

    elif "validation" in str(type(exc)).lower():
        return CatalogErrorResponse.handle_validation_error(exc)

    else:
        return CatalogErrorResponse.handle_internal_error(exc)


# Common HTTP exceptions for catalog module
class CatalogHTTPExceptions:
    """Common HTTP exceptions for catalog module."""

    @staticmethod
    def product_not_found(product_id: str) -> HTTPException:
        """Product not found exception."""
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    @staticmethod
    def product_not_found_by_sku(sku: str) -> HTTPException:
        """Product not found by SKU exception."""
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with SKU {sku} not found",
        )

    @staticmethod
    def product_already_exists(sku: str) -> HTTPException:
        """Product already exists exception."""
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product with SKU {sku} already exists",
        )

    @staticmethod
    def invalid_price(price: str) -> HTTPException:
        """Invalid price exception."""
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid price: {price}"
        )

    @staticmethod
    def validation_error(message: str) -> HTTPException:
        """Validation error exception."""
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {message}",
        )

    @staticmethod
    def unauthorized() -> HTTPException:
        """Unauthorized exception."""
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    @staticmethod
    def forbidden() -> HTTPException:
        """Forbidden exception."""
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )
