# Language Justification: Go

## Why Go

| Criteria            | Python (FastAPI) | Go (net/http)      | Java (Spring Boot) |
|---------------------|------------------|---------------------|---------------------|
| Binary size         | N/A (interpreted)| ~7 MB               | ~20 MB (fat JAR)    |
| Startup time        | ~1s              | Instant             | ~2-3s               |
| Dependencies        | pip + venv       | Zero (stdlib only)  | Maven + JDK         |
| Compilation speed   | N/A              | Very fast           | Moderate            |
| Memory usage        | Moderate         | Very low            | High                |
| Concurrency         | GIL-limited      | Goroutines (native) | Threads             |

## Reasons for Choosing Go

1. **Zero external dependencies** — the entire service is built using Go's standard library (`net/http`, `encoding/json`, `runtime`). No frameworks, no package managers, no dependency hell.

2. **Single static binary** — `go build` produces one executable with everything baked in. No runtime needed, no JVM, no interpreter. Just copy the binary and run it anywhere.

3. **Ideal for Docker** — small binary size and no runtime dependencies make for minimal Docker images. A multi-stage build with `FROM scratch` can produce images under 10 MB.

4. **Fast compilation** — the entire project compiles in under a second, making the development loop fast.

## Trade-offs

- **Verbosity** — Go requires explicit struct definitions with JSON tags. More typing than Python dicts, but safer.
- **No auto-docs** — unlike FastAPI's built-in Swagger, Go's stdlib has no API documentation generation.
- **Error handling** — Go uses explicit `if err != nil` patterns instead of exceptions. More boilerplate but more predictable.
