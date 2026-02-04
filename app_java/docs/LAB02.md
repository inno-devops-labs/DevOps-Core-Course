## Multi-stage Build Strategy
Stage 1: Builder
Uses full Maven image with JDK 21

Installs all Maven dependencies

Compiles application into JAR file

Stage 2: Runtime
Uses minimal JRE Alpine image

Copies only the compiled JAR file


## Size Comparison
Image Sizes:
Builder stage: 1.04GB (Maven + JDK + dependencies)

Final image: 323MB

Space Savings:
Savings: ~742MB


## Why Multi-stage Builds Matter for Compiled Languages

Security: Fewer vulnerabilities in final image

Size: Significant size reduction

Attack surface: Only runtime environment present


## Teminal Output
docker build -t javaapp:1.0.0 .


```bash
[+] Building 173.1s (15/15) FINISHED                                                                                         docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                                         0.1s
 => => transferring dockerfile: 453B                                                                                                         0.0s 
 => [internal] load metadata for docker.io/library/maven:3.9.6-eclipse-temurin-21                                                            0.7s 
 => [internal] load metadata for docker.io/library/eclipse-temurin:21-jre-alpine                                                             0.7s 
 => [internal] load .dockerignore                                                                                                            0.0s
 => => transferring context: 157B                                                                                                            0.0s 
 => [builder 1/6] FROM docker.io/library/maven:3.9.6-eclipse-temurin-21@sha256:8d63d4c1902cb12d9e79a70671b18ebe26358cb592561af33ca1808f00d9  0.1s 
 => => resolve docker.io/library/maven:3.9.6-eclipse-temurin-21@sha256:8d63d4c1902cb12d9e79a70671b18ebe26358cb592561af33ca1808f00d935cb      0.1s
 => CACHED [runner 1/3] FROM docker.io/library/eclipse-temurin:21-jre-alpine@sha256:08eecc477dbe3f2e33daac27f36e41daf7f4ec51d2f3396006e54fa  0.1s
 => => resolve docker.io/library/eclipse-temurin:21-jre-alpine@sha256:08eecc477dbe3f2e33daac27f36e41daf7f4ec51d2f3396006e54fa41832c74c       0.1s
 => [internal] load build context                                                                                                            0.0s
 => => transferring context: 1.91kB                                                                                                          0.0s
 => [runner 2/3] RUN addgroup -S spring && adduser -S spring -G spring                                                                       0.6s
 => CACHED [builder 2/6] WORKDIR /app                                                                                                        0.0s
 => CACHED [builder 3/6] COPY pom.xml .                                                                                                      0.0s 
 => [builder 5/6] COPY src ./src                                                                                                             0.1s 
 => [runner 3/3] COPY --from=builder ./app/target/app_java-0.0.1-SNAPSHOT.jar ./app.jar                                                      0.1s 
 => exporting to image                                                                                                                       2.2s 
 => => exporting layers                                                                                                                      1.8s 
 => => exporting manifest sha256:3fb0ff01cf2c83ac6c47e430883faa8d522b8e55a9b05193be5ba00420a74dc2                                            0.0s 
 => => exporting config sha256:228d607e5908bf848b71dcbd8cbc0125a96288a9b2d4d0f12e4f592e11e20c0d                                              0.0s 
 => => exporting attestation manifest sha256:e3202aee20a5900a329f8fb1729f2b448991ae695df757ac1833fbc5d0936b06                                0.0s 
 => => exporting manifest list sha256:9c6df41a190b49b5c43c43dd446dc8a9b77b43faa368a04c3ebcc95b1bc829fe                                       0.0s 
 => => naming to docker.io/library/javaapp:1.0.0                                                                                             0.0s 
 => => unpacking to docker.io/library/javaapp:1.0.0                                                                                      0.2s 
```

docker images
```bash
javaapp-builder:1.0.0                         eded1826a506       1.04GB          351MB
javaapp:1.0.0                                 9c6df41a190b        323MB         92.3MB
```

## Technical Explanation of Each Stage
Builder Stage:
```dockerfile
FROM maven:3.9.6-eclipse-temurin-21 AS builder
```
Full build tooling

JDK for compilation

Maven for dependency management

Runtime Stage:
```dockerfile
FROM eclipse-temurin:21-jre-alpine
```
Minimal Linux image (Alpine)

Only JRE for execution

Minimal system dependencies

Security Benefits
Fewer vulnerabilities: Only necessary packages

No compiler: Attacker cannot compile code

Non-root user: Limited privileges


## Trade-offs and Decisions
Trade-off: Production debugging
Solution: Separate debug images with full tooling
