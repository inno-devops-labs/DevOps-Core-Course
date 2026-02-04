FROM golang:1.21-alpine AS builder

WORKDIR /src

COPY go.mod .
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /bin/devops-info-service main.go

FROM gcr.io/distroless/base-debian12 AS runtime

WORKDIR /app

COPY --from=builder /bin/devops-info-service /app/devops-info-service

EXPOSE 8080

ENV HOST=0.0.0.0 \
    PORT=8080

USER nonroot:nonroot

ENTRYPOINT ["/app/devops-info-service"]

