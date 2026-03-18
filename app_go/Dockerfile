# Multi-stage Dockerfile for Go app

# Builder stage: compile static binary
FROM golang:1.21-alpine AS builder

WORKDIR /src

# Download modules first to leverage caching (go.sum may not be present)
COPY go.mod ./
RUN go mod download || go mod tidy

# Copy source and build a statically-linked binary
COPY . .
# Build with no cgo, target linux/amd64, strip symbols
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -ldflags='-s -w' -o /out/devops-info-service ./

# Final stage: minimal runtime image with healthcheck tools
FROM alpine:3.20

RUN adduser -D -u 1000 app && apk add --no-cache wget ca-certificates

# Copy binary from builder stage
COPY --from=builder /out/devops-info-service /usr/local/bin/devops-info-service

# Expose the port and use a non-root numeric UID for runtime
EXPOSE 8080
USER 1000
ENTRYPOINT ["/usr/local/bin/devops-info-service"]
