# Moscow Time Web Application

## Overview

Flask-based web application that displays current Moscow time (MSK) with automatic updates. Features both web interface
and REST API.

## Features

- Real-time MSK time display
- Auto-refresh every second
- REST API endpoint
- Minimalist UI
- Timezone-aware calculations

## Installation

1. **Clone repository**:
   ```bash
   git clone https://github.com/EzzySoft/S25-core-course-labs.git
   cd web-lab1/app_python
   ```

2. **Install dependencies:**:
   ```bash
   python3 -m venv venv
   source ./venv/bin/activate
   pip3 install -r requirements.txt
   ```

3. **Run application:**:
   ```bash
    python3 app.py
   ```

4. **Access in browser:**
    ```
   http://localhost:5000
   ```

## API Documentation

### Get Current Time

```http request
GET /api/time/
```
### Response:

```json
{
  "time":"19:41:37"
}
```

## Docker Build & Run Commands
```bash
# Build
docker build moscow-time .

# Pull
docker pull yourusername/moscow-time:1.0

# Run
docker run -p 5000:5000 ezzysoft/moscow-time:1.0
```

## Unit Tests
Unit tests are used in the project to check correctness of functions and template display.

To run the tests, execute the command in `project root directory`:

```bash
pytest .\app_python\ -v
```