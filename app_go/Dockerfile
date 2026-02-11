FROM golang:1.25-alpine AS builder

WORKDIR /app

COPY go.mod ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o app

FROM alpine:3.19

WORKDIR /app

RUN adduser -D appuser
USER appuser

COPY --from=builder /app/app .

EXPOSE 5000

CMD ["./app"]
