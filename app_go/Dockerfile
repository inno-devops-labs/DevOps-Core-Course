FROM golang:1.23-alpine AS builder

WORKDIR /src

COPY go.mod ./

RUN go mod download

COPY main.go ./

RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o /out/devops-info-service .

FROM scratch

USER 65532:65532

COPY --from=builder /out/devops-info-service /devops-info-service

EXPOSE 8080

ENTRYPOINT ["/devops-info-service"]