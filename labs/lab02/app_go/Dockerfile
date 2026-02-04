FROM golang:1.23-alpine AS builder

RUN apk add --no-cache git

WORKDIR /build

COPY go.mod go.sum* ./

RUN go mod download

COPY main.go .

RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags="-w -s" \
    -o devops-info-service \
    main.go

FROM alpine:latest

RUN apk --no-cache add ca-certificates

RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

WORKDIR /app

COPY --from=builder /build/devops-info-service .

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

CMD ["./devops-info-service"]
