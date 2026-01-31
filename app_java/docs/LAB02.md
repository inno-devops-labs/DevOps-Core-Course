# Lab 02 — Bonus Multi-Stage Build (Java)

## Multi-Stage Build Strategy

- **Stage 1 (builder)**: `eclipse-temurin:21-jdk` compiles `Main.java` and runs `jlink` to produce a minimal custom JRE.
- **Stage 2 (runtime)**: `debian:bookworm-slim` includes only the custom JRE and compiled class for a smaller final image.

**Key Dockerfile steps:**
```dockerfile
FROM eclipse-temurin:21-jdk AS builder
WORKDIR /app
COPY Main.java ./
RUN javac Main.java
RUN jlink --add-modules java.base,java.net.http,jdk.httpserver \
    --strip-debug --no-man-pages --no-header-files --compress=2 \
    --output /opt/jre

FROM debian:bookworm-slim
WORKDIR /app
COPY --from=builder /opt/jre /opt/jre
COPY --from=builder /app/Main.class ./
CMD ["/opt/jre/bin/java", "Main"]
```

## Size Comparison

```
docker images devops-info-service-java --format "{{.Repository}}:{{.Tag}} {{.Size}}"
devops-info-service-java:builder 767MB
devops-info-service-java:lab02 198MB
```

- **Reduction**: 767MB → 198MB by removing the JDK toolchain and using a custom JRE.
- **Target met**: final image is under 200MB.
- **Why it matters**: smaller images pull faster, ship fewer components, and reduce attack surface.

## Build & Run Evidence

**Build output (excerpt):**
```
docker build -t devops-info-service-java:lab02 .
...
#12 [builder 4/4] RUN javac Main.java
#15 naming to docker.io/library/devops-info-service-java:lab02 done
```

**Container running (docker ps):**
```
CONTAINER ID   IMAGE                            COMMAND                     CREATED         STATUS         PORTS                    NAMES
758f21e07144   devops-info-service-java:lab02   "/opt/jre/bin/java M…"      2 seconds ago   Up 2 seconds   0.0.0.0:8080->8080/tcp   devops-info-service-java-lab02
```

**Endpoint tests:**
```
curl -s http://localhost:8080/health
{"status":"healthy","timestamp":"2026-01-31T10:33:52.944626139Z","uptime_seconds":2}
```

## Security and Trade-offs

- **Security**: non-root runtime user; smaller runtime image reduces attack surface.
- **Trade-offs**: two stages add complexity, but make images smaller and more secure.
