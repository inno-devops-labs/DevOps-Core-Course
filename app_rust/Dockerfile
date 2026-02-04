FROM rust:1.88-slim-bookworm AS builder

WORKDIR /app

COPY Cargo.toml Cargo.lock ./
COPY src ./src

RUN cargo build --release

FROM gcr.io/distroless/cc-debian12

WORKDIR /app

COPY --from=builder /app/target/release/devops-info-service /app/devops-info-service

USER 65532

EXPOSE 8080

CMD ["/app/devops-info-service"]
