# LAB01 — DevOps Info Service

## Framework Selection

For this laboratory work, the **Flask** web framework was selected to implement the DevOps Info Service.

### Framework Comparison

| Framework | Pros                                       | Cons                            |
| --------- | ------------------------------------------ | ------------------------------- |
| Flask     | Lightweight, easy to learn, minimal setup  | No built-in async support       |
| FastAPI   | Modern, async support, auto-generated docs | Slightly steeper learning curve |
| Django    | Full-featured, batteries included          | Too heavy for this lab          |

### Justification

I chose Flask because of its simplicity and lightweight nature. Since the primary goal of this service is to provide system information without complex database interactions or asynchronous processing, Flask provides the most straightforward implementation with minimal overhead. It is perfect for a DevOps utility service.

## Best Practices Applied

### Clean Code Organization

The application code is organized into logical sections:

* Configuration
* Logging setup
* Helper functions
* Route definitions
* Error handling

Functions have clear responsibilities and meaningful names. The code follows PEP 8 style guidelines.

### Environment-based Configuration

Application configuration such as host, port, and debug mode is controlled via environment variables. This approach allows the same codebase to be used in different environments without modification.

### Logging

The standard Python `logging` module is used to log application startup and incoming HTTP requests. Logging helps with debugging and monitoring application behavior.

### Error Handling

Custom handlers for HTTP 404 and 500 errors return structured JSON responses. This ensures consistent API behavior and improves client-side error handling.

## API Documentation & Testing

### Endpoints

* `GET /`: Returns detailed system and service metadata.

* `GET /health`: Returns service health status and uptime.

### Testing Commands

To verify the service manually, use curl:
```bash
curl -i [http://127.0.0.1:8080/](http://127.0.0.1:8080/)
curl -i [http://127.0.0.1:8080/health](http://127.0.0.1:8080/health)
```

## Testing Evidence

The application was tested locally on a Windows system using:

* Web browser
* curl command-line tool

Screenshots demonstrating successful responses from both endpoints and formatted JSON output are included in the `screenshots` directory.

## Challenges & Solutions

**No Significant Challenges**: The development process was straightforward due to the clear requirements and the minimalist nature of the Flask framework. The environment was pre-configured correctly, and the implementation followed standard Python web development patterns.

## GitHub Community

Starring repositories helps support open-source projects and increases their visibility within the developer community. Following developers and classmates on GitHub enables better collaboration, knowledge sharing, and professional growth.
