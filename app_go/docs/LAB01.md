# Choosen language: Go

# Best practices followed
- Use virtual environment for dependency management
- Clear function and variable names
- Logging for monitoring and debugging
- Error handling for robustness
- Modular code structure for maintainability

# API documentation 

- endpoints:
  - `GET /` - Returns system metadata including hostname, IP address, and current timestamp.
  - `GET /health` - Returns the health status of the service.

## Testing commands in basic configuration 

    curl http://localhost:5000/
    curl http://localhost:5000/health

# Testing evidence

Basic endpoint test:

![Basic Endpoint Test json](screenshots/base_request_json.png)
![Basic Endpoint Test text](screenshots/base_request_terminal.png)

Health endpoint test:

![Health Endpoint Test json](screenshots/health_request_json.png)
![Health Endpoint Test text](screenshots/health_request_terminal.png)

# Challenges and solutions
 No challenges faced during the lab