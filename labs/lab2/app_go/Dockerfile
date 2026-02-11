# -----------------------
# Stage 1: builder
# -----------------------
FROM golang:1.24-alpine AS builder

WORKDIR /src

# Copy and download deps first (layer caching)
COPY go.mod ./
RUN go mod download

# Copy the rest of the source
COPY . .

# Build a small static binary
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/devops-info-service .

# -----------------------
# Stage 2: runtime
# -----------------------
FROM alpine:3.20

# Create non-root user
RUN addgroup -S app && adduser -S app -G app

WORKDIR /app
COPY --from=builder /out/devops-info-service /app/devops-info-service

ENV HOST=0.0.0.0 PORT=8080
EXPOSE 8080

USER app
ENTRYPOINT ["/app/devops-info-service"]
