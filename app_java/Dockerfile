FROM gradle:8.13-jdk21 AS builder

WORKDIR /home/gradle/project

COPY build.gradle.kts settings.gradle.kts gradle.properties* ./
COPY gradle ./gradle
COPY gradlew ./

RUN ./gradlew --no-daemon dependencies || true

COPY src ./src

RUN ./gradlew --no-daemon clean bootJar

FROM gcr.io/distroless/java21-debian12:nonroot

WORKDIR /app

COPY --from=builder /home/gradle/project/build/libs/*.jar /app/app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "/app/app.jar"]
