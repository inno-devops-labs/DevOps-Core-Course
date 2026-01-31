FROM golang:1.21-alpine AS builder

WORKDIR /src

COPY go.mod ./
RUN go mod download

COPY main.go ./

RUN CGO_ENABLED=0 GOOS=linux go build -o devops-info-service main.go

FROM gcr.io/distroless/static:nonroot

WORKDIR /app

COPY --from=builder /src/devops-info-service /app/devops-info-service

EXPOSE 8080

USER nonroot

ENTRYPOINT ["/app/devops-info-service"]