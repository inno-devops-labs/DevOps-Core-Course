# --- STAGE 1: Build (Builder) ---
# Use an image with build tools for compilation
FROM golang:1.23-alpine AS builder

# Set the working directory
WORKDIR /build

# Copy dependency files (if any)
COPY go.mod ./
# If you don't have a go.sum file, this command might fail.
# In that case, comment it out or run 'go mod tidy' locally first.
# RUN go mod download

# Copy the entire source code
COPY . .

# Compile the application.
# CGO_ENABLED=0 is required for a static build (so it can run in minimal images)
RUN CGO_ENABLED=0 GOOS=linux go build -o /app-service main.go


# --- STAGE 2: Final Image (Runtime) ---
# Use minimal Alpine Linux (~5MB)
FROM alpine:3.20

# Create a non-privileged user for security (avoid running as root)
RUN adduser -D appuser
USER appuser

WORKDIR /app

# Copy ONLY the compiled binary from the builder stage
COPY --from=builder /app-service .

# Expose the application port
EXPOSE 8080

# Run the binary
CMD ["./app-service"]