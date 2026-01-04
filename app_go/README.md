# Wordle Game - Go Web Application

## Overview

Interactive Wordle game built with Go's standard library. Players have 6 attempts to guess a randomly selected 5-letter word. Features modern Bootstrap UI with CSS animations and thread-safe session management.

## Features

- Full Wordle game implementation with proper algorithm
- Bootstrap 5 UI with smooth animations
- Color-coded feedback (green, yellow, gray)
- Unique word per game session
- Thread-safe concurrent access
- Health check endpoint

## Technology Stack

- **Language**: Go 1.21
- **Web Server**: net/http (standard library)
- **Templating**: html/template
- **Frontend**: Bootstrap 5
- **Session Management**: UUID

## Quick Start

### Using Docker Compose (Recommended)

```bash
docker compose up
```

Access at: <http://localhost:8080>

### Local Development

```bash
cd app_go
go mod download
go run .
```

### Docker Only

```bash
docker build -t wordle-game .
docker run -p 8080:8080 wordle-game
```

## How to Play

1. Visit <http://localhost:8080> to start a new game
2. Enter a 5-letter word
3. Submit and observe feedback:
   - 🟩 **Green**: Correct position
   - 🟨 **Yellow**: Wrong position
   - ⬜ **Gray**: Not in word
4. You have 6 attempts to guess the word
5. Start a new game after winning/losing

## API Endpoints

- **GET /** - Redirects to new game session
- **GET /game/{game_id}** - Game page for specific session
- **POST /guess** - Submit guess (params: `game_id`, `guess`)
- **GET /health** - Health check endpoint

```json
{
  "status": "healthy",
  "service": "wordle-game"
}
```

## Architecture

- **Session Management**: UUID-based, in-memory storage
- **Concurrency**: `sync.RWMutex` for thread-safe operations
- **Game Logic**: Proper Wordle algorithm with letter frequency handling
- **Word List**: 25 curated 5-letter words

## Testing

1. Visit <http://localhost:8080>
2. Play through a complete game
3. Verify color-coded feedback works correctly
4. Check health: `curl http://localhost:8080/health`
5. Test concurrent sessions (multiple browser tabs)
