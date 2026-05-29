FROM golang:1.24 AS build
WORKDIR /src
COPY go.mod ./
COPY main.go ./
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /out/health ./

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/health /health
EXPOSE 8082
USER nonroot:nonroot
ENTRYPOINT ["/health"]
