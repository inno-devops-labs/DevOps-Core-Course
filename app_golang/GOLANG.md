# Golang Web App

## Best Practices

- **Separation of Concerns**: Logic in `utils/time_utils.go`, UI in `templates/index.html`.
- **Dependencies**: Managed with Go modules (`go mod`).
- **Version Control**: `.gitignore` to exclude unnecessary files.
- **Modular Design**: Handlers in `handlers/handler.go`, utilities in `utils/time_utils.go`.

## Coding Standards

- **Formatting**: `go fmt` and `golangci-lint` for consistent code.
- **Error Handling**: Check errors, especially in template rendering.
- **Naming**: Clear and descriptive names.

## Testing

- **Testing**: Use Go's built-in testing framework.
- **Tests**: Found in `handlers/handler_test.go` and `utils/time_utils_test.go`.

## Code Quality

- **Pre-commmit**: add pre-commit config with markdown linter, prettier,
  golang linters, formtatters, validators
- **Linting**: `golangci-lint` for code quality.
- **Test Coverage**: Ensures important logic is covered.
