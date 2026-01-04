# Go Web Application - Wordle Game

## Framework Choice: Standard Library (net/http)

### Justification

I chose to use Go's **standard library** (`net/http` and `html/template`) for this web application for the following reasons:

1. **No External Dependencies**: The standard library is powerful enough to build a complete web application without external frameworks.
2. **Performance**: Go's built-in HTTP server is extremely fast and efficient.
3. **Simplicity**: Direct control over routing and request handling without framework overhead.
4. **Production Ready**: Go's standard library is battle-tested and used by major companies.
5. **Easy Deployment**: Compiled binaries are self-contained and easy to deploy.
6. **Type Safety**: Go's strong typing prevents many runtime errors.

## Best Practices Applied

### 1. Code Organization

- **Package Structure**: Clean package organization with separate concerns.
- **Type Safety**: Strong typing for game state and data structures.
- **Separation of Concerns**: Game logic separated from HTTP handlers.
- **Template Management**: HTML templates in dedicated directory.

### 2. Coding Standards

- **Go Conventions**: Follows standard Go naming conventions and idioms.
- **Exported vs Unexported**: Proper use of capitalization for visibility.
- **Error Handling**: Explicit error handling throughout the code.
- **Code Comments**: Clear comments explaining complex logic.
- **Formatting**: Code formatted with `gofmt`.

### 3. Concurrency Safety

- **Mutex Protection**: Game store uses `sync.RWMutex` for thread-safe operations.
- **Read/Write Locks**: Appropriate use of read and write locks for performance.
- **Safe Concurrent Access**: Multiple players can play simultaneously without conflicts.

### 4. Game Logic

- **Wordle Algorithm**: Proper implementation of Wordle rules:
  - Correct position (green)
  - Wrong position (yellow)
  - Not in word (gray)
- **Letter Frequency**: Correct handling of duplicate letters.
- **Session Management**: Each game has a unique ID using UUID.

### 5. Security

- **Input Validation**: All user inputs are validated (5-letter words only).
- **Method Checking**: HTTP methods are validated (GET/POST).
- **No Sensitive Data**: No secrets or sensitive information in code.
- **XSS Prevention**: Template engine automatically escapes HTML.

### 6. Performance

- **Compiled Binary**: Go compiles to native binary for maximum performance.
- **Efficient Memory**: Minimal memory footprint.
- **Fast Startup**: Application starts in milliseconds.
- **Concurrent Request Handling**: Built-in goroutines handle multiple requests efficiently.

### 7. Containerization

- **Multi-stage Build**: Dockerfile uses multi-stage build for minimal image size.
- **Alpine Base**: Final image based on Alpine Linux (~10MB).
- **Static Binary**: CGO disabled for portable binary.
- **Health Checks**: Docker health check included for orchestration.

### 8. User Experience

- **Modern UI**: Bootstrap 5 for responsive design.
- **Animations**: CSS animations for better user feedback:
  - Fade-in effects
  - Flip animations for letter reveals
  - Slide-in animations for new rows
- **Visual Feedback**: Color-coded tiles (green, yellow, gray).
- **Responsive Design**: Works on mobile and desktop.

### 9. Testing Approach

The application is designed to be testable:

- **Unit Tests**: Game logic can be tested independently.
- **Handler Tests**: HTTP handlers can be tested with httptest package.
- **Manual Testing**: Play the game to verify functionality.
- **Health Endpoint**: `/health` endpoint for monitoring.

### 10. Documentation

- **Inline Comments**: Code includes explanatory comments.
- **README**: Comprehensive setup and usage instructions.
- **Type Documentation**: Struct fields are well-documented.

## Wordle Game Implementation

### Game Rules

1. Players have 6 attempts to guess a 5-letter word.
2. After each guess, tiles change color:
   - 🟩 **Green**: Letter is in the correct position
   - 🟨 **Yellow**: Letter is in the word but wrong position
   - ⬜ **Gray**: Letter is not in the word
3. Each game session has a unique randomly selected word.

### Technical Details

- **Word List**: Curated list of common 5-letter words.
- **Session Management**: UUID-based session tracking.
- **State Management**: In-memory game state with thread-safe access.
- **Template Rendering**: Server-side rendering with Go templates.

## Development Workflow

1. **Module Management**: Go modules for dependency management.
2. **Code Quality**: Follow Go best practices and conventions.
3. **Version Control**: `.gitignore` prevents committing binaries and temporary files.
4. **Containerization**: Docker ensures consistent deployment.

## Go-Specific Features

- **Goroutines**: Implicit concurrent request handling.
- **Interfaces**: Clean abstraction for extensibility.
- **Struct Embedding**: Efficient data structures.
- **Template Functions**: Custom functions for template logic.
