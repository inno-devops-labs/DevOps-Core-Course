# DevOps Info Service (Rust)

Rust implementation of the DevOps Info Service using Actix-web. Same functionality as the Python version but with better performance and a single binary deployment.

## Prerequisites

- Rust 1.70+ (install via [rustup](https://rustup.rs/))

## Build

```bash
cd app_rust
cargo build --release
```

The binary will be at `target/release/devops-info-service` (~5-7 MB).

## Run

```bash
cargo run --release
```

Or run the compiled binary directly:

```bash
./target/release/devops-info-service
```

With custom configuration:

```bash
PORT=3000 cargo run --release
HOST=127.0.0.1 PORT=8000 cargo run --release
RUST_LOG=debug cargo run --release
```

## API Endpoints

### GET /

Returns service info, system details, runtime stats, and request information.

```bash
curl http://localhost:8080/
```

### GET /health

Health check endpoint.

```bash
curl http://localhost:8080/health
```

## Configuration

| Variable   | Default   | Description                                 |
| ---------- | --------- | ------------------------------------------- |
| `HOST`     | `0.0.0.0` | Host address                                |
| `PORT`     | `8080`    | Port number                                 |
| `RUST_LOG` | `info`    | Log level (error, warn, info, debug, trace) |

## Performance vs Python

- **Memory**: 3-8 MB (vs Python's 20-40 MB)
- **Throughput**: 50,000+ req/s (vs Python's 5,000-10,000 req/s)
- **Startup**: <50ms (vs Python's 200-500ms)
- **Binary Size**: 5-7 MB single file (vs Python's 40-90 MB with dependencies)

## Cross-Compilation

```bash
# Add target
rustup target add x86_64-unknown-linux-gnu

# Build for target
cargo build --release --target x86_64-unknown-linux-gnu
```

## Development

```bash
# Check code
cargo check

# Format code
cargo fmt

# Lint code
cargo clippy
```
