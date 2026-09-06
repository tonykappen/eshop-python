"""Tests for validation framework."""

from dataclasses import dataclass

from app.core.validation.validators import (
    AbstractValidator,
    GreaterThanRule,
    NotEmptyListRule,
    NotEmptyRule,
    ValidationResult,
)


@dataclass
class SampleCommand:
    name: str
    price: float
    categories: list[str]


class SampleValidator(AbstractValidator[SampleCommand]):
    def __init__(self) -> None:
        super().__init__()
        self.rule_for("name").not_empty()
        self.rule_for("price").greater_than(0)
        self.rule_for("categories").not_empty_list()


class TestValidationRules:
    def test_not_empty_rule(self) -> None:
        rule = NotEmptyRule("name")
        assert rule.validate("") == ["name is required"]
        assert rule.validate("ok") == []

    def test_greater_than_rule(self) -> None:
        rule = GreaterThanRule("price", 0)
        assert rule.validate(0) != []
        assert rule.validate(1.5) == []
        assert rule.validate("bad") != []

    def test_not_empty_list_rule(self) -> None:
        rule = NotEmptyListRule("categories")
        assert rule.validate([]) != []
        assert rule.validate(["a"]) == []


class TestAbstractValidator:
    def test_validate_success(self) -> None:
        validator = SampleValidator()
        cmd = SampleCommand(name="Widget", price=10, categories=["tools"])
        assert validator.validate(cmd) == []

    def test_validate_failure(self) -> None:
        validator = SampleValidator()
        cmd = SampleCommand(name="", price=-1, categories=[])
        errors = validator.validate(cmd)
        assert len(errors) >= 3


class TestValidationResult:
    def test_success_and_failure(self) -> None:
        ok = ValidationResult.success()
        bad = ValidationResult.failure(["error"])
        assert ok.is_valid is True
        assert bad.is_valid is False
        assert bad.errors == ["error"]
