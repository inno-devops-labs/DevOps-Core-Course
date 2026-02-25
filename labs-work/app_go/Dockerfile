FROM golang:1.21-alpine AS builder

WORKDIR /build

COPY go.mod .
COPY main.go .

RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o devops-info-service .

FROM scratch

WORKDIR /app

COPY --from=builder /build/devops-info-service .

EXPOSE 8080

ENTRYPOINT ["/app/devops-info-service"]
