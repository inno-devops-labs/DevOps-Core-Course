# Stage 1: Build
FROM golang:1.25-alpine AS builder

WORKDIR /app_go

COPY go.mod ./
RUN go mod download

COPY . .

RUN go build -o app

# Stage 2: Run
FROM alpine:latest

WORKDIR /app_go

COPY --from=builder /app_go/app .

EXPOSE 8080

USER nobody:nobody

CMD ["./app"]
