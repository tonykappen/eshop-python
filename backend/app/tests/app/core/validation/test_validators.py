"""Tests for validation validators."""

import pytest

from app.core.validation.validators import (
    AbstractValidator,
    GreaterThanRule,
    NotEmptyListRule,
    NotEmptyRule,
    RuleBuilder,
    ValidationResult,
    ValidationRule,
)


class TestValidationRule:
    """Test ValidationRule base class."""

    def test_validation_rule_is_abstract(self) -> None:
        """Test that ValidationRule is an abstract base class."""
        with pytest.raises(TypeError):
            ValidationRule()  # Should raise TypeError for abstract class


class TestNotEmptyRule:
    """Test NotEmptyRule."""

    def test_not_empty_rule_with_valid_value(self) -> None:
        """Test NotEmptyRule with valid (non-empty) value."""
        rule = NotEmptyRule("name")
        errors = rule.validate("John Doe")
        
        assert errors == []

    def test_not_empty_rule_with_empty_string(self) -> None:
        """Test NotEmptyRule with empty string."""
        rule = NotEmptyRule("name")
        errors = rule.validate("")
        
        assert len(errors) == 1
        assert "name is required" in errors[0]

    def test_not_empty_rule_with_whitespace_string(self) -> None:
        """Test NotEmptyRule with whitespace-only string."""
        rule = NotEmptyRule("name")
        errors = rule.validate("   ")
        
        assert len(errors) == 1
        assert "name is required" in errors[0]

    def test_not_empty_rule_with_none(self) -> None:
        """Test NotEmptyRule with None value."""
        rule = NotEmptyRule("name")
        errors = rule.validate(None)
        
        assert len(errors) == 1
        assert "name is required" in errors[0]

    def test_not_empty_rule_with_custom_message(self) -> None:
        """Test NotEmptyRule with custom error message."""
        rule = NotEmptyRule("name", custom_message="Custom error message")
        errors = rule.validate("")
        
        assert len(errors) == 1
        assert errors[0] == "Custom error message"

    def test_not_empty_rule_with_empty_list(self) -> None:
        """Test NotEmptyRule with empty list."""
        rule = NotEmptyRule("items")
        errors = rule.validate([])
        
        assert len(errors) == 1


class TestGreaterThanRule:
    """Test GreaterThanRule."""

    def test_greater_than_rule_with_valid_value(self) -> None:
        """Test GreaterThanRule with valid value."""
        rule = GreaterThanRule("price", 10.0)
        errors = rule.validate(15.0)
        
        assert errors == []

    def test_greater_than_rule_with_equal_value(self) -> None:
        """Test GreaterThanRule with equal value (should fail)."""
        rule = GreaterThanRule("price", 10.0)
        errors = rule.validate(10.0)
        
        assert len(errors) == 1
        assert "price must be greater than 10.0" in errors[0]

    def test_greater_than_rule_with_lesser_value(self) -> None:
        """Test GreaterThanRule with lesser value."""
        rule = GreaterThanRule("price", 10.0)
        errors = rule.validate(5.0)
        
        assert len(errors) == 1
        assert "price must be greater than 10.0" in errors[0]

    def test_greater_than_rule_with_string_number(self) -> None:
        """Test GreaterThanRule with string number."""
        rule = GreaterThanRule("price", 10.0)
        errors = rule.validate("15.5")
        
        assert errors == []

    def test_greater_than_rule_with_invalid_string(self) -> None:
        """Test GreaterThanRule with invalid string."""
        rule = GreaterThanRule("price", 10.0)
        errors = rule.validate("not-a-number")
        
        assert len(errors) == 1
        assert "price must be a valid number" in errors[0]

    def test_greater_than_rule_with_none(self) -> None:
        """Test GreaterThanRule with None value."""
        rule = GreaterThanRule("price", 10.0)
        errors = rule.validate(None)
        
        assert len(errors) == 1
        assert "price must be a valid number" in errors[0]

    def test_greater_than_rule_with_custom_message(self) -> None:
        """Test GreaterThanRule with custom error message."""
        rule = GreaterThanRule("price", 10.0, custom_message="Price too low")
        errors = rule.validate(5.0)
        
        assert len(errors) == 1
        assert errors[0] == "Price too low"


class TestNotEmptyListRule:
    """Test NotEmptyListRule."""

    def test_not_empty_list_rule_with_valid_list(self) -> None:
        """Test NotEmptyListRule with valid (non-empty) list."""
        rule = NotEmptyListRule("items")
        errors = rule.validate([1, 2, 3])
        
        assert errors == []

    def test_not_empty_list_rule_with_empty_list(self) -> None:
        """Test NotEmptyListRule with empty list."""
        rule = NotEmptyListRule("items")
        errors = rule.validate([])
        
        assert len(errors) == 1
        assert "items must have at least one item" in errors[0]

    def test_not_empty_list_rule_with_none(self) -> None:
        """Test NotEmptyListRule with None value."""
        rule = NotEmptyListRule("items")
        errors = rule.validate(None)
        
        assert len(errors) == 1
        assert "items must have at least one item" in errors[0]

    def test_not_empty_list_rule_with_non_list(self) -> None:
        """Test NotEmptyListRule with non-list value."""
        rule = NotEmptyListRule("items")
        errors = rule.validate("not-a-list")
        
        assert len(errors) == 1

    def test_not_empty_list_rule_with_custom_message(self) -> None:
        """Test NotEmptyListRule with custom error message."""
        rule = NotEmptyListRule("items", custom_message="List cannot be empty")
        errors = rule.validate([])
        
        assert len(errors) == 1
        assert errors[0] == "List cannot be empty"


