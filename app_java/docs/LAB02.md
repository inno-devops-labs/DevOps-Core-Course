# Lab 2: Docker Containerization (Bonus Task)

## Multi-Stage Build Strategy

A multi-stage build is employed to create an optimized and secure Docker image for the Java application. This strategy involves two distinct stages:

-   **Stage 1 (Builder)**: This stage uses the `maven:3.9.6-eclipse-temurin-21` image, which is a comprehensive environment containing the full JDK 21 and Maven build tools. Its purpose is to compile the Java source code and package the application into an executable JAR file.

-   **Stage 2 (Runtime)**: This stage is based on the `eclipse-temurin:21-jre-jammy` image. This is a minimal image that includes only the Java 21 Runtime Environment (JRE), which is all that's needed to run the application. The compiled JAR file from the `builder` stage is copied into this final stage.

This separation ensures that the final production image is lightweight and does not contain any build-time dependencies, compilers, or source code, significantly reducing its size and potential attack surface.

## Image Size Comparison

-   **Builder Image (`maven:3.9.6-eclipse-temurin-21`):** 770MB
-   **Final Image (`112005/devops-java-app:latest`):** 487MB

The multi-stage build provides a significant size reduction of approximately 283MB (a ~37% reduction). This optimization is crucial for production environments as it leads to faster image pulls, reduced storage costs in container registries, and a smaller attack surface.

## Build & Run Process

### Build Output

The image was built successfully using the multi-stage Dockerfile after correcting the Java version mismatch.

```
[+] Building 11.1s (17/17) FINISHED
 => [internal] load build definition from Dockerfile
 => => transferring dockerfile: 819B
 => [internal] load metadata for docker.io/library/eclipse-temurin:21-jre-jammy
 => [internal] load metadata for docker.io/library/maven:3.9.6-eclipse-temurin-21
 => [internal] load .dockerignore
 => => transferring context: 246B
 => [builder 1/6] FROM docker.io/library/maven:3.9.6-eclipse-temurin-21
 => [stage-1 1/4] FROM docker.io/library/eclipse-temurin:21-jre-jammy
 => [internal] load build context
 => => transferring context: 13.31kB
 => [stage-1 2/4] RUN useradd --create-home appuser
 => [builder 2/6] WORKDIR /app
 => [builder 3/6] COPY pom.xml .
 => [builder 4/6] RUN mvn dependency:go-offline
 => [builder 5/6] COPY src ./src
 => [builder 6/6] RUN mvn package -DskipTests
 => [stage-1 3/4] COPY --from=builder /app/target/*.jar /app/app.jar
 => [stage-1 4/4] RUN chown appuser:appuser /app/app.jar
 => exporting to image
 => => exporting layers
 => => writing image sha256:2e9b1d2...
 => => naming to docker.io/112005/devops-java-app:latest
```

### Run and Test Output

The container was started, and the application endpoint was tested successfully after a 15-second delay to allow for startup.

```bash
$ docker run -d -p 8082:8080 --name devops-java-app 112005/devops-java-app:latest
eb450ae4f7f1a653317caf7dff5c21e41cafa16e3da88efcae639bc20a53a036

$ Start-Sleep -Seconds 15; curl http://localhost:8082/ -UseBasicParsing

StatusCode        : 200
StatusDescription :
Content           : {"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps c
                    ourse info service","framework":"Spring Boot"},"system":{"hostname":"eb450ae4f7f1"
                    ...}}
```

## Technical Explanation

The multi-stage `Dockerfile` works by defining multiple `FROM` instructions. Each `FROM` starts a new, independent stage. The `COPY --from=<stage_name>` instruction is the key that allows us to selectively copy artifacts from a previous stage into the current one. By copying only the final compiled JAR from the `builder` stage to the lean `runtime` stage, we create a final image that is optimized for production.

## Security Benefits

The most significant security benefit is the **reduced attack surface**. The final image lacks compilers, build tools (like Maven), and source code. This means that if an attacker were to gain access to the running container, they would have a very limited set of tools at their disposal, making it much harder to explore the environment, compile exploits, or reverse-engineer the application.
