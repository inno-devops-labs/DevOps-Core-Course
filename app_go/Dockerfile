# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

# Final stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates
RUN addgroup -g 10001 -S app && adduser -S -D -H -u 10001 -G app app

WORKDIR /app

COPY --from=builder /app/main .
RUN chown app:app /app/main && chmod 755 /app/main

USER 10001:10001

EXPOSE 8080

CMD ["./main"]
