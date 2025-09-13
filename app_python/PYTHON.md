# Python Web Application Description

## Framework Choice: Flask

**Justification:**

- **Lightweight & Minimalistic**: Ideal for small applications like a time display service
- **Template Support**: Built-in Jinja2 templating engine for HTML rendering
- **API Support**: Native JSON response handling via `jsonify`

## Best Practices Implementation

### 1. Code Organization

- Separation of concerns (routes, business logic, templates)
- Configuration constants (`START_HOST`, `START_PORT`) at module level
- Dedicated time calculation function (`get_current_time`)

### 2. Coding Standards

- PEP8 compliance
- Type hints for function signatures
- Descriptive variable names
- 79-character line length limit

### 3. Testing Strategy

1. **Manual Testing**:
    - Timezone validation (MSK vs UTC)
    - Auto-refresh functionality check
    - Cross-browser compatibility

2. **Automated Checks**:
   ```bash
   flake8 app.py
   mypy app.py
   black --check app.py
   ```

### 4. Architecture

```
app_python/
├── .gitignore
├── app.py
├── templates/
├── static/
├── requirements.txt
├── tests/
├── PYTHON.md
└── README.md
```

### 5. Unit Tests for the Project

#### Test Descriptions

- `test_get_current_time_format`

  Verifies that the get_current_time function returns time in the "HH:MM:SS" format.


- `test_show_time_route`

  Uses a Flask test client to access the main page ("/"). This test checks:

    - A 200 response status.
    - The presence of the "MOSCOW TIME" header.
    - The existence of a container with id time-container and a `<p id="time">` element.
- `test_api_time_route`

    Tests the API endpoint `/api/time/`, ensuring that the JSON response contains the key `time` and that its value matches the expected current time.


#### Best Practices Applied
- Independence of tests.
- Use of `pytest` fixtures to create the test client.
- Validation of the correct time format using datetime.strptime.
- Precise testing of key HTML elements.