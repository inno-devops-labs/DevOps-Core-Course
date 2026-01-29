## Multi-Stage Build (Java Spring Boot)

### Strategy (Why multi-stage)
I used a multi-stage Docker build because Docker allows multiple `FROM` stages and lets me copy only the build artifacts into the final runtime image using `COPY --from=...`, leaving behind the compiler/SDK and intermediate files.
This is important for compiled (or build-tool heavy) languages like Java because a builder image with Gradle + JDK is large, while the runtime image only needs a JRE-compatible environment and the final JAR. 

### Stage 1 — Builder
- Base: `gradle:8.13-jdk21`
- Purpose: compile and package the Spring Boot app (`bootJar`), producing a JAR in `build/libs/`.

Key caching decision:
- I copy `build.gradle.kts`, `settings.gradle.kts`, `gradle/`, and `gradlew` before copying `src/` so that dependency-related layers can be reused when I only change application code.

### Stage 2 — Runtime
- Base: `gcr.io/distroless/java21-debian12:nonroot`
- Purpose: run the compiled JAR with the Java runtime, without including build tools.

Why distroless:
Distroless images contain only the application and its runtime dependencies and do not include a shell or package manager, which reduces what is available inside the container at runtime.
I used the `:nonroot` variant to run the container as a non-root user by default.

### Size comparison (builder vs final)
Commands I used:
```bash
# Build only the builder stage (for size comparison)
docker build --target builder -t app_java:builder .

# Build the final runtime image
docker build -t app_java:runtime .

# Push to the hub
docker tag app_java:builder gghost1/app_java:builder
docker push gghost1/app_java:builder

docker tag app_java:runtime gghost1/app_java:runtime
docker push gghost1/app_java:runtime
```
**Results**:
- Builder image size: 624.97 MB
- Final runtime image size: 86.39 MB

Analysis:
The builder image is much larger because it contains Gradle and the full JDK toolchain, while the runtime image includes only what is needed to run the JAR plus the JAR itself.

Trade-offs and debugging
A trade-off of distroless is that it does not contain a shell, so interactive debugging inside the container is harder; distroless provides debug variants for debugging scenarios.
For production, I prefer the non-debug distroless runtime because it is minimal and reduces unnecessary tooling in the final image.

Docker Hub repository URL: https://hub.docker.com/r/gghost1/devops-lab-app-java

### Multi-stage builds matter for compiled languages
For compiled / build-tool-heavy stacks like Java (Gradle + JDK), a single-stage image would often ship the entire build toolchain (Gradle, compiler, caches) into production, which is unnecessarily large and increases what exists inside the container at runtime.
Multi-stage builds solve this by separating “build environment” and “runtime environment,” producing a smaller final image that contains only what is needed to run the already-built artifact.
This also improves security in practice because fewer tools and packages exist in the runtime image, which reduces the potential attack surface.

