"""Product command validators - matches .NET FluentValidation pattern."""

from uuid import UUID

from app.core.validation.validators import AbstractValidator, ValidationResult
from app.modules.catalog.application.features.products.commands.create_product.create_product_command import \
    CreateProductCommand
from app.modules.catalog.application.features.products.commands.delete_product.delete_product_command import \
    DeleteProductCommand
from app.modules.catalog.application.features.products.commands.update_product.update_product_command import \
    UpdateProductCommand


class CreateProductCommandValidator(AbstractValidator[CreateProductCommand]):
    """Validator for CreateProductCommand - matches .NET CreateProductCommandValidator."""

    def __init__(self) -> None:
        """Initialize the validator with rules."""
        super().__init__()
        self._setup_rules()

    def _setup_rules(self) -> None:
        """Setup validation rules for CreateProductCommand - matches .NET validation rules."""
        self.rule_for("product").not_empty("Product is required")
        self.rule_for("product.name").not_empty("Product name is required")
        self.rule_for("product.description").not_empty(
            "Product description is required"
        )
        self.rule_for("product.price").greater_than(
            0, "Product price must be greater than 0"
        )
        self.rule_for("product.picture_url").not_empty(
            "Product picture URL is required"
        )
        self.rule_for("product.category").not_empty("Product category is required")


class UpdateProductCommandValidator(AbstractValidator[UpdateProductCommand]):
    """Validator for UpdateProductCommand - matches .NET UpdateProductCommandValidator."""

    def __init__(self) -> None:
        """Initialize the validator with rules."""
        super().__init__()
        self._setup_rules()

    def _setup_rules(self) -> None:
        """Setup validation rules for UpdateProductCommand."""
        self.rule_for("id").not_empty("Id is required")
        self.rule_for("name").not_empty("Name is required")
        self.rule_for("description").not_empty("Description is required")
        self.rule_for("price").greater_than(0, "Price must be greater than 0")
        self.rule_for("picture_url").not_empty("Picture URL is required")
        self.rule_for("category").not_empty("Category is required")


class DeleteProductCommandValidator(AbstractValidator[DeleteProductCommand]):
    """Validator for DeleteProductCommand - matches .NET DeleteProductCommandValidator."""

    def __init__(self) -> None:
        """Initialize the validator with rules."""
        super().__init__()
        self._setup_rules()

    def _setup_rules(self) -> None:
        """Setup validation rules for DeleteProductCommand."""
        self.rule_for("product_id").not_empty("Product Id is required")


class ProductDtoValidator:
    """Validator for ProductDto - matches .NET ProductDto validation."""

    @staticmethod
    def validate_name(name: str) -> list[str]:
        """Validate product name."""
        if not name or not name.strip():
            return ["Name is required"]
        return []

    @staticmethod
    def validate_category(category: list[str]) -> list[str]:
        """Validate product category."""
        if not category:
            return ["Category is required"]
        return []

    @staticmethod
    def validate_image_file(image_file: str) -> list[str]:
        """Validate product image file."""
        if not image_file or not image_file.strip():
            return ["ImageFile is required"]
        return []

    @staticmethod
    def validate_price(price: float) -> list[str]:
        """Validate product price."""
        if price <= 0:
            return ["Price must be greater than 0"]
        return []

    @staticmethod
    def validate_description(description: str) -> list[str]:
        """Validate product description."""
        if not description or not description.strip():
            return ["Description is required"]
        return []

    @staticmethod
    def validate_id(product_id: UUID) -> list[str]:
        """Validate product ID."""
        if not product_id:
            return ["Id is required"]
        return []


def validate_create_product_command(command: CreateProductCommand) -> ValidationResult:
    """Validate CreateProductCommand and return result."""
    validator = CreateProductCommandValidator()
    errors = validator.validate(command)

    if errors:
        return ValidationResult.failure(errors)
    return ValidationResult.success()


def validate_update_product_command(command: UpdateProductCommand) -> ValidationResult:
    """Validate UpdateProductCommand and return result."""
    validator = UpdateProductCommandValidator()
    errors = validator.validate(command)

    if errors:
        return ValidationResult.failure(errors)
    return ValidationResult.success()


def validate_delete_product_command(command: DeleteProductCommand) -> ValidationResult:
    """Validate DeleteProductCommand and return result."""
    validator = DeleteProductCommandValidator()
    errors = validator.validate(command)

    if errors:
        return ValidationResult.failure(errors)
    return ValidationResult.success()
