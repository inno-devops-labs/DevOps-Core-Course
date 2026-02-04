FROM maven:3.9.6-eclipse-temurin-21 AS builder

WORKDIR /app

COPY pom.xml .

RUN mvn dependency:go-offline -B

COPY src ./src

RUN mvn clean package

FROM eclipse-temurin:21-jre-alpine AS runner

RUN addgroup -S spring && adduser -S spring -G spring

COPY --from=builder ./app/target/app_java-0.0.1-SNAPSHOT.jar ./app.jar

USER spring:spring

EXPOSE 5000

CMD [ "java", "-jar", "./app.jar" ]
