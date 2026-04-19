FROM golang:1.22-alpine AS builder

WORKDIR /src

COPY go.mod ./

RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go mod download

COPY . .

RUN --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -trimpath -ldflags="-s -w" -buildvcs=false -o /out/app ./main.go

FROM gcr.io/distroless/static:nonroot

WORKDIR /app

COPY --from=builder /out/app /app/app

USER nonroot:nonroot

EXPOSE 5000

# Default envs (can be overridden at runtime)
ENV HOST=0.0.0.0 PORT=5000 DEBUG=false

# Run the binary
ENTRYPOINT ["/app/app"]
