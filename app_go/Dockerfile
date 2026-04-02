FROM golang:1.24-alpine AS builder

WORKDIR /app
COPY go.mod .
COPY main.go .
RUN CGO_ENABLED=0 go build -o devops-info-service .

FROM alpine:3.21

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app
COPY --from=builder /app/devops-info-service .
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000

CMD ["./devops-info-service"]
