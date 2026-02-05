## Multi-stage Dockerfile for Go app

# Builder stage: use official Go image to compile a static Linux binary
FROM golang:1.22-alpine AS builder

WORKDIR /src

# Download dependencies separately to leverage caching
COPY go.mod ./
RUN apk add --no-cache git \
    && go mod tidy

# Copy source
COPY . .

# Build a statically linked binary for Linux
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -ldflags "-s -w" -o /devops-info ./

# Final stage: tiny runtime image
FROM scratch

# Copy binary from builder
COPY --from=builder /devops-info /devops-info

# Expose port and use non-root numeric UID
EXPOSE 5002
USER 1000

ENTRYPOINT ["/devops-info"]
