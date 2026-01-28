package server

import (
	"encoding/json"
	"log"
	"net/http"
	"time"

	"devops-info-service-go/internal/info"
)

// New creates an HTTP handler with registered routes and middleware.
func New(logger *log.Logger) http.Handler {
	mux := http.NewServeMux()

	mux.Handle("/", info.MainHandler(logger))
	logger.Println("Registered route: GET /")

	mux.Handle("/health", info.HealthHandler(logger))
	logger.Println("Registered route: GET /health")

	// Wrap with middleware: recovery then logging.
	var handler http.Handler = mux
	handler = recoveryMiddleware(logger, handler)
	handler = loggingMiddleware(logger, handler)

	return handler
}

// loggingMiddleware logs basic request information and latency.
func loggingMiddleware(logger *log.Logger, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		ww := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}

		logger.Printf("Incoming request: %s %s from %s", r.Method, r.URL.Path, r.RemoteAddr)

		next.ServeHTTP(ww, r)

		duration := time.Since(start)
		logger.Printf("%s %s %d %s", r.Method, r.URL.Path, ww.statusCode, duration)
	})
}

// recoveryMiddleware recovers from panics and returns a JSON 500 error.
func recoveryMiddleware(logger *log.Logger, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if rec := recover(); rec != nil {
				logger.Printf("panic recovered: %v", rec)

				w.Header().Set("Content-Type", "application/json")
				w.WriteHeader(http.StatusInternalServerError)

				_ = json.NewEncoder(w).Encode(map[string]string{
					"error":   "Internal Server Error",
					"message": "Unexpected server error",
				})
			}
		}()

		next.ServeHTTP(w, r)
	})
}

// responseWriter wraps http.ResponseWriter to capture status codes.
type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (w *responseWriter) WriteHeader(statusCode int) {
	w.statusCode = statusCode
	w.ResponseWriter.WriteHeader(statusCode)
}
