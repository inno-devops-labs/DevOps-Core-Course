# ---------- Stage 1: Build ----------
# Use the full Go toolchain image only for compilation, which will take place in the /app directory
FROM golang:1.25.5-bookworm AS builder
WORKDIR /app

# Copy and install module metadata to use Docker layer caching (if go.sum appears later, this will speed up rebuilding).
COPY go.mod ./
RUN go mod download

# Copy the rest of the source code (excess code is filtered out by .dockerignore) and build the binary
COPY . .
RUN CGO_ENABLED=0 go build -o myapp .

# ---------- Stage 2: Runtime ----------
# Define the runtime environment (only necessary for running the binary).
FROM alpine:3.18

# Create an unprivileged user (does not run as root).
RUN adduser -D appuser

# Create an application directory inside the runtime container and copy the binary from the compilation environment into it (assigning the file to the appuser user)
WORKDIR /app
COPY --from=builder --chown=appuser:appuser /app/myapp .
USER appuser

EXPOSE 5000
CMD ["./myapp"]