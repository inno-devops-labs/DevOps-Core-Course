FROM golang:1.20-alpine AS builder
RUN apk add --no-cache git ca-certificates
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
ENV CGO_ENABLED=0 GOOS=linux GOARCH=amd64
RUN go build -ldflags="-s -w" -o /out/devops-info-service-go ./main.go

FROM alpine:3.18
RUN apk add --no-cache ca-certificates wget
RUN addgroup -S app && adduser -S -G app app
COPY --from=builder /out/devops-info-service-go /usr/local/bin/devops-info-service-go
RUN chown app:app /usr/local/bin/devops-info-service-go
USER app
WORKDIR /home/app
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD wget -qO- http://localhost:8080/health || exit 1
ENTRYPOINT ["/usr/local/bin/devops-info-service-go"]
