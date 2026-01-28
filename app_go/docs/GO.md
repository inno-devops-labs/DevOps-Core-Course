# GO.md — Why Go for the Bonus Task

## Why Go

Go is a compiled, statically typed language designed for building simple, fast, and reliable network services — which matches this lab perfectly.

Key reasons for choosing Go:

- **Small, self-contained binaries** — easy to ship in Docker images and ideal for multi-stage builds.
- **Fast compilation** — quick feedback loop while developing.
- **Standard library HTTP server** — `net/http` provides everything needed for simple REST-style services.
- **Cross-platform** — the same code works on macOS, Linux, and Windows with minimal changes.

## Comparison with Python Version

- **Startup**: the Go binary starts instantly, without requiring a virtual environment or interpreter.
- **Deployment**: shipping a single binary is often simpler than managing Python + dependencies.
- **Docker**: multi-stage builds can produce very small final images for Go services.

The Python implementation is still excellent for readability, teaching concepts, and rapid prototyping, while the Go version is closer to how small production microservices are often packaged for containers.


