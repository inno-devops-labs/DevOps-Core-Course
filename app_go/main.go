package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"runtime"
	"time"
)

// JSONLog represents a structured log entry
type JSONLog struct {
	Timestamp string `json:"timestamp"`
	Level     string `json:"level"`
	Logger    string `json:"logger"`
	Message   string `json:"message"`
	Method    string `json:"method,omitempty"`
	Path      string `json:"path,omitempty"`
	Status    int    `json:"status,omitempty"`
	ClientIP  string `json:"client_ip,omitempty"`
	DurationMS float64 `json:"duration_ms,omitempty"`
}

// JSONLogger is a structured JSON logger
type JSONLogger struct {
	name string
}

// NewJSONLogger creates a new JSON logger
func NewJSONLogger(name string) *JSONLogger {
	return &JSONLogger{name: name}
}

// Info logs an info level message
func (l *JSONLogger) Info(msg string) {
	l.log("INFO", msg, nil)
}

// Error logs an error level message
func (l *JSONLogger) Error(msg string) {
	l.log("ERROR", msg, nil)
}

// InfoWithFields logs an info message with additional fields
func (l *JSONLogger) InfoWithFields(msg string, fields map[string]interface{}) {
	l.log("INFO", msg, fields)
}

// log creates and outputs a JSON log entry
func (l *JSONLogger) log(level, msg string, fields map[string]interface{}) {
	logEntry := JSONLog{
		Timestamp: time.Now().UTC().Format(time.RFC3339Nano),
		Level:     level,
		Logger:    l.name,
		Message:   msg,
	}

	if fields != nil {
		if method, ok := fields["method"].(string); ok {
			logEntry.Method = method
		}
		if path, ok := fields["path"].(string); ok {
			logEntry.Path = path
		}
		if status, ok := fields["status"].(int); ok {
			logEntry.Status = status
		}
		if clientIP, ok := fields["client_ip"].(string); ok {
			logEntry.ClientIP = clientIP
		}
		if duration, ok := fields["duration_ms"].(float64); ok {
			logEntry.DurationMS = duration
		}
	}

	jsonBytes, _ := json.Marshal(logEntry)
	log.Println(string(jsonBytes))
}

var logger = NewJSONLogger("devops-info-service")

// Service metadata
type Service struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Framework   string `json:"framework"`
}

// System information
type System struct {
	Hostname        string `json:"hostname"`
	Platform        string `json:"platform"`
	PlatformVersion string `json:"platform_version"`
	Architecture    string `json:"architecture"`
	CPUCount        int    `json:"cpu_count"`
	GoVersion       string `json:"go_version"`
}

// Runtime information
type Runtime struct {
	UptimeSeconds int    `json:"uptime_seconds"`
	UptimeHuman   string `json:"uptime_human"`
	CurrentTime   string `json:"current_time"`
	Timezone      string `json:"timezone"`
}

// Request information
type Request struct {
	ClientIP  string `json:"client_ip"`
	UserAgent string `json:"user_agent"`
	Method    string `json:"method"`
	Path      string `json:"path"`
}

// Endpoint metadata
type Endpoint struct {
	Path        string `json:"path"`
	Method      string `json:"method"`
	Description string `json:"description"`
}

// Complete service response
type ServiceInfo struct {
	Service   Service    `json:"service"`
	System    System     `json:"system"`
	Runtime   Runtime    `json:"runtime"`
	Request   Request    `json:"request"`
	Endpoints []Endpoint `json:"endpoints"`
}

// Health response
type HealthResponse struct {
	Status        string `json:"status"`
	Timestamp     string `json:"timestamp"`
	UptimeSeconds int    `json:"uptime_seconds"`
}

// Error response
type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message"`
}

var startTime = time.Now()

// getUptime calculates application uptime
func getUptime() Runtime {
	delta := time.Since(startTime)
	seconds := int(delta.Seconds())
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60
	secs := seconds % 60

	var human string
	if hours > 0 {
		human = fmt.Sprintf("%d hour%s, %d minute%s", hours, plural(hours), minutes, plural(minutes))
	} else if minutes > 0 {
		human = fmt.Sprintf("%d minute%s, %d second%s", minutes, plural(minutes), secs, plural(secs))
	} else {
		human = fmt.Sprintf("%d second%s", secs, plural(secs))
	}

	return Runtime{
		UptimeSeconds: seconds,
		UptimeHuman:   human,
		CurrentTime:   time.Now().UTC().Format(time.RFC3339),
		Timezone:      "UTC",
	}
}

