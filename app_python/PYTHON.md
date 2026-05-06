# Python Web Application

## Framework Choice

For this lab I used Flask via gunicorn because it is a simple and lightweight Python web framework.
It is a good choice for a small application that only needs to display the current time.

## Best Practices Used

- Dependencies are kept minimal.
- Runtime dependencies are separated from development dependencies.
- The application logic for Moscow time generation is separated into a dedicated function.
- The project structure is simple and clear.
- Tests are automated and can be executed locally and in CI.

## Coding Standards

- Code is written in PEP 8 format.
- Ruff is used as a linter.

## Testing

The application includes automated unit tests written with pytest.

Implemented tests:

- `test_get_moscow_time_format` checks that the Moscow time function returns time in the expected format.
- `test_index_returns_success_status_code` checks that the main route returns HTTP 200.
- `test_index_contains_expected_content` checks that the response contains the expected page text.
- `test_index_contains_time_value` checks that the page contains a generated time value.

Testing best practices used:

- Tests are isolated and do not require a running external server.
- Flask test client is used instead of manual browser checks.
- The time generation logic is separated into a function to make it easier to test.
- Tests validate both application logic and HTTP response behavior.
- Tests import the application as a normal Python package: `app_python.app`.

Run tests from the repository root:

```bash
python -m pytest app_python/tests -q
```

## Code Quality

Code quality is checked automatically in CI with Ruff.

Run linting from the repository root:

```bash
ruff check app_python
```
