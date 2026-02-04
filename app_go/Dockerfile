# DevOps Info Service — Go (Lab 2 Bonus)
# Multi-stage build: separate build environment from runtime

FROM golang:1.24-alpine AS builder

WORKDIR /build

COPY go.mod .
RUN go mod download

COPY main.go .

RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o devops-info-service .

FROM alpine:3.21

RUN addgroup -g 1000 appgroup && \
    adduser -D -u 1000 -G appgroup appuser

WORKDIR /app

COPY --from=builder /build/devops-info-service .

RUN chown appuser:appgroup devops-info-service

USER appuser

EXPOSE 5000

ENV PORT=5000 HOST=0.0.0.0

CMD ["./devops-info-service"]
