"""FluentValidation equivalent for Python - Command and Query validation."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class ValidationRule(ABC):
    """Base class for validation rules."""

    @abstractmethod
    def validate(self, value: Any) -> list[str]:
        """Validate a value and return list of error messages."""
        pass


class NotEmptyRule(ValidationRule):
    """Rule to validate that a value is not empty."""

    def __init__(self, field_name: str, custom_message: str | None = None) -> None:
        """Initialize the rule."""
        self.field_name = field_name
        self.custom_message = custom_message or f"{field_name} is required"

    def validate(self, value: Any) -> list[str]:
        """Validate that value is not empty."""
        if not value or (isinstance(value, str) and not value.strip()):
            return [self.custom_message]
        return []


class GreaterThanRule(ValidationRule):
    """Rule to validate that a numeric value is greater than a threshold."""

    def __init__(
        self, field_name: str, threshold: float, custom_message: str | None = None
    ) -> None:
        """Initialize the rule."""
        self.field_name = field_name
        self.threshold = threshold
        self.custom_message = custom_message or f"{field_name} must be greater than {threshold}"

    def validate(self, value: Any) -> list[str]:
        """Validate that value is greater than threshold."""
        try:
            numeric_value = float(value)
            if numeric_value <= self.threshold:
                return [self.custom_message]
        except (ValueError, TypeError):
            return [f"{self.field_name} must be a valid number"]
        return []


class NotEmptyListRule(ValidationRule):
    """Rule to validate that a list is not empty."""

    def __init__(self, field_name: str, custom_message: str | None = None) -> None:
        """Initialize the rule."""
        self.field_name = field_name
        self.custom_message = custom_message or f"{field_name} must have at least one item"

    def validate(self, value: Any) -> list[str]:
        """Validate that list is not empty."""
        if not isinstance(value, list) or len(value) == 0:
            return [self.custom_message]
        return []


class AbstractValidator(ABC, Generic[T]):
    """Abstract base class for validators - matches .NET AbstractValidator pattern."""

    def __init__(self) -> None:
        """Initialize the validator."""
        self._rules: dict[str, list[ValidationRule]] = {}

    def rule_for(self, field_name: str) -> "RuleBuilder":
        """Create a rule builder for a field - matches .NET RuleFor pattern."""
        return RuleBuilder(self, field_name)

    def validate(self, obj: T) -> list[str]:
        """Validate an object and return list of error messages."""
        errors = []
        
        for field_name, rules in self._rules.items():
            value = getattr(obj, field_name, None)
            for rule in rules:
                field_errors = rule.validate(value)
                errors.extend(field_errors)
        
        return errors

    def add_rule(self, field_name: str, rule: ValidationRule) -> None:
        """Add a validation rule for a field."""
        if field_name not in self._rules:
            self._rules[field_name] = []
        self._rules[field_name].append(rule)


class RuleBuilder:
    """Builder for validation rules - matches .NET FluentValidation pattern."""

    def __init__(self, validator: AbstractValidator, field_name: str) -> None:
        """Initialize the rule builder."""
        self.validator = validator
        self.field_name = field_name

    def not_empty(self, custom_message: str | None = None) -> "RuleBuilder":
        """Add a not empty rule."""
        rule = NotEmptyRule(self.field_name, custom_message)
        self.validator.add_rule(self.field_name, rule)
        return self

    def greater_than(self, threshold: float, custom_message: str | None = None) -> "RuleBuilder":
        """Add a greater than rule."""
        rule = GreaterThanRule(self.field_name, threshold, custom_message)
        self.validator.add_rule(self.field_name, rule)
        return self

    def not_empty_list(self, custom_message: str | None = None) -> "RuleBuilder":
        """Add a not empty list rule."""
        rule = NotEmptyListRule(self.field_name, custom_message)
        self.validator.add_rule(self.field_name, rule)
        return self


class ValidationResult:
    """Result of validation - matches .NET ValidationResult pattern."""

    def __init__(self, is_valid: bool, errors: list[str]) -> None:
        """Initialize validation result."""
        self.is_valid = is_valid
        self.errors = errors

    @classmethod
    def success(cls) -> "ValidationResult":
        """Create a successful validation result."""
        return cls(True, [])

    @classmethod
    def failure(cls, errors: list[str]) -> "ValidationResult":
        """Create a failed validation result."""
        return cls(False, errors)
