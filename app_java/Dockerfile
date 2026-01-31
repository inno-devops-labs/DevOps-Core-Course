FROM eclipse-temurin:21-jdk AS builder

WORKDIR /app
COPY Main.java ./
RUN javac Main.java

# Create a minimal custom JRE to reduce final image size
RUN jlink \
    --add-modules java.base,java.net.http,jdk.httpserver \
    --strip-debug \
    --no-man-pages \
    --no-header-files \
    --compress=2 \
    --output /opt/jre

FROM debian:bookworm-slim

WORKDIR /app
COPY --from=builder /opt/jre /opt/jre
RUN groupadd --system appuser && useradd --system --gid appuser --create-home appuser
COPY --from=builder /app/Main.class ./
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8080
CMD ["/opt/jre/bin/java", "Main"]