// plural returns 's' if n != 1, empty string otherwise
func plural(n int) string {
	if n != 1 {
		return "s"
	}
	return ""
}

// getSystemInfo collects system information
func getSystemInfo() System {
	hostname, _ := os.Hostname()
	return System{
		Hostname:        hostname,
		Platform:        runtime.GOOS,
		PlatformVersion: "unknown", // Platform version varies by OS
		Architecture:    runtime.GOARCH,
		CPUCount:        runtime.NumCPU(),
		GoVersion:       runtime.Version(),
	}
}

// getRequestInfo collects request information
func getRequestInfo(r *http.Request) Request {
	// Get client IP, handle X-Forwarded-For for proxies
	clientIP := r.RemoteAddr
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		clientIP = xff
	}

	// Remove port if present
	if host, _, err := net.SplitHostPort(clientIP); err == nil {
		clientIP = host
	}

	return Request{
		ClientIP:  clientIP,
		UserAgent: r.Header.Get("User-Agent"),
		Method:    r.Method,
		Path:      r.URL.Path,
	}
}

// mainHandler handles the main endpoint
func mainHandler(w http.ResponseWriter, r *http.Request) {
	startTime := time.Now()
	uptime := getUptime()
	info := ServiceInfo{
		Service: Service{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service",
			Framework:   "Go net/http",
		},
		System:  getSystemInfo(),
		Runtime: uptime,
		Request: getRequestInfo(r),
		Endpoints: []Endpoint{
			{Path: "/", Method: "GET", Description: "Service information"},
			{Path: "/health", Method: "GET", Description: "Health check"},
		},
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(info); err != nil {
		logger.Error(fmt.Sprintf("Error encoding response: %v", err))
	}

	// Log the request with structured fields
	duration := time.Since(startTime).Seconds() * 1000
	logger.InfoWithFields(fmt.Sprintf("Serving info request from %s", r.RemoteAddr), map[string]interface{}{
		"method":     r.Method,
		"path":       r.URL.Path,
		"status":     200,
		"client_ip":  r.RemoteAddr,
		"duration_ms": duration,
	})
}

// healthHandler handles health check endpoint
func healthHandler(w http.ResponseWriter, r *http.Request) {
	uptime := getUptime()
	response := HealthResponse{
		Status:        "healthy",
		Timestamp:     time.Now().UTC().Format(time.RFC3339),
		UptimeSeconds: uptime.UptimeSeconds,
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(response); err != nil {
		logger.Error(fmt.Sprintf("Error encoding response: %v", err))
	}
}

// errorHandler handles 404 errors
func errorHandler(w http.ResponseWriter, r *http.Request) {
	startTime := time.Now()
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotFound)
	if err := json.NewEncoder(w).Encode(ErrorResponse{
		Error:   "Not Found",
		Message: "Endpoint does not exist",
	}); err != nil {
		logger.Error(fmt.Sprintf("Error encoding response: %v", err))
		return
	}

	// Log the 404 request with structured fields
	duration := time.Since(startTime).Seconds() * 1000
	logger.InfoWithFields("Endpoint not found", map[string]interface{}{
		"method":      r.Method,
		"path":        r.URL.Path,
		"status":      404,
		"client_ip":   r.RemoteAddr,
		"duration_ms": duration,
	})
}

func main() {
	// Configuration from environment variables
	host := getEnv("HOST", "0.0.0.0")
	port := getEnv("PORT", "8080")
	addr := net.JoinHostPort(host, port)

	// Set up handlers
	http.HandleFunc("/", mainHandler)
	http.HandleFunc("/health", healthHandler)

	// Log startup with structured messages
	logger.Info(fmt.Sprintf("Starting DevOps Info Service on %s", addr))
	logger.Info(fmt.Sprintf("Go version: %s", runtime.Version()))
	logger.Info(fmt.Sprintf("Platform: %s/%s", runtime.GOOS, runtime.GOARCH))
	logger.Info(fmt.Sprintf("CPU count: %d", runtime.NumCPU()))

	// Start server
	if err := http.ListenAndServe(addr, nil); err != nil {
		logger.Error(fmt.Sprintf("Server failed to start: %v", err))
		log.Fatalf("Server failed to start: %v", err)
	}
}

// getEnv gets environment variable with fallback
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
