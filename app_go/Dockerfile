# syntax=docker/dockerfile:1

# --- Stage 1: Builder ---
FROM golang:1.23.5-alpine3.21 AS builder

WORKDIR /src

# Cache deps first
COPY go.mod ./
RUN go mod download

# Copy source
COPY main.go ./

# Build a static binary (smaller + easier to run in minimal images)
ARG TARGETOS
ARG TARGETARCH

RUN CGO_ENABLED=0 GOOS=${TARGETOS:-linux} GOARCH=${TARGETARCH:-arm64} \
    go build -trimpath -ldflags="-s -w" -o /out/devops-info-service .

# --- Stage 2: Runtime (minimal, non-root) ---
FROM gcr.io/distroless/static-debian12:nonroot AS runtime

WORKDIR /app

COPY --from=builder /out/devops-info-service /app/devops-info-service

EXPOSE 8080

ENV HOST=0.0.0.0 \
    PORT=8080

# distroless:nonroot already runs as nonroot
ENTRYPOINT ["/app/devops-info-service"]
