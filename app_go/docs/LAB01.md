## Implementation Details

The Go version implements the same API structure as the Python service using the standard `net/http` package.

## Build Process
```bash
go build -o devops-info
```

## Binary Size Comparison

| Implementation | Size                         |
| -------------- | ---------------------------- |
| Python (Flask) | ~30–50 MB (with venv & deps) |
| Go binary      | ~7–10 MB                     |

The Go binary does not require an interpreter or external dependencies, making it more efficient for deployment.