class TestAbstractValidator:
    """Test AbstractValidator."""

    class SampleModel:
        """Sample model for testing."""

        def __init__(self, name: str, price: float, items: list) -> None:
            self.name = name
            self.price = price
            self.items = items

    class SampleValidator(AbstractValidator[SampleModel]):
        """Sample validator for testing."""

        def __init__(self) -> None:
            super().__init__()
            self.rule_for("name").not_empty()
            self.rule_for("price").greater_than(0.0)
            self.rule_for("items").not_empty_list()

    def test_validator_with_valid_object(self) -> None:
        """Test validator with valid object."""
        validator = self.SampleValidator()
        obj = self.SampleModel("Product", 10.0, [1, 2, 3])
        
        errors = validator.validate(obj)
        
        assert errors == []

    def test_validator_with_invalid_object(self) -> None:
        """Test validator with invalid object."""
        validator = self.SampleValidator()
        obj = self.SampleModel("", -5.0, [])
        
        errors = validator.validate(obj)
        
        assert len(errors) == 3
        assert any("name is required" in error for error in errors)
        assert any("price must be greater than 0.0" in error for error in errors)
        assert any("items must have at least one item" in error for error in errors)

    def test_validator_with_partial_errors(self) -> None:
        """Test validator with partial errors."""
        validator = self.SampleValidator()
        obj = self.SampleModel("Product", -5.0, [1, 2])
        
        errors = validator.validate(obj)
        
        assert len(errors) == 1
        assert "price must be greater than 0.0" in errors[0]

    def test_validator_with_missing_attribute(self) -> None:
        """Test validator with missing attribute."""
        validator = self.SampleValidator()
        
        class IncompleteModel:
            pass
        
        obj = IncompleteModel()
        errors = validator.validate(obj)
        
        # Should handle missing attributes gracefully
        assert len(errors) >= 1

    def test_validator_add_rule(self) -> None:
        """Test adding rules manually."""
        validator = self.SampleValidator()
        rule = NotEmptyRule("description")
        validator.add_rule("description", rule)
        
        obj = self.SampleModel("Product", 10.0, [1, 2, 3])
        # Add description attribute
        obj.description = ""  # type: ignore[attr-defined]
        
        errors = validator.validate(obj)
        
        assert len(errors) == 1
        assert "description is required" in errors[0]


class TestRuleBuilder:
    """Test RuleBuilder."""

    class TestValidator(AbstractValidator):
        """Test validator for RuleBuilder tests."""

        def __init__(self) -> None:
            super().__init__()

    def test_rule_builder_not_empty(self) -> None:
        """Test RuleBuilder.not_empty()."""
        validator = self.TestValidator()
        builder = validator.rule_for("name")
        
        result = builder.not_empty()
        
        assert isinstance(result, RuleBuilder)
        # Verify rule was added
        obj = type("Obj", (), {"name": ""})()
        errors = validator.validate(obj)
        assert len(errors) == 1

    def test_rule_builder_greater_than(self) -> None:
        """Test RuleBuilder.greater_than()."""
        validator = self.TestValidator()
        builder = validator.rule_for("price")
        
        result = builder.greater_than(10.0)
        
        assert isinstance(result, RuleBuilder)
        # Verify rule was added
        obj = type("Obj", (), {"price": 5.0})()
        errors = validator.validate(obj)
        assert len(errors) == 1

    def test_rule_builder_not_empty_list(self) -> None:
        """Test RuleBuilder.not_empty_list()."""
        validator = self.TestValidator()
        builder = validator.rule_for("items")
        
        result = builder.not_empty_list()
        
        assert isinstance(result, RuleBuilder)
        # Verify rule was added
        obj = type("Obj", (), {"items": []})()
        errors = validator.validate(obj)
        assert len(errors) == 1

    def test_rule_builder_chaining(self) -> None:
        """Test chaining multiple rules."""
        validator = self.TestValidator()
        
        validator.rule_for("name").not_empty()
        validator.rule_for("price").greater_than(0.0)
        
        obj = type("Obj", (), {"name": "", "price": -1.0})()
        errors = validator.validate(obj)
        
        assert len(errors) == 2


class TestValidationResult:
    """Test ValidationResult."""

    def test_validation_result_success(self) -> None:
        """Test creating successful validation result."""
        result = ValidationResult.success()
        
        assert result.is_valid is True
        assert result.errors == []

    def test_validation_result_failure(self) -> None:
        """Test creating failed validation result."""
        errors = ["Error 1", "Error 2"]
        result = ValidationResult.failure(errors)
        
        assert result.is_valid is False
        assert result.errors == errors

    def test_validation_result_constructor(self) -> None:
        """Test ValidationResult constructor."""
        result = ValidationResult(True, [])
        
        assert result.is_valid is True
        assert result.errors == []

    def test_validation_result_with_errors(self) -> None:
        """Test ValidationResult with errors."""
        errors = ["Field is required", "Value too low"]
        result = ValidationResult(False, errors)
        
        assert result.is_valid is False
        assert result.errors == errors
