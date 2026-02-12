FROM golang:1.21-alpine AS builder

WORKDIR /build

COPY go.mod .
COPY main.go .

RUN CGO_ENABLED=0 GOOS=linux go build -o devops-info-service

FROM scratch

COPY --from=builder /build/devops-info-service /devops-info-service

EXPOSE 8080

ENTRYPOINT ["/devops-info-service"]
