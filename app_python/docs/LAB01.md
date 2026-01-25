# Framework selection

**chosen framework:** Flask

comparison table:

| Framework | information                                                 |
|-----------|-------------------------------------------------------------|
| flask     | lightweight, easy to use                                    |
| FastAPI   | async-first, auto-docs, better for hight perfomance API's   |
| Django    | heavy-weight, includes ORM and admin, overkill for this lab |

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

![Basic Endpoint Test json](screenshots/base_request_json_output.png)
![Basic Endpoint Test text](screenshots/terminal_output_base_request.png)

Health endpoint test:
![Health Endpoint Test json](screenshots/health_request_json_output.png)
![Health Endpoint Test text](screenshots/health_request_terminal_output.png)

# Challenges and solutions
 No challenges faced during the lab