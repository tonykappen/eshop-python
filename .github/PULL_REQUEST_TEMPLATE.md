## Description

<!-- Provide a clear and concise description of what this PR does -->

## Type of Change

<!-- Mark the relevant option with an "x" -->

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📝 Documentation update
- [ ] 🔧 Configuration change
- [ ] ♻️ Code refactoring
- [ ] ✅ Test updates
- [ ] 🎨 Style/formatting changes

## Motivation and Context

<!-- Why is this change required? What problem does it solve? -->
<!-- If it fixes an open issue, please link to the issue here -->

Fixes #(issue)

## How Has This Been Tested?

<!-- Describe the tests you ran to verify your changes -->
<!-- Provide instructions so reviewers can reproduce -->

- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing
- [ ] Test coverage maintained/improved (≥80%)

**Test Configuration**:
- Python version:
- Operating System:

## Screenshots (if applicable)

<!-- Add screenshots here if this is a UI change -->

## Checklist

<!-- Mark completed items with an "x" -->

### Code Quality

- [ ] My code follows the style guidelines of this project (Black, Ruff, isort)
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings or errors

### Testing

- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Test coverage is at least 80% (required by CI)
- [ ] I have run `pytest --cov=app --cov-fail-under=80` successfully

### Pre-commit Checks

- [ ] All pre-commit hooks pass (`poetry run pre-commit run --all-files`)
- [ ] Ruff linter passes (`poetry run ruff check .`)
- [ ] Black formatter passes (`poetry run black --check .`)
- [ ] isort passes (`poetry run isort --check-only .`)
- [ ] MyPy type checking passes (`poetry run mypy app --ignore-missing-imports`)
- [ ] Bandit security check passes (`poetry run bandit -r app`)

### CI/CD

- [ ] All GitHub Actions CI checks are passing
- [ ] No merge conflicts with target branch
- [ ] Branch is up to date with target branch

### Documentation

- [ ] I have updated the README.md if needed
- [ ] I have updated API documentation if needed
- [ ] I have added/updated docstrings for new/modified functions
- [ ] I have updated relevant markdown documentation

## Dependencies

<!-- List any new dependencies added -->

- [ ] No new dependencies added
- [ ] New dependencies added and justified below:

<!-- If you added new dependencies, explain why they are necessary -->

## Performance Impact

<!-- Describe any performance implications of this change -->

- [ ] No significant performance impact
- [ ] Performance improved
- [ ] Performance impact explained below:

## Security Considerations

<!-- Describe any security implications of this change -->

- [ ] No security impact
- [ ] Security improvements included
- [ ] Security considerations explained below:

## Breaking Changes

<!-- If this is a breaking change, describe the impact and migration path -->

- [ ] No breaking changes
- [ ] Breaking changes documented below:

## Additional Notes

<!-- Add any additional notes for reviewers -->

## Reviewer Checklist

<!-- For reviewers -->

- [ ] Code review completed
- [ ] Tests are adequate
- [ ] Documentation is clear
- [ ] No security concerns
- [ ] CI/CD pipeline passes

---

**By submitting this pull request, I confirm that:**

- [ ] I have read and followed the [Contributing Guidelines](../CONTRIBUTING.md)
- [ ] My code meets the project's quality standards
- [ ] I have tested my changes thoroughly
- [ ] I understand that this PR must pass all CI checks including 80% test coverage

