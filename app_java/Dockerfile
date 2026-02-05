# Stage 1: Build
FROM maven:3.9.6-eclipse-temurin-21 AS builder

WORKDIR /app

# Copy the Maven project file
COPY pom.xml .

# Download dependencies
RUN mvn dependency:go-offline

# Copy the rest of the source code
COPY src ./src

# Build the application
RUN mvn package -DskipTests

# Stage 2: Runtime
FROM eclipse-temurin:21-jre-jammy

# Create a non-root user
RUN useradd --create-home appuser

# Copy the JAR file from the builder stage
COPY --from=builder /app/target/*.jar /app/app.jar

# Set ownership and switch to the non-root user
RUN chown appuser:appuser /app/app.jar
USER appuser

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD ["java", "-jar", "/app/app.jar"]
