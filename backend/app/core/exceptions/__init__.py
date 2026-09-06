"""Exception handling and custom exceptions."""

# Import common exceptions for backward compatibility
from app.core.exceptions.bad_request_exception import (BadRequestError,
                                                       BadRequestException)
from app.core.exceptions.common_exceptions import (BaseError,
                                                   ConfigurationError,
                                                   ConflictError,
                                                   ConnectionError,
                                                   DatabaseError,
                                                   DomainException,
                                                   ForbiddenError,
                                                   UnauthorizedError,
                                                   ValidationError)
from app.core.exceptions.internal_server_exception import (
    InternalServerError, InternalServerException)
from app.core.exceptions.not_found_exception import (NotFoundError,
                                                     NotFoundException)

__all__ = [
    # Base
    "BaseError",
    # Standardized exceptions
    "BadRequestException",
    "BadRequestError",
    "InternalServerException",
    "InternalServerError",
    "NotFoundException",
    "NotFoundError",
    # Other exceptions (for backward compatibility)
    "ValidationError",
    "UnauthorizedError",
    "ForbiddenError",
    "ConflictError",
    "DatabaseError",
    "ConnectionError",
    "ConfigurationError",
    "DomainException",
]
