# Multi-stage distroless build — see Lecture 2.
# Build context is this directory.

FROM golang:1.24 AS build
WORKDIR /src
COPY go.mod ./
COPY main.go ./
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /out/echo ./

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/echo /echo
EXPOSE 8081
USER nonroot:nonroot
ENTRYPOINT ["/echo"]
