FROM golang:1.22 AS builder

WORKDIR /src

COPY go.mod ./
RUN go mod download

COPY main.go ./
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o devops-info

FROM gcr.io/distroless/static-debian12:nonroot

WORKDIR /app
COPY --from=builder /src/devops-info /app/devops-info

ENV HOST=0.0.0.0 \
    PORT=5000

EXPOSE 5000

ENTRYPOINT ["/app/devops-info"]
