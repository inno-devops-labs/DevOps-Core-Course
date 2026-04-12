FROM golang:1.22 AS builder
WORKDIR /app
COPY go.mod ./
RUN go mod download
COPY . .

RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -o info-service
FROM alpine:latest
RUN adduser -D appuser
WORKDIR /app
COPY --from=builder /app/info-service .
USER appuser
EXPOSE 5000
CMD ["./info-service"]
