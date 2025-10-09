"""SKU (Stock Keeping Unit) value object for catalog domain."""

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator


class SKU(BaseModel):
    """SKU (Stock Keeping Unit) value object."""

    value: str = Field(..., description="SKU value")

    @field_validator("value")
    @classmethod
    def validate_sku(cls, v: str) -> str:
        """Validate SKU format."""
        if not v:
            raise ValueError("SKU cannot be empty")
        
        # Remove whitespace and convert to uppercase
        v = v.strip().upper()
        
        # SKU should be alphanumeric with optional hyphens and underscores
        if not re.match(r"^[A-Z0-9_-]+$", v):
            raise ValueError("SKU must contain only letters, numbers, hyphens, and underscores")
        
        # SKU should be between 3 and 50 characters
        if len(v) < 3 or len(v) > 50:
            raise ValueError("SKU must be between 3 and 50 characters")
        
        return v

    def __str__(self) -> str:
        """String representation of SKU."""
        return self.value

    def __eq__(self, other: Any) -> bool:
        """Equality comparison."""
        if not isinstance(other, SKU):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash(self.value)

    def __repr__(self) -> str:
        """Representation of SKU."""
        return f"SKU('{self.value}')"


