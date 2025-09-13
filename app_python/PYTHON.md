# Python Web Application

## Best Practices

- Separation of Concerns: Logic in utilities/time_utils.py, UI in templates/index.html.
- Requirements File: Listed in requirements.txt.
- Virtual Environment: Setup instructions provided.
- pyproject.toml for Black configuration.
- .gitignore to exclude unnecessary files.

## Coding Standards

- Follows PEP 8 with Black formatting (88 chars max).
- Type Annotations
- Readable Naming

## Testing

### Best practices

- Pytest for unit tests.
- Tests in the tests/ directory.
- Mock modules for code that depends on them
- use `assert` for validation
- use regular expressions to validation

### Unit tests

- Add App test to test that web appliccation returns 200 with Moscow time
- Add unit tests with datetime module mock in order to
  test get_current_time_in_moscow() function

## Code Quality

- **Pre-commmit**: add pre-commit config with markdown linter, prettier,
  python linters, formtatters (mypy and black)
- Black: Automated formatting
