"""ORM mapping utilities for converting between Domain entities and SQLAlchemy ORM models."""

from datetime import datetime
from inspect import signature
from typing import Any, TypeVar, get_type_hints
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase

from app.core.domain.entity import Entity
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)

T = TypeVar("T")
DomainEntityType = TypeVar("DomainEntityType", bound=Entity)
ORMModelType = TypeVar("ORMModelType", bound=DeclarativeBase)


class ORMMapper:
    """Mapper for converting between Domain entities and ORM models."""

    @classmethod
    def to_orm(
        cls, domain_entity: DomainEntityType, orm_model_class: type[ORMModelType]
    ) -> ORMModelType:
        """Convert a domain entity to an ORM model."""
        if domain_entity is None:
            return None

        try:
            # Get the domain entity data
            if hasattr(domain_entity, "model_dump"):
                # Pydantic-based domain entity
                entity_data = domain_entity.model_dump(exclude={"domain_events"})
            elif hasattr(domain_entity, "items"):
                # Entity with items() method (prioritize this over __dict__)
                entity_data = dict(domain_entity.items())
            elif hasattr(domain_entity, "__dict__"):
                # Regular domain entity
                entity_data = {
                    k: v
                    for k, v in domain_entity.__dict__.items()
                    if not k.startswith("_") and k != "domain_events"
                }
            else:
                raise ValueError(
                    f"Cannot convert domain entity of type {type(domain_entity)}"
                )

            # Convert UUIDs to strings if needed
            entity_data = cls._convert_uuids_for_orm(entity_data)

            # Handle Product-specific conversions (domain to ORM)
            is_product = domain_entity.__class__.__name__ == "Product"

            if is_product:
                # Convert SKU value object to string
                if "sku" in entity_data:
                    sku_value = entity_data["sku"]
                    if hasattr(sku_value, "value"):  # SKU value object
                        entity_data["sku"] = sku_value.value
                    elif isinstance(sku_value, dict) and "value" in sku_value:
                        entity_data["sku"] = sku_value["value"]
                    elif isinstance(sku_value, str):
                        entity_data["sku"] = sku_value
                    else:
                        entity_data["sku"] = str(sku_value)

                # Convert Money value object to price_amount and price_currency
                if "price" in entity_data:
                    price_value = entity_data["price"]
                    if hasattr(price_value, "amount") and hasattr(
                        price_value, "currency"
                    ):
                        # Money value object
                        entity_data["price_amount"] = str(price_value.amount)
                        entity_data["price_currency"] = price_value.currency
                    elif isinstance(price_value, dict):
                        # Dictionary representation
                        entity_data["price_amount"] = str(price_value.get("amount", ""))
                        entity_data["price_currency"] = price_value.get(
                            "currency", "USD"
                        )
                    # Remove price field as it doesn't exist in ORM
                    entity_data.pop("price", None)

                # Map category (domain) to categories (ORM)
                if "category" in entity_data and "categories" not in entity_data:
                    entity_data["categories"] = entity_data.pop("category")

                # Set default audit fields if not present
                current_time = datetime.utcnow()
                if (
                    "created_at" not in entity_data
                    or entity_data.get("created_at") is None
                ):
                    entity_data["created_at"] = current_time
                if (
                    "updated_at" not in entity_data
                    or entity_data.get("updated_at") is None
                ):
                    entity_data["updated_at"] = current_time
                if (
                    "is_deleted" not in entity_data
                    or entity_data.get("is_deleted") is None
                ):
                    entity_data["is_deleted"] = False
                # Map last_modified (domain) to updated_at (ORM) if needed
                if "last_modified" in entity_data and "updated_at" not in entity_data:
                    entity_data["updated_at"] = (
                        entity_data.pop("last_modified") or current_time
                    )

            # Filter data to only include fields that exist in ORM model
            orm_fields = cls._get_orm_model_fields(orm_model_class)
            filtered_data = {k: v for k, v in entity_data.items() if k in orm_fields}

            # Create ORM model instance
            orm_instance = orm_model_class(**filtered_data)

            logger.log_debug_with_context(
                "Converted domain entity to ORM model",
                context={
                    "domain_entity_type": type(domain_entity).__name__,
                    "orm_model_type": orm_model_class.__name__
                }
            )
            return orm_instance

        except Exception as e:
            logger.log_error_with_context(
                "Failed to convert domain entity to ORM model",
                error=e,
                context={
                    "domain_entity_type": type(domain_entity).__name__,
                    "orm_model_type": orm_model_class.__name__
                }
            )
            raise ValueError(
                f"Failed to convert {type(domain_entity).__name__} to {orm_model_class.__name__}: {e}"
            ) from e

    @classmethod
    def from_orm(
        cls, orm_model: ORMModelType, domain_entity_class: type[DomainEntityType]
    ) -> DomainEntityType:
        """Convert an ORM model to a domain entity."""
        if orm_model is None:
            return None

        try:
            # Get ORM model data
            orm_data = cls._extract_orm_data(orm_model)

            # Convert data types for domain entity
            domain_data = cls._convert_types_for_domain(orm_data, domain_entity_class)

            # Create domain entity instance
            if issubclass(domain_entity_class, BaseModel):
                # Pydantic-based domain entity
                domain_entity = domain_entity_class(**domain_data)
            else:
                # Regular domain entity
                domain_entity = domain_entity_class(**domain_data)

            logger.log_debug_with_context(
                "Converted ORM model to domain entity",
                context={
                    "orm_model_type": type(orm_model).__name__,
                    "domain_entity_type": domain_entity_class.__name__
                }
            )
            return domain_entity

        except Exception as e:
            logger.log_error_with_context(
                "Failed to convert ORM model to domain entity",
                error=e,
                context={
                    "orm_model_type": type(orm_model).__name__,
                    "domain_entity_type": domain_entity_class.__name__
                }
            )
            raise ValueError(
                f"Failed to convert {type(orm_model).__name__} to {domain_entity_class.__name__}: {e}"
            ) from e

    @classmethod
    def to_orm_list(
        cls,
        domain_entities: list[DomainEntityType],
        orm_model_class: type[ORMModelType],
    ) -> list[ORMModelType]:
        """Convert a list of domain entities to ORM models."""
        if not domain_entities:
            return []
        return [cls.to_orm(entity, orm_model_class) for entity in domain_entities]

    @classmethod
    def from_orm_list(
        cls, orm_models: list[ORMModelType], domain_entity_class: type[DomainEntityType]
    ) -> list[DomainEntityType]:
        """Convert a list of ORM models to domain entities."""
        if not orm_models:
            return []
        return [cls.from_orm(model, domain_entity_class) for model in orm_models]

    @classmethod
    def update_orm_from_domain(
        cls, orm_model: ORMModelType, domain_entity: DomainEntityType
    ) -> ORMModelType:
        """Update an existing ORM model with data from a domain entity."""
        if domain_entity is None or orm_model is None:
            return orm_model

        try:
            # Get domain entity data
            if hasattr(domain_entity, "model_dump"):
                entity_data = domain_entity.model_dump(exclude={"domain_events"})
            else:
                entity_data = {
                    k: v
                    for k, v in domain_entity.__dict__.items()
                    if not k.startswith("_") and k != "domain_events"
                }

            # Convert UUIDs for ORM
            entity_data = cls._convert_uuids_for_orm(entity_data)

            # Handle Product-specific conversions (domain to ORM)
            is_product = domain_entity.__class__.__name__ == "Product"

            if is_product:
                # Convert SKU value object to string
                if "sku" in entity_data:
                    sku_value = entity_data["sku"]
                    if hasattr(sku_value, "value"):  # SKU value object
                        entity_data["sku"] = sku_value.value
                    elif isinstance(sku_value, dict) and "value" in sku_value:
                        entity_data["sku"] = sku_value["value"]
                    elif isinstance(sku_value, str):
                        entity_data["sku"] = sku_value
                    else:
                        entity_data["sku"] = str(sku_value)

                # Convert Money value object to price_amount and price_currency
                if "price" in entity_data:
                    price_value = entity_data["price"]
                    if hasattr(price_value, "amount") and hasattr(
                        price_value, "currency"
                    ):
                        # Money value object
                        entity_data["price_amount"] = str(price_value.amount)
                        entity_data["price_currency"] = price_value.currency
                    elif isinstance(price_value, dict):
                        # Dictionary representation
                        entity_data["price_amount"] = str(price_value.get("amount", ""))
                        entity_data["price_currency"] = price_value.get(
                            "currency", "USD"
                        )
                    # Remove price field as it doesn't exist in ORM
                    entity_data.pop("price", None)

                # Map category (domain) to categories (ORM)
                if "category" in entity_data and "categories" not in entity_data:
                    entity_data["categories"] = entity_data.pop("category")

                # Always update updated_at on update operations
                entity_data["updated_at"] = datetime.utcnow()
                # Map last_modified (domain) to updated_at (ORM) if present
                if "last_modified" in entity_data:
                    entity_data["updated_at"] = (
                        entity_data.pop("last_modified") or datetime.utcnow()
                    )

            # Update ORM model attributes
            orm_fields = cls._get_orm_model_fields(type(orm_model))
            for field_name, field_value in entity_data.items():
                if field_name in orm_fields and hasattr(orm_model, field_name):
                    setattr(orm_model, field_name, field_value)

            logger.log_debug_with_context(
                "Updated ORM model from domain entity",
                context={
                    "orm_model_type": type(orm_model).__name__,
                    "domain_entity_type": type(domain_entity).__name__
                }
            )
            return orm_model

        except Exception as e:
            logger.log_error_with_context(
                "Failed to update ORM model from domain entity",
                error=e,
                context={
                    "orm_model_type": type(orm_model).__name__,
                    "domain_entity_type": type(domain_entity).__name__
                }
            )
            raise ValueError(
                f"Failed to update {type(orm_model).__name__} from {type(domain_entity).__name__}: {e}"
            ) from e

    @staticmethod
    def _extract_orm_data(orm_model: Any) -> dict[str, Any]:
        """Extract data from ORM model."""
        data = {}

        # Get all columns from SQLAlchemy model
        if hasattr(orm_model, "__table__"):
            for column in orm_model.__table__.columns:
                column_name = column.name
                if hasattr(orm_model, column_name):
                    data[column_name] = getattr(orm_model, column_name)
        else:
            # Fallback to __dict__ if not a SQLAlchemy model
            data = {
                k: v for k, v in orm_model.__dict__.items() if not k.startswith("_")
            }

        return data

    @staticmethod
    def _get_orm_model_fields(orm_model_class: type[Any]) -> set[str]:
        """Get field names from ORM model class."""
        fields: set[str] = set()

        # Try SQLAlchemy table columns first
        if hasattr(orm_model_class, "__table__"):
            fields.update(column.name for column in orm_model_class.__table__.columns)

        # Fallback to constructor signature
        try:
            sig = signature(orm_model_class.__init__)
            fields.update(
                param.name for param in sig.parameters.values() if param.name != "self"
            )
        except Exception:  # nosec B110
            pass

        return fields

    @staticmethod
    def _convert_uuids_for_orm(data: dict[str, Any]) -> dict[str, Any]:
        """Convert UUID objects to strings for ORM storage."""
        converted: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, UUID):
                converted[key] = str(value)
            elif isinstance(value, list):
                # Convert list items, handling UUIDs to strings
                converted_list = []
                for item in value:
                    if isinstance(item, UUID):
                        converted_list.append(str(item))
                    else:
                        converted_list.append(item)
                converted[key] = converted_list
            else:
                converted[key] = value
        return converted

    @classmethod
    def _convert_types_for_domain(
        cls, data: dict[str, Any], domain_entity_class: type[Any]
    ) -> dict[str, Any]:
        """Convert ORM data types to domain entity types."""
        converted = {}

        # Get type hints from domain entity
        try:
            type_hints = get_type_hints(domain_entity_class)
        except Exception:
            type_hints = {}

        # For Pydantic models, use model fields; for regular classes, use constructor parameters
        if issubclass(domain_entity_class, BaseModel):
            # Use model fields for Pydantic models
            try:
                model_fields = domain_entity_class.model_fields
                valid_fields = set(model_fields.keys())
            except Exception:
                valid_fields = set()
        else:
            # Use constructor signature for regular classes
            try:
                sig = signature(domain_entity_class.__init__)
                valid_fields = set(sig.parameters.keys()) - {"self"}
            except Exception:
                valid_fields = set()

        # Handle Product-specific conversions
        is_product = domain_entity_class.__name__ == "Product"

        if is_product:
            # Convert sku string to SKU value object
            if "sku" in data and isinstance(data["sku"], str):
                try:
                    from app.modules.catalog.domain.value_objects import SKU

                    converted["sku"] = SKU(value=data["sku"])
                except Exception as e:
                    logger.log_warning_with_context(
                        "Failed to convert sku to SKU value object",
                        context={"error": str(e)}
                    )
                    # Fallback: try to use as-is, validation will catch it
                    converted["sku"] = data["sku"]

            # Convert price_amount and price_currency to Money value object
            if "price_amount" in data:
                try:
                    from decimal import Decimal

                    from app.modules.catalog.domain.value_objects import Money

                    price_amount = data["price_amount"]
                    price_currency = data.get("price_currency") or "USD"

                    # Convert price_amount to Decimal if it's a string
                    if isinstance(price_amount, str):
                        price_amount = Decimal(price_amount)
                    elif not isinstance(price_amount, Decimal):
                        price_amount = Decimal(str(price_amount))

                    converted["price"] = Money(
                        amount=price_amount, currency=price_currency
                    )
                except Exception as e:
                    logger.log_warning_with_context(
                        "Failed to convert price to Money value object",
                        context={"error": str(e)}
                    )
                    # Don't add price if conversion fails - let validation catch it

            # Map categories (ORM) to category (domain)
            if "categories" in data and "category" in valid_fields:
                converted["category"] = data["categories"]
            elif "categories" in data:
                # If domain expects "categories", use it directly
                converted["categories"] = data["categories"]

            # Map updated_at (ORM) to last_modified (domain Entity)
            if "updated_at" in data and "last_modified" in valid_fields:
                converted["last_modified"] = data["updated_at"]

        for key, value in data.items():
            # Skip fields we've already handled specially
            if is_product and key in (
                "sku",
                "price_amount",
                "price_currency",
                "categories",
                "updated_at",
            ):
                continue

            # Only include fields that exist in the domain entity
            if key in valid_fields:
                if key in type_hints:
                    expected_type = type_hints[key]
                    converted[key] = cls._convert_single_value(value, expected_type)
                else:
                    # Manual type conversion when get_type_hints fails
                    if key == "uuid_field" and isinstance(value, str):
                        converted[key] = UUID(value)
                    else:
                        converted[key] = value

        return converted

    @staticmethod
    def _convert_single_value(value: Any, expected_type: type[Any]) -> Any:
        """Convert a single value to the expected type."""
        if value is None:
            return None

        # Handle UUID conversion
        if expected_type == UUID or (
            hasattr(expected_type, "__origin__") and expected_type.__origin__ == UUID
        ):
            if isinstance(value, str):
                return UUID(value)
            elif isinstance(value, UUID):
                return value

        # Handle datetime
        if expected_type == datetime:
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            elif isinstance(value, datetime):
                return value

        # Handle optional types (Union[Type, None])
        if (
            (
                hasattr(expected_type, "__origin__")
                and expected_type.__origin__ == type(None)
            )
            or str(expected_type).startswith("typing.Union")
        ) and hasattr(expected_type, "__args__"):
            # For Union types, try the first non-None type
            for arg_type in expected_type.__args__:
                if arg_type != type(None):
                    try:
                        return ORMMapper._convert_single_value(value, arg_type)
                    except Exception:  # nosec B112
                        continue

        # Default: return as-is or try direct conversion
        try:
            if not isinstance(value, expected_type) and callable(expected_type):
                return expected_type(value)
        except Exception:  # nosec B110
            pass

        return value