### Build output:
```terminaloutput
antipovd@Mac app_java % docker build -t devops-lab-app-java:1.0.0 .
[+] Building 70.5s (18/18) FINISHED                                                                                                                                                      docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                                                                                                     0.0s
 => => transferring dockerfile: 502B                                                                                                                                                                     0.0s 
 => [internal] load metadata for gcr.io/distroless/java21-debian12:nonroot                                                                                                                               2.0s 
 => [internal] load metadata for docker.io/library/gradle:8.13-jdk21                                                                                                                                     2.7s
 => [auth] library/gradle:pull token for registry-1.docker.io                                                                                                                                            0.0s
 => [internal] load .dockerignore                                                                                                                                                                        0.0s
 => => transferring context: 174B                                                                                                                                                                        0.0s 
 => [builder 1/8] FROM docker.io/library/gradle:8.13-jdk21@sha256:67b8c4bfd2b064e58a7307e2da1fc3881bc03ecc7a57cf61d8b570a02ebfaea2                                                                      19.6s 
 => => resolve docker.io/library/gradle:8.13-jdk21@sha256:67b8c4bfd2b064e58a7307e2da1fc3881bc03ecc7a57cf61d8b570a02ebfaea2                                                                               0.0s
 => => sha256:71a8b7fad68fc85eaee6cc7676712870dcfa1c968bb3763082b563db6c379028 59.53kB / 59.53kB                                                                                                         0.6s 
 ... (repeating)                                                                                                       8.4s
 => => sha256:49b96e96358d7aed127d4f4cd2294d77d497c683123bbad89fa80a83d8ef64aa 28.85MB / 28.85MB                                                                                                         3.3s
 => => extracting sha256:49b96e96358d7aed127d4f4cd2294d77d497c683123bbad89fa80a83d8ef64aa                                                                                                                0.3s
 ...                                                                                                             0.5s 
 => => extracting sha256:71a8b7fad68fc85eaee6cc7676712870dcfa1c968bb3763082b563db6c379028                                                                                                                0.0s 
 => [internal] load build context                                                                                                                                                                        0.0s 
 => => transferring context: 64.49kB                                                                                                                                                                     0.0s 
 => [stage-1 1/3] FROM gcr.io/distroless/java21-debian12:nonroot@sha256:a801e7ccb0606399ae950b0010b03261d4cee3d9866aa2930de6e0dcb4a5b0f5                                                                11.5s 
 => => resolve gcr.io/distroless/java21-debian12:nonroot@sha256:a801e7ccb0606399ae950b0010b03261d4cee3d9866aa2930de6e0dcb4a5b0f5                                                                         0.0s 
 => => sha256:7102060171e5d2a2c0f02f523912a62778fbab1d7abd7fee43a97ee39f79a6c9 59.45MB / 59.45MB                                                                                                        10.8s 
 ...                                                                                                       1.4s 
 => => sha256:d1c559a043f52900e1caad98278530ca55be2708a21a1d486f51109a79a5f4e5 104.22kB / 104.22kB                                                                                                       0.9s 
 => => extracting sha256:d1c559a043f52900e1caad98278530ca55be2708a21a1d486f51109a79a5f4e5                                                                                                                0.0s 
 ...                                                                                                             0.0s 
 => => extracting sha256:7102060171e5d2a2c0f02f523912a62778fbab1d7abd7fee43a97ee39f79a6c9                                                                                                                0.5s 
 => [stage-1 2/3] WORKDIR /app                                                                                                                                                                           0.3s 
 => [builder 2/8] WORKDIR /home/gradle/project                                                                                                                                                           0.4s 
 => [builder 3/8] COPY build.gradle.kts settings.gradle.kts gradle.properties* ./                                                                                                                        0.0s 
 => [builder 4/8] COPY gradle ./gradle                                                                                                                                                                   0.0s 
 => [builder 5/8] COPY gradlew ./                                                                                                                                                                        0.0s 
 => [builder 6/8] RUN ./gradlew --no-daemon dependencies || true                                                                                                                                        39.8s 
 => [builder 7/8] COPY src ./src                                                                                                                                                                         0.0s 
 => [builder 8/8] RUN ./gradlew --no-daemon clean bootJar                                                                                                                                                7.2s 
 => [stage-1 3/3] COPY --from=builder /home/gradle/project/build/libs/*.jar /app/app.jar                                                                                                                 0.0s 
 => exporting to image                                                                                                                                                                                   0.5s 
 => => exporting layers                                                                                                                                                                                  0.4s 
 => => exporting manifest sha256:70afed2532c3b2f772b1429130e008c37374ab6037eec196c840e8321041073f                                                                                                        0.0s 
 => => exporting config sha256:bfa435964c2136301877bc43fbe28d55df6e7a5a3d001f60009853ae72773d8c                                                                                                          0.0s 
 => => exporting attestation manifest sha256:820c286b3949c1dd3b9c485ffbe99fad7500c6ea6fa766d599dc6437b640435a                                                                                            0.0s 
 => => exporting manifest list sha256:d62d4f81f51b75a540746f277bae4d00967ab6461de78d9388e62be632938891                                                                                                   0.0s 
 => => naming to docker.io/library/devops-lab-app-java:1.0.0                                                                                                                                             0.0s 
 => => unpacking to docker.io/library/devops-lab-app-java:1.0.0                                                                                                                                          0.1s 
                                                                                                                                                                                                              
View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/aj8d7f9fo4hz3qliib5xv7gx1
```