# Convenience functions
def to_orm(
    domain_entity: DomainEntityType, orm_model_class: type[ORMModelType]
) -> ORMModelType:
    """Convert a domain entity to an ORM model."""
    return ORMMapper.to_orm(domain_entity, orm_model_class)


def from_orm(
    orm_model: ORMModelType, domain_entity_class: type[DomainEntityType]
) -> DomainEntityType:
    """Convert an ORM model to a domain entity."""
    return ORMMapper.from_orm(orm_model, domain_entity_class)


def to_orm_list(
    domain_entities: list[DomainEntityType], orm_model_class: type[ORMModelType]
) -> list[ORMModelType]:
    """Convert a list of domain entities to ORM models."""
    return ORMMapper.to_orm_list(domain_entities, orm_model_class)


def from_orm_list(
    orm_models: list[ORMModelType], domain_entity_class: type[DomainEntityType]
) -> list[DomainEntityType]:
    """Convert a list of ORM models to domain entities."""
    return ORMMapper.from_orm_list(orm_models, domain_entity_class)


def update_orm_from_domain(
    orm_model: ORMModelType, domain_entity: DomainEntityType
) -> ORMModelType:
    """Update an existing ORM model with data from a domain entity."""
    return ORMMapper.update_orm_from_domain(orm_model, domain_entity)